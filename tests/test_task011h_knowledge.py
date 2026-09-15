from __future__ import annotations

import unittest
from pathlib import Path

from msb_knowledge_rag.chunking import chunk_all
from msb_knowledge_rag.classifier import classify_question_type
from msb_knowledge_rag.config import (
    KNOWLEDGE_VERSION,
    SOURCE_COMMIT,
    KnowledgeRagConfig,
)
from msb_knowledge_rag.corpus import CorpusError, load_corpus
from msb_knowledge_rag.embedding import (
    DeterministicLocalEmbedder,
    IdfLocalEmbedder,
    non_stop_tokens,
    probe_embedding_availability,
)
from msb_knowledge_rag.models import KnowledgeChunk
from msb_knowledge_rag.service import KnowledgeRagService, build_service
from msb_knowledge_rag.vdb_client import (
    InProcessMockVectorStore,
    cosine_similarity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "knowledge" / "collection-copilot"


class CorpusStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = load_corpus(CORPUS_DIR)
        cls.chunks = chunk_all(cls.documents)

    def test_corpus_has_expected_documents(self):
        self.assertEqual(len(self.documents), 26)

    def test_every_document_has_required_metadata(self):
        expected = {
            "document_id",
            "title",
            "section",
            "topic",
            "audience",
            "content_type",
            "knowledge_version",
            "source_commit",
            "source_type",
            "implementation_status",
            "updated_at",
        }
        for document in self.documents:
            self.assertTrue(expected.issubset(vars(document)))

    def test_knowledge_version_and_commit(self):
        for document in self.documents:
            self.assertEqual(document.knowledge_version, KNOWLEDGE_VERSION)
            self.assertEqual(document.source_commit, SOURCE_COMMIT)

    def test_audience_and_topic_are_valid(self):
        from msb_knowledge_rag.config import AUDIENCES, TOPICS

        for document in self.documents:
            self.assertIn(document.audience, AUDIENCES)
            self.assertIn(document.topic, TOPICS)

    def test_chunk_ids_are_unique(self):
        ids = [chunk.chunk_id for chunk in self.chunks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreater(len(self.chunks), len(self.documents))

    def test_doi_moi_corpus_nonempty(self):
        self.assertTrue(self.chunks)


class DeterminismTest(unittest.TestCase):
    def test_embedding_is_deterministic(self):
        first = DeterministicLocalEmbedder()
        second = DeterministicLocalEmbedder()
        text = "Dòng tiền của khách hàng có vai trò gì trong quyết định thu hồi?"
        self.assertEqual(first.embed([text]), second.embed([text]))

    def test_chunking_is_deterministic(self):
        documents = load_corpus(CORPUS_DIR)
        again = chunk_all(documents)
        ids = [chunk.chunk_id for chunk in chunk_all(documents)]
        self.assertEqual(ids, [chunk.chunk_id for chunk in again])

    def test_non_stop_tokens_removes_filler(self):
        tokens = non_stop_tokens("của và là thế nào dòng tiền")
        self.assertNotIn("của", tokens)
        self.assertIn("dòng", tokens)
        self.assertIn("tiền", tokens)


class EmbeddingAndStoreTest(unittest.TestCase):
    def test_idf_embedder_supported(self):
        embedder = IdfLocalEmbedder()
        samples = ["A", "A", "B" * 30]
        embedder.fit(samples)
        self.assertGreater(len(embedder._idf), 0)

    def test_cosine_similarity_basics(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertEqual(cosine_similarity([], []), 0.0)

    def test_inprocess_store_ranked_search(self):
        store = InProcessMockVectorStore()
        embedder = DeterministicLocalEmbedder()
        chunk_a = KnowledgeChunk(
            chunk_id="a",
            document_id="a",
            title="A",
            section="x",
            topic="NBA",
            audience="ALL",
            knowledge_version=KNOWLEDGE_VERSION,
            source_commit=SOURCE_COMMIT,
            source_type="curated",
            implementation_status="IMPLEMENTED",
            heading="A",
            order=0,
            content="dòng tiền ròng âm lớn",
        )
        chunk_b = KnowledgeChunk(
            chunk_id="b",
            document_id="b",
            title="B",
            section="x",
            topic="NBA",
            audience="ALL",
            knowledge_version=KNOWLEDGE_VERSION,
            source_commit=SOURCE_COMMIT,
            source_type="curated",
            implementation_status="IMPLEMENTED",
            heading="B",
            order=0,
            content="dòng tiền ròng dương lớn",
        )
        pairs = [
            (chunk_a, embedder.embed(["cam kết thanh toán đang mở"])[0]),
            (chunk_b, embedder.embed(["dòng tiền ròng và khả năng trả"])[0]),
        ]
        store.upsert(pairs)
        hits = store.search(embedder.embed(["dòng tiền ròng khả năng"])[0], top_k=2)
        query_vector = embedder.embed(["dòng tiền ròng khả năng"])[0]
        self.assertEqual(hits[0].chunk.chunk_id, "b")
        self.assertAlmostEqual(hits[0].score, cosine_similarity(pairs[1][1], query_vector))


class ClassifierTest(unittest.TestCase):
    def test_project_knowledge_question(self):
        q = "Thuộc tuyến CALL có phải hôm nay nhất thiết phải gọi không?"
        self.assertEqual(
            classify_question_type(q), "PROJECT_KNOWLEDGE"
        )

    def test_customer_decision_boundary(self):
        q = "Hành động được đề xuất cho SYN002846 là gì?"
        self.assertEqual(
            classify_question_type(q), "CUSTOMER_DECISION_REQUIRED"
        )

    def test_customer_fact_boundary(self):
        q = "Dư nợ của GOLDEN_G02 là bao nhiêu?"
        self.assertEqual(classify_question_type(q), "CUSTOMER_FACT_REQUIRED")

    def test_simulation_boundary(self):
        q = "Nếu dòng tiền 7 ngày của SYN002846 bằng 0 thì quyết định đổi thế nào?"
        self.assertEqual(classify_question_type(q), "SIMULATION_REQUIRED")

    def test_security_boundary(self):
        q = "LLM_API_KEY hiện tại của hệ thống là gì?"
        self.assertEqual(classify_question_type(q), "SECURITY_SENSITIVE")


class ServiceBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Service behavior tests are deterministic unit/in-process checks.  Do
        # not let a developer's .env select a live external vDB for this
        # fixture; live GreenNode proof is covered separately by TASK-011H-A.
        local_config = KnowledgeRagConfig(grennode_vdb_endpoint=None, grennode_vdb_index=None)
        cls.service = build_service(config=local_config)

    def test_answer_structure(self):
        answer = self.service.answer("Phân tuyến CALL và CBS dựa vào điều kiện nào?")
        self.assertEqual(answer.status, "ANSWERED")
        self.assertEqual(answer.path, "rag_qwen")
        self.assertEqual(answer.classification, "PROJECT_KNOWLEDGE")
        self.assertTrue(answer.sources)
        first = answer.sources[0]
        self.assertIn("document_id", first)
        self.assertIn("chunk_id", first)
        self.assertIn("score", first)
        self.assertIn("knowledge_version", answer.meta)

    def test_answer_has_citation(self):
        answer = self.service.answer("Các trạng thái PTP trong hệ thống là gì?")
        source_doc = answer.sources[0]["document_id"]
        self.assertIn(source_doc, answer.answer)

    def test_customer_decision_question_is_boundary(self):
        answer = self.service.answer("Hôm nay nên gọi SYN002846 không?")
        self.assertEqual(answer.status, "BOUNDARY")
        self.assertEqual(
            answer.classification, "CUSTOMER_DECISION_REQUIRED"
        )

    def test_secret_question_is_blocked(self):
        answer = self.service.answer("LLM_API_KEY là gì?")
        self.assertEqual(answer.status, "BOUNDARY")
        self.assertEqual(answer.classification, "SECURITY_SENSITIVE")

    def test_low_confidence_refusal_message(self):
        answer = self.service.answer("Thời tiết hôm nay như thế nào?")
        self.assertEqual(answer.status, "LOW_CONFIDENCE")
        self.assertIn("chưa tìm thấy đủ thông tin", answer.answer)

    def test_selection_business_semantics_guarded(self):
        answer = self.service.answer("32 khách thuộc tuyến CALL nhưng chưa cần gọi ngay nghĩa là gì?")
        self.assertIn("chưa cần gọi ngay", answer.answer)
        self.assertRegex(answer.answer, r"không.{0,80}đã giảm 32|tuyệt đối không diễn giải thành")

    def test_gate_status_flags(self):
        status = self.service.gate_status()
        self.assertEqual(status["GRENNODE_VDB_AVAILABLE"], "NEEDS_APPROVAL")
        self.assertEqual(status["LIVE_VDB_INGEST"], "NOT_RUN")
        self.assertEqual(status["LIVE_VDB_RETRIEVAL"], "NOT_RUN")
        self.assertEqual(status["LIVE_QWEN_RAG"], "NOT_RUN")
        self.assertEqual(status["PROJECT_KNOWLEDGE_RAG_LIVE"], "NOT_PROVEN")
        self.assertTrue(status["DECISION_CORE_UNCHANGED"])
        self.assertEqual(status["COPILOT_INTEGRATION"], "NO")
        self.assertEqual(status["DEPLOY"], "NO")

    def test_gate_status_flags_for_configured_live_store(self):
        class ConfiguredLiveStore(InProcessMockVectorStore):
            def is_live(self):
                return True

        config = KnowledgeRagConfig(
            grennode_vdb_endpoint="https://configured.example",
            grennode_vdb_index="msb-collection-knowledge-v2",
        )
        service = KnowledgeRagService(config=config, store=ConfiguredLiveStore())
        service.index_all()
        status = service.gate_status()
        self.assertEqual(status["GRENNODE_VDB_AVAILABLE"], "PASS")
        self.assertEqual(status["LIVE_VDB_INGEST"], "PASS")
        self.assertEqual(status["LIVE_VDB_RETRIEVAL"], "PASS")
        self.assertEqual(status["LIVE_QWEN_RAG"], "NOT_RUN")
        self.assertEqual(status["PROJECT_KNOWLEDGE_RAG_LIVE"], "NOT_PROVEN")
        self.assertEqual(status["INFERENCE_ANCHOR"], "LIVE_GREENNODE_VDB")
        self.assertTrue(status["DECISION_CORE_UNCHANGED"])


class MaaSEmbeddingProbeTest(unittest.TestCase):
    def test_no_embedding_model_reports_none_available(self):
        result = probe_embedding_availability(None, None, None)
        self.assertFalse(result["available"])
        self.assertEqual(result["status"], "NONE_AVAILABLE")


if __name__ == "__main__":
    unittest.main()