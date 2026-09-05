"""TASK-011H-A tests: local multilingual embedder, OpenSearch client wiring,
semantic admission gate, latency harness, LLM citation parsing, security audit."""

from __future__ import annotations

import pytest

from msb_knowledge_rag.answerer import MaasRagAnswerer
from msb_knowledge_rag.config import KnowledgeRagConfig
from msb_knowledge_rag.embedding import (
    EmbeddingUnavailable,
    IdfLocalEmbedder,
    LocalMultilingualEmbedder,
    build_embedder,
)
from msb_knowledge_rag.evaluation import (
    GOLDEN_QUESTIONS,
    OUT_OF_SCOPE_QUESTIONS,
    _cited_expected,
    evaluate_question,
    llm_citation_indices,
    secret_audit,
)
from msb_knowledge_rag.latency import latency_report
from msb_knowledge_rag.models import RagAnswer
from msb_knowledge_rag.service import KnowledgeRagService
from msb_knowledge_rag.vdb_client import (
    GreennodeVdbOpenSearchClient,
    InProcessMockVectorStore,
    VdbUnavailable,
    build_store,
)

SEMANTIC = "local-multilingual"
FASTEMBED = LocalMultilingualEmbedder.available()


def _semantic_config() -> KnowledgeRagConfig:
    config = KnowledgeRagConfig()
    config.embedding_provider = SEMANTIC
    config.semantic_min_score = 0.38
    return config


@pytest.fixture(scope="module")
def semantic_service():
    if not FASTEMBED:
        pytest.skip("fastembed / multilingual model not available")
    service = KnowledgeRagService(config=_semantic_config())
    service.index_all()
    return service


# --- embedding factory ---


def test_build_embedder_default_is_deterministic():
    embedder = build_embedder(KnowledgeRagConfig())
    assert isinstance(embedder, IdfLocalEmbedder)


def test_build_embedder_local_multilingual():
    embedder = build_embedder(_semantic_config())
    assert isinstance(embedder, LocalMultilingualEmbedder)
    assert embedder.dimension() == 384


def test_build_embedder_greennode_maas_requires_provisioned_model():
    config = KnowledgeRagConfig()
    config.embedding_provider = "greennode-maas"
    with pytest.raises(EmbeddingUnavailable):
        build_embedder(config)


def test_build_embedder_unknown_provider_raises():
    config = KnowledgeRagConfig()
    config.embedding_provider = "nope"
    with pytest.raises(ValueError):
        build_embedder(config)


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_local_multilingual_deterministic_and_same_dimension():
    embedder_1 = LocalMultilingualEmbedder()
    embedder_2 = LocalMultilingualEmbedder()
    texts = ["Quyết định cuối cùng thuộc về ai?", "dòng tiền thu hồi nợ"]
    first = embedder_1.embed(texts)
    second = embedder_2.embed(texts)
    assert len(first) == 2 and len(first[0]) == 384
    assert all(a == pytest.approx(b, abs=1e-6) for a, b in zip(first, second))


# --- VDB wiring ---


def test_build_store_defaults_to_mock():
    store = build_store(KnowledgeRagConfig())
    assert isinstance(store, InProcessMockVectorStore)
    assert store.is_live() is False


def test_build_store_configured_returns_opensearch(monkeypatch):
    monkeypatch.setenv("GRENNODE_VDB_ENDPOINT", "https://vdb.example")
    monkeypatch.setenv("GRENNODE_VDB_INDEX", "msb-knowledge")
    config = KnowledgeRagConfig()
    store = build_store(config)
    assert isinstance(store, GreennodeVdbOpenSearchClient)
    assert store.is_live() is True
    assert store.name == "greennode-vdb-opensearch"


def test_opensearch_unconfigured_raises(monkeypatch):
    monkeypatch.delenv("GRENNODE_VDB_ENDPOINT", raising=False)
    config = KnowledgeRagConfig()
    client = GreennodeVdbOpenSearchClient(config, dimension=384)
    assert client.is_live() is False
    with pytest.raises(VdbUnavailable):
        client.count()
    with pytest.raises(VdbUnavailable):
        client.search([0.0] * 384)
    assert client.upsert([]) == 0


def test_opensearch_client_never_exposes_password_in_errors():
    class _Config:
        grennode_vdb_endpoint = "https://vdb.example"
        grennode_vdb_index = "idx"
        grennode_vdb_user = "master"
        grennode_vdb_password = "topsecret"

    client = GreennodeVdbOpenSearchClient(_Config(), dimension=384)  # type: ignore[arg-type]
    try:
        client.count()
    except VdbUnavailable as error:
        assert "topsecret" not in str(error)


# --- semantic gate (integration) ---


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_semantic_gate_d6_now_answerable(semantic_service):
    question = next(q for q in GOLDEN_QUESTIONS if q.question_id == "D6")
    answer = semantic_service.answer(question.question)
    assert answer.status == "ANSWERED"
    assert answer.classification == "PROJECT_KNOWLEDGE"
    top = [source["document_id"] for source in answer.sources]
    assert any(doc in top for doc in question.expected_documents)
    assert answer.meta["confidence_features"]["tier"] == "semantic"
    assert answer.meta["confidence_features"]["top1_cosine"] >= 0.38


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_semantic_gate_out_of_scope_refused(semantic_service):
    for question in OUT_OF_SCOPE_QUESTIONS:
        answer = semantic_service.answer(question)
        assert answer.status == "LOW_CONFIDENCE"
        assert "chưa tìm thấy đủ thông tin" in answer.answer
        assert answer.meta["confidence_features"]["tier"] == "semantic"


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_semantic_gate_boundaries_and_security_preserved(semantic_service):
    boundary_qs = [q for q in GOLDEN_QUESTIONS if q.group in ("BOUNDARY", "SECURITY")]
    for question in boundary_qs:
        answer = semantic_service.answer(question.question)
        assert answer.classification == question.expected_boundary, question.question_id
        assert answer.status == "BOUNDARY"


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_semantic_full_33_eval_no_regressions_on_boundaries(semantic_service):
    rows = [evaluate_question(semantic_service, question) for question in GOLDEN_QUESTIONS]
    knowledge = [row for row in rows if row.group in ("A", "B", "C", "D")]
    boundary = [row for row in rows if row.group in ("BOUNDARY", "SECURITY")]
    assert all(row.boundary_ok for row in boundary)
    assert any(row.recall_3 for row in knowledge if row.question_id == "D6")


# --- latency harness ---


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_latency_report_phase_shape(semantic_service):
    questions = [
        question.question
        for question in GOLDEN_QUESTIONS
        if question.group in ("A", "B", "C", "D")
    ][:6]
    report = latency_report(semantic_service, questions)
    assert report["samples"] == 6
    for phase in ("classification_ms", "embedding_ms", "retrieval_ms", "model_ms", "total_ms"):
        stats = report["phases"][phase]
        assert stats["count"] == 6
        assert stats["min"] <= stats["median"] <= stats["max"]


@pytest.mark.skipif(not FASTEMBED, reason="fastembed not installed")
def test_latency_meta_fields_present_on_answers(semantic_service):
    answer = semantic_service.answer("Phiên bản kiến thức hiện tại của hệ thống là gì?")
    for field in ("classification_ms", "embedding_ms", "retrieval_ms", "total_ms"):
        assert field in answer.meta


# --- LLM citation parsing ---


def test_llm_citation_indices_only_valid_range():
    answer = RagAnswer(
        status="ANSWERED",
        path="rag_qwen",
        knowledge_type="PROJECT_KNOWLEDGE",
        answer="Theo [2] và [4] và [99] và xyz[0].",
        classification="PROJECT_KNOWLEDGE",
        sources=[{"document_id": "a"}, {"document_id": "b"}, {"document_id": "c"}, {"document_id": "d"}, {"document_id": "e"}],
    )
    assert llm_citation_indices(answer) == [2, 4]


def test_cited_expected_via_llm_reference():
    answer = RagAnswer(
        status="ANSWERED",
        path="rag_qwen",
        knowledge_type="PROJECT_KNOWLEDGE",
        answer="Câu trả lời trích từ [2].",
        classification="PROJECT_KNOWLEDGE",
        sources=[{"document_id": "x"}, {"document_id": "20-trust-and-safety"}],
    )
    assert _cited_expected(answer, ["20-trust-and-safety"], ["20-trust-and-safety"]) is True


def test_cited_expected_false_when_ref_maps_outside_expected():
    answer = RagAnswer(
        status="ANSWERED",
        path="rag_qwen",
        knowledge_type="PROJECT_KNOWLEDGE",
        answer="Đoạn [1].",
        classification="PROJECT_KNOWLEDGE",
        sources=[{"document_id": "irrelevant"}, {"document_id": "20-trust-and-safety"}],
    )
    assert _cited_expected(answer, ["20-trust-and-safety"], ["20-trust-and-safety"]) is False


# --- security ---


def test_secret_audit_passes(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-live-do-not-leak-0123456789")
    monkeypatch.setenv("GREENNODE_VDB_PASSWORD", "vdb-secret-pw-0987654321")
    service = KnowledgeRagService(config=KnowledgeRagConfig())
    service.index_all()
    report = secret_audit(service)
    assert report["SECRET_AUDIT"] == "PASS"
    assert report["SECRET_QUERY_SAFE"] == "PASS"
    assert report["PRIVATE_REASONING_AUDIT"] == "PASS"


class _StubMaaSClient:
    model = "qwen/qwen3.6-flash"

    def __init__(self, content: str):
        self._content = content
        self.calls = []

    def complete(self, prompt: str, max_tokens: int, temperature: float) -> tuple[str, str]:
        self.calls.append(prompt)
        return self._content, self.model


def test_maas_answerer_uses_only_prompt_content_and_citations():
    client = _StubMaaSClient("Dựa trên [1], quyết định thuộc về Decision Core. [3]")
    answerer = MaasRagAnswerer(config=KnowledgeRagConfig(), client=client)
    from msb_knowledge_rag.models import KnowledgeChunk

    chunks = [
        KnowledgeChunk(
            chunk_id="04-call-cbs-routing::k1",
            document_id="04-call-cbs-routing",
            title="Routing",
            section="s",
            topic="ROUTING",
            audience="ALL",
            knowledge_version="TASK-011H-V1",
            source_commit="c",
            source_type="official",
            implementation_status="IMPLEMENTED",
            heading="h",
            order=1,
            content="Nội dung routing.",
        )
    ]
    text = answerer.answer("Câu hỏi?", chunks)
    assert "[1]" in text and "[3]" in text
    assert len(client.calls) == 1
    assert "04-call-cbs-routing" in client.calls[0]
    assert "reasoning_content" not in text