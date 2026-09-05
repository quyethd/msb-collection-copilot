from __future__ import annotations

import time
from typing import Callable

from .answerer import DeterministicGroundedAnswerer, RagAnswerer
from .classifier import classify_question_type, infer_topics
from .config import (
    BOUNDARY_RESPONSES,
    LOW_CONFIDENCE_REFUSAL,
    KNOWLEDGE_VERSION,
    SOURCE_COMMIT,
    KnowledgeRagConfig,
)
from .corpus import load_corpus
from .embedding import Embedder, IdfLocalEmbedder
from .models import QuestionType, RagAnswer
from .retriever import IndexedRetrievalPipeline, _chunk_text
from .security import security_scan
from .vdb_client import InProcessMockVectorStore, VectorStore

BoundaryHint = Callable[[QuestionType], str | None]


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
        self.embedder = embedder or IdfLocalEmbedder()
        self.posstore = store or InProcessMockVectorStore()
        self.answerer = answerer or DeterministicGroundedAnswerer()
        self.boundary_hint = boundary_hint
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
        qtype = classify_question_type(text)
        if qtype != "PROJECT_KNOWLEDGE":
            return self._boundary(text, qtype, started)

        topics = infer_topics(text)
        retrieval_started = time.perf_counter()
        result = self.pipeline.retrieve(question=text)
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000
        if not result.hits:
            return RagAnswer(
                status="LOW_CONFIDENCE",
                path="rag_qwen",
                knowledge_type="PROJECT_KNOWLEDGE",
                answer=LOW_CONFIDENCE_REFUSAL,
                classification="LOW_CONFIDENCE",
                sources=self._sources(result.hits),
                meta=self._meta(
                    retrieval_ms=retrieval_ms,
                    question_type="PROJECT_KNOWLEDGE",
                    topics=topics,
                    started=started,
                ),
            )
        if self.pipeline.evidence_ok(result.hits, text) is False:
            return RagAnswer(
                status="LOW_CONFIDENCE",
                path="rag_qwen",
                knowledge_type="PROJECT_KNOWLEDGE",
                answer=LOW_CONFIDENCE_REFUSAL,
                classification="LOW_CONFIDENCE",
                sources=self._sources(result.hits),
                meta=self._meta(
                    retrieval_ms=retrieval_ms,
                    question_type="PROJECT_KNOWLEDGE",
                    topics=topics,
                    started=started,
                ),
            )
        model_started = time.perf_counter()
        answer_text = self.answerer.answer(text, [hit.chunk for hit in result.hits])
        model_ms = (time.perf_counter() - model_started) * 1000
        return RagAnswer(
            status="ANSWERED",
            path="rag_qwen",
            knowledge_type="PROJECT_KNOWLEDGE",
            answer=answer_text,
            sources=self._sources(result.hits),
            classification="PROJECT_KNOWLEDGE",
            meta=self._meta(
                retrieval_ms=retrieval_ms,
                model_ms=model_ms,
                question_type="PROJECT_KNOWLEDGE",
                topics=topics,
                started=started,
            ),
        )

    def _meta(self, retrieval_ms: float, started: float, **extra) -> dict:
        meta = {
            "knowledge_version": self.config.knowledge_version,
            "source_commit": SOURCE_COMMIT,
            "embedder": getattr(self.embedder, "name", self.embedder.__class__.__name__),
            "store": getattr(self.posstore, "name", self.posstore.__class__.__name__),
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
        return {
            "knowledge_version": self.config.knowledge_version,
            "source_commit": SOURCE_COMMIT,
            "noop_documents": len({chunk.document_id for chunk in self.all_chunks}),
            "corpus_chunks": len(self.all_chunks),
            "QWEN_FAST_MODEL": self.config.qwen_fast_model,
            "QWEN_FAST_MODEL_AVAILABLE": "PASS"
            if self.config.qwen_fast_model
            else "NOT_CONFIGURED",
            "GRENNODE_VDB_AVAILABLE": "NEEDS_APPROVAL",
            "LIVE_VDB_INGEST": "NOT_RUN",
            "LIVE_VDB_RETRIEVAL": "NOT_RUN",
            "LIVE_QWEN_RAG": "NOT_RUN",
            "PROJECT_KNOWLEDGE_RAG_LIVE": "NOT_PROVEN",
            "EMBEDDING_MODEL_STATUS": "NONE_AVAILABLE",
            "INFERENCE_ANCHOR": "LOCAL_MOCKED_VDB",
            "DECISION_CORE_UNCHANGED": True,
            "COPILOT_INTEGRATION": "NO",
            "DEPLOY": "NO",
        }


def build_service(config: KnowledgeRagConfig | None = None) -> KnowledgeRagService:
    service = KnowledgeRagService(config=config)
    service.index_all()
    return service