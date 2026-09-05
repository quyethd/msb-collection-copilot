from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import KnowledgeRagConfig
from .embedding import (
    DeterministicLocalEmbedder,
    Embedder,
    IdfLocalEmbedder,
    non_stop_tokens,
)
from .models import KnowledgeChunk, RetrievalHit
from .vdb_client import InProcessMockVectorStore, VectorStore

_CURRENT_STATUSES = {"IMPLEMENTED", "PROVEN", "PROTOTYPE_ONLY"}
_RERANK_BOOST = 0.1
_RANK_WINDOW = 16
_DISTINCTIVE_DF_FRACTION = 0.2
_HYBRID_LEXICAL_WEIGHT = 0.55


@dataclass
class RetrievalResult:
    hits: list[RetrievalHit] = field(default_factory=list)
    query_vector: list[float] = field(default_factory=list)
    filtered_total: int = 0
    top_cosine: float = 0.0


@dataclass
class RetrievalPerf:
    embedding_ms: float = 0.0
    search_ms: float = 0.0
    rerank_ms: float = 0.0
    candidate_count: int = 0


def _query_tokens(question: str) -> set[str]:
    return set(non_stop_tokens(question))


def _chunk_tokens(chunk: KnowledgeChunk) -> set[str]:
    return set(non_stop_tokens(_chunk_text(chunk)))


def _chunk_text(chunk: KnowledgeChunk) -> str:
    return f"{chunk.title}\n{chunk.heading}\n{chunk.content}"


class IndexedRetrievalPipeline:
    def __init__(
        self,
        config: KnowledgeRagConfig,
        store: VectorStore,
        embedder: Embedder,
        all_chunks: list[KnowledgeChunk],  # type: ignore[name-defined]
    ):
        self.config = config
        self.store = store
        self.embedder = embedder
        self.semantic = not isinstance(embedder, IdfLocalEmbedder) and not isinstance(
            embedder, DeterministicLocalEmbedder
        )
        self._all_chunks = list(all_chunks)
        self._bigram_docs: set[str] = set()
        self._token_docs: set[str] = set()
        self._df_ready: bool = False
        self.last_perf: RetrievalPerf | None = None
        self._chunk_vectors: dict[str, list[float]] = {}

    def index_all(self) -> int:
        if isinstance(self.embedder, IdfLocalEmbedder):
            self.embedder.fit([_chunk_text(chunk) for chunk in self._all_chunks])
        pairs = []
        for chunk in self._all_chunks:
            vector = self._chunk_vectors.get(chunk.chunk_id)
            if vector is None:
                vector = self.embedder.embed([_chunk_text(chunk)])[0]
                self._chunk_vectors[chunk.chunk_id] = vector
            pairs.append((chunk, vector))
        return self.store.upsert(pairs)

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        topic_filter: list[str] | None = None,
    ) -> RetrievalResult:
        perf = RetrievalPerf()
        self.last_perf = perf
        candidates = self._candidates(topic_filter)
        perf.candidate_count = len(candidates)

        embedding_started = time.perf_counter()
        query_vector = self.embedder.embed([question])[0]
        perf.embedding_ms = (time.perf_counter() - embedding_started) * 1000

        window = (top_k or self.config.top_k) * _RANK_WINDOW
        search_started = time.perf_counter()
        if self.store.is_live():
            hits = self.store.search(query_vector, window)
            perf.candidate_count = self.store.count()
        else:
            substore = InProcessMockVectorStore()
            substore.upsert(
                [
                    (chunk, self._vector_for(chunk))
                    for chunk in candidates
                ]
            )
            hits = substore.search(query_vector, window)
        perf.search_ms = (time.perf_counter() - search_started) * 1000

        hits = [hit for hit in hits if hit.score >= self.config.min_score]
        top_cosine = hits[0].score if hits else 0.0
        rerank_started = time.perf_counter()
        if self.semantic:
            hits = self.hybrid_rescore(hits, question)
        else:
            hits = self._rerank(hits, question)
        perf.rerank_ms = (time.perf_counter() - rerank_started) * 1000
        hits = hits[: (top_k or self.config.top_k)]
        return RetrievalResult(
            hits=hits,
            query_vector=query_vector,
            filtered_total=perf.candidate_count,
            top_cosine=top_cosine,
        )

    def _rerank(
        self, hits: list[RetrievalHit], question: str
    ) -> list[RetrievalHit]:
        query_tokens = _query_tokens(question)
        denominator = max(len(query_tokens), 1)
        reranked: list[RetrievalHit] = []
        for hit in hits:
            overlap = len(query_tokens & _chunk_tokens(hit.chunk))
            boost = 0.0
            if query_tokens and overlap:
                coverage = overlap / denominator
                boost = _RERANK_BOOST * min(coverage, 1.0)
            reranked.append(
                RetrievalHit(
                    chunk=hit.chunk,
                    score=round(hit.score + boost, 4),
                )
            )
        reranked.sort(key=lambda hit: (hit.score, hit.chunk.chunk_id), reverse=True)
        return reranked

    def hybrid_rescore(
        self, hits: list[RetrievalHit], question: str
    ) -> list[RetrievalHit]:
        """Hybrid blend: cosine + lexical coverage (shared token + bigram).

        Used by the live semantic tier so that queries sharing many lexical
        terms with a document (e.g. B2 'nguồn quyết định nghiệp vụ', D1 'tăng
        hiệu quả thu hồi') are lifted past cosine-only neighbors, while the
        semantic gate still governs admission.
        """
        query_tokens = _query_tokens(question)
        ordered_tokens = list(query_tokens)
        denominator = max(len(query_tokens), 1)
        self._ensure_vocab()
        rescored: list[RetrievalHit] = []
        for hit in hits:
            chunk_tokens = _chunk_tokens(hit.chunk)
            overlap = len(query_tokens & chunk_tokens)
            bigram_hit = any(
                f"{first} {second}" in self._bigram_docs
                for first, second in zip(ordered_tokens, ordered_tokens[1:])
            )
            coverage = overlap / denominator
            lexical = coverage + (0.2 if bigram_hit else 0.0)
            rescored.append(
                RetrievalHit(
                    chunk=hit.chunk,
                    score=round(hit.score + _HYBRID_LEXICAL_WEIGHT * lexical, 4),
                )
            )
        rescored.sort(key=lambda hit: (hit.score, hit.chunk.chunk_id), reverse=True)
        return rescored

    def top_score(self, hits: list[RetrievalHit]) -> float:
        return hits[0].score if hits else 0.0

    def lexical_features(self, question: str) -> dict:
        """Confidence features only — lexical phrase presence is advisory for
        the semantic tier, never a hard admission gate (TASK-011H-A)."""
        self._ensure_vocab()
        tokens = non_stop_tokens(question)
        bigram_hit = False
        if len(tokens) >= 2:
            bigram_hit = any(
                f"{first} {second}" in self._bigram_docs
                for first, second in zip(tokens, tokens[1:])
            )
        elif tokens:
            bigram_hit = tokens[0] in self._token_docs
        return {
            "query_token_count": len(tokens),
            "query_bigram_hit": bigram_hit,
        }

    def evidence_overlap(self, hits: list[RetrievalHit], question: str) -> int:
        query_tokens = _query_tokens(question)
        if not hits or not query_tokens:
            return 0
        top = hits[0].chunk
        return len(query_tokens & _chunk_tokens(top))

    def evidence_ok(self, hits: list[RetrievalHit], question: str) -> bool:
        """Phrase-evidence gate: refuse when no word-sequence in the question
        has any presence in the corpus (e.g., 'thời tiết', 'bán đảo')."""
        if not hits:
            return False
        self._ensure_vocab()
        tokens = non_stop_tokens(question)
        if not tokens:
            return False
        if len(tokens) >= 2:
            for first, second in zip(tokens, tokens[1:]):
                bigram = f"{first} {second}"
                if bigram in self._bigram_docs:
                    return True
            return False
        return tokens[0] in self._token_docs

    def _ensure_vocab(self) -> None:
        if self._df_ready:
            return
        for chunk in self._candidates(None):
            tokens = non_stop_tokens(_chunk_text(chunk))
            self._token_docs.update(tokens)
            if len(tokens) >= 2:
                self._bigram_docs.update(
                    f"{first} {second}" for first, second in zip(tokens, tokens[1:])
                )
        self._df_ready = True

    def _vector_for(self, chunk: KnowledgeChunk) -> list[float]:
        vector = self._chunk_vectors.get(chunk.chunk_id)
        if vector is None:
            vector = self.embedder.embed([_chunk_text(chunk)])[0]
            self._chunk_vectors[chunk.chunk_id] = vector
        return vector

    def _candidates(self, topic_filter: list[str] | None) -> list[KnowledgeChunk]:
        selected = []
        for chunk in self._all_chunks:
            if chunk.knowledge_version != self.config.knowledge_version:
                continue
            if chunk.source_type not in ("curated", "official", "auto"):
                continue
            if chunk.implementation_status not in _CURRENT_STATUSES:
                continue
            if topic_filter and chunk.topic not in topic_filter:
                continue
            selected.append(chunk)
        return selected