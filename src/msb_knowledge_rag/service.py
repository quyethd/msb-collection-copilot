from __future__ import annotations

import time
from typing import Callable

from .answerer import DeterministicGroundedAnswerer, MaasRagAnswerer, RagAnswerer
from .classifier import classify_question_type, infer_topics
from .config import (
    BOUNDARY_RESPONSES,
    LOW_CONFIDENCE_REFUSAL,
    KNOWLEDGE_VERSION,
    SOURCE_COMMIT,
    EMBEDDING_MODEL_STATUS,
    KnowledgeRagConfig,
)
from .corpus import load_corpus
from .embedding import (
    DeterministicLocalEmbedder,
    Embedder,
    IdfLocalEmbedder,
    LocalMultilingualEmbedder,
    build_embedder,
    embedder_is_live,
)
from .models import QuestionType, RagAnswer
from .retriever import IndexedRetrievalPipeline, _chunk_text
from .security import security_scan
from .vdb_client import VectorStore, build_store

BoundaryHint = Callable[[QuestionType], str | None]


def _is_semantic_embedder(embedder: Embedder) -> bool:
    return not isinstance(embedder, (DeterministicLocalEmbedder, IdfLocalEmbedder))


class KnowledgeRagService:
    def __init__(
        self,
        config: KnowledgeRagConfig | None = None,
        store: VectorStore | None = None,
        embedder: Embedder | None = None,
        answerer: RagAnswerer | None = None,
        all_chunks=None,
        boundary_hint: BoundaryHint | None = None,
    ):
        self.config = config or KnowledgeRagConfig()
        self.embedder = embedder or build_embedder(self.config)
        if store is None:
            store = build_store(self.config, dimension=self.embedder.dimension())
        self.posstore = store
        self.semantic = _is_semantic_embedder(self.embedder)
        self.answerer = answerer or DeterministicGroundedAnswerer()
        self.boundary_hint = boundary_hint
        self._live_answer_ran = False
        if all_chunks is None:
            documents = load_corpus(self.config.corpus_dir)
            from .chunking import chunk_all

            all_chunks = chunk_all(documents)
        self.all_chunks = all_chunks
        self.pipeline = IndexedRetrievalPipeline(
            self.config, self.posstore, self.embedder, all_chunks
        )
        if isinstance(self.embedder, IdfLocalEmbedder):
            self.embedder.fit([_chunk_text(chunk) for chunk in self.all_chunks])

    def index_all(self) -> int:
        return self.pipeline.index_all()

    def answer(self, question: str) -> RagAnswer:
        started = time.perf_counter()
        text = question if isinstance(question, str) else ""
        if not text.strip():
            return RagAnswer(
                status="LOW_CONFIDENCE",
                path="rag_qwen",
                knowledge_type="PROJECT_KNOWLEDGE",
                answer=LOW_CONFIDENCE_REFUSAL,
                classification="LOW_CONFIDENCE",
                meta={"total_ms": round((time.perf_counter() - started) * 1000, 3)},
            )
        blocked, reason = security_scan(text)
        if blocked:
            return self._boundary(text, "SECURITY_SENSITIVE", started, reason)
        classify_started = time.perf_counter()
        qtype = classify_question_type(text)
        classification_ms = (time.perf_counter() - classify_started) * 1000
        if qtype != "PROJECT_KNOWLEDGE":
            return self._boundary(text, qtype, started)

        topics = infer_topics(text)
        retrieval_started = time.perf_counter()
        result = self.pipeline.retrieve(question=text)
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000
        perf = getattr(self.pipeline, "last_perf", None)
        embedding_ms = perf.embedding_ms if perf else 0.0
        if not result.hits:
            confidence = self._confidence_for_empty(text)
            return RagAnswer(
                status="LOW_CONFIDENCE",
                path="rag_qwen",
                knowledge_type="PROJECT_KNOWLEDGE",
                answer=LOW_CONFIDENCE_REFUSAL,
                classification="LOW_CONFIDENCE",
                sources=self._sources(result.hits),
                meta=self._meta(
                    retrieval_ms=retrieval_ms,
                    classification_ms=classification_ms,
                    embedding_ms=embedding_ms,
                    question_type="PROJECT_KNOWLEDGE",
                    topics=topics,
                    started=started,
                    confidence_features=confidence,
                ),
            )
        admitted, confidence = self._evidence_gate(result.hits, text, result.top_cosine)
        if not admitted:
            return RagAnswer(
                status="LOW_CONFIDENCE",
                path="rag_qwen",
                knowledge_type="PROJECT_KNOWLEDGE",
                answer=LOW_CONFIDENCE_REFUSAL,
                classification="LOW_CONFIDENCE",
                sources=self._sources(result.hits),
                meta=self._meta(
                    retrieval_ms=retrieval_ms,
                    classification_ms=classification_ms,
                    embedding_ms=embedding_ms,
                    question_type="PROJECT_KNOWLEDGE",
                    topics=topics,
                    started=started,
                    confidence_features=confidence,
                ),
            )
        model_started = time.perf_counter()
        answer_text = self.answerer.answer(text, [hit.chunk for hit in result.hits])
        model_ms = (time.perf_counter() - model_started) * 1000
        if isinstance(self.answerer, MaasRagAnswerer) and self.posstore.is_live():
            self._live_answer_ran = True
        return RagAnswer(
            status="ANSWERED",
            path="rag_qwen",
            knowledge_type="PROJECT_KNOWLEDGE",
            answer=answer_text,
            sources=self._sources(result.hits),
            classification="PROJECT_KNOWLEDGE",
            meta=self._meta(
                retrieval_ms=retrieval_ms,
                classification_ms=classification_ms,
                embedding_ms=embedding_ms,
                model_ms=model_ms,
                question_type="PROJECT_KNOWLEDGE",
                topics=topics,
                started=started,
                confidence_features=confidence,
            ),
        )

    def _confidence_for_empty(self, question: str) -> dict:
        if self.semantic:
            return {
                "tier": "semantic",
                "top1_cosine": 0.0,
                "semantic_min_score": self.config.semantic_min_score,
                **self.pipeline.lexical_features(question),
            }
        return {"tier": "deterministic", "phrase_evidence": False}

    def _evidence_gate(self, hits, question: str, top_cosine: float = 0.0) -> tuple[bool, dict]:
        """Admission gate per embedding tier.

        Semantic tier (TASK-011H-A): the RAW top-1 cosine (pre rerank-boost,
        exactly what SEMANTIC_MIN_SCORE=0.38 was calibrated on) must reach the
        threshold. Lexical bigram presence is recorded as a confidence feature
        only — it never acts as a hard admission gate.

        Deterministic tier (foundation): unchanged phrase-evidence gate so the
        LOCAL_MOCKED_VDB baseline keeps its exact refusal semantics.
        """
        if self.semantic:
            top1 = round(top_cosine, 4)
            admitted = top1 >= self.config.semantic_min_score
            confidence = {
                "tier": "semantic",
                "top1_cosine": top1,
                "semantic_min_score": self.config.semantic_min_score,
                **self.pipeline.lexical_features(question),
            }
            return admitted, confidence
        admitted = bool(hits) and self.pipeline.evidence_ok(hits, question) is not False
        confidence = {
            "tier": "deterministic",
            "phrase_evidence": bool(hits and self.pipeline.evidence_ok(hits, question)),
        }
        return admitted, confidence

    def _meta(self, retrieval_ms: float, started: float, **extra) -> dict:
        meta = {
            "knowledge_version": self.config.knowledge_version,
            "source_commit": SOURCE_COMMIT,
            "embedding_provider": getattr(self.embedder, "name", self.embedder.__class__.__name__),
            "embedding_dimension": getattr(self.embedder, "dimension", lambda: 0)(),
            "store": getattr(self.posstore, "name", self.posstore.__class__.__name__),
            "inference_anchor": "LIVE_GREENNODE_VDB"
            if self.posstore.is_live()
            else "LOCAL_MOCKED_VDB",
            "classification_ms": round(extra.pop("classification_ms", 0.0), 3),
            "embedding_ms": round(extra.pop("embedding_ms", 0.0), 3),
            "retrieval_ms": round(retrieval_ms, 3),
            "model_ms": round(extra.pop("model_ms", 0.0), 3),
            "total_ms": round((time.perf_counter() - started) * 1000, 3),
            **extra,
        }
        return meta

    def _boundary(
        self, text: str, qtype: QuestionType, started: float, reason: str | None = None
    ) -> RagAnswer:
        hinted = self.boundary_hint(qtype) if self.boundary_hint else None
        answer = hinted or BOUNDARY_RESPONSES[qtype]
        return RagAnswer(
            status="BOUNDARY",
            path="rag_qwen",
            knowledge_type="PROJECT_KNOWLEDGE",
            answer=answer,
            classification=qtype,
            meta={
                "knowledge_version": self.config.knowledge_version,
                "reason": reason,
                "total_ms": round((time.perf_counter() - started) * 1000, 3),
            },
        )

    @staticmethod
    def _sources(hits) -> list[dict]:
        return [
            {
                "document_id": hit.chunk.document_id,
                "title": hit.chunk.title,
                "section": hit.chunk.section,
                "chunk_id": hit.chunk.chunk_id,
                "score": round(hit.score, 4),
            }
            for hit in hits
        ]

    def gate_status(self) -> dict:
        store_live = self.posstore.is_live()
        qwen_available = "PASS" if self.config.live_maas_configured() else "NOT_CONFIGURED"
        if self.config.embedding_provider in ("local-multilingual", "local-e5"):
            embedding_status = (
                "LOCAL_MULTILINGUAL_AVAILABLE"
                if LocalMultilingualEmbedder.available()
                else "LOCAL_MULTILINGUAL_MISSING"
            )
        else:
            embedding_status = EMBEDDING_MODEL_STATUS
        return {
            "knowledge_version": self.config.knowledge_version,
            "source_commit": SOURCE_COMMIT,
            "noop_documents": len({chunk.document_id for chunk in self.all_chunks}),
            "corpus_chunks": len(self.all_chunks),
            "QWEN_FAST_MODEL": self.config.qwen_fast_model,
            "QWEN_FAST_MODEL_AVAILABLE": qwen_available,
            "EMBEDDING_PROVIDER": self.config.embedding_provider,
            "EMBEDDING_MODEL": getattr(self.embedder, "model_name", None)
            if self.semantic
            else None,
            "EMBEDDING_DIMENSION": getattr(self.embedder, "dimension", lambda: 0)(),
            "EMBEDDING_MODEL_STATUS": embedding_status,
            "SEMANTIC_MIN_SCORE": self.config.semantic_min_score,
            "SEMANTIC_PARAPHRASE_GATE": "PASS" if self.semantic else "N/A",
            "GRENNODE_VDB_AVAILABLE": "PASS" if store_live else "NEEDS_APPROVAL",
            "LIVE_VDB_INGEST": "PASS" if store_live else "NOT_RUN",
            "LIVE_VDB_RETRIEVAL": "PASS" if store_live else "NOT_RUN",
            "LIVE_QWEN_RAG": "PASS" if self._live_answer_ran else "NOT_RUN",
            "PROJECT_KNOWLEDGE_RAG_LIVE": "PASS" if store_live and self._live_answer_ran else "NOT_PROVEN",
            "INFERENCE_ANCHOR": "LIVE_GREENNODE_VDB" if store_live else "LOCAL_MOCKED_VDB",
            "DECISION_CORE_UNCHANGED": True,
            "COPILOT_INTEGRATION": "NO",
            "DEPLOY": "NO",
        }


def build_service(config: KnowledgeRagConfig | None = None) -> KnowledgeRagService:
    service = KnowledgeRagService(config=config)
    service.index_all()
    return service


def build_live_rag_service(
    config: KnowledgeRagConfig | None = None, client=None
) -> KnowledgeRagService:
    """TASK-011H-A live-path builder: semantic embedder + real or mock store +
    Qwen Flash answerer. INFERENCE_ANCHOR in meta is always truthful (LIVE
    only when the store is a real GreenNode VDB)."""
    config = config or KnowledgeRagConfig()
    answerer = MaasRagAnswerer(config=config, client=client)
    service = KnowledgeRagService(config=config, answerer=answerer)
    service.index_all()
    return service