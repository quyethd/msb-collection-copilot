from __future__ import annotations

from dataclasses import dataclass, field

from .config import KnowledgeRagConfig
from .embedding import Embedder, IdfLocalEmbedder, non_stop_tokens
from .models import KnowledgeChunk, RetrievalHit
from .vdb_client import InProcessMockVectorStore, VectorStore

_CURRENT_STATUSES = {"IMPLEMENTED", "PROVEN", "PROTOTYPE_ONLY"}
_RERANK_BOOST = 0.1
_RANK_WINDOW = 8
_DISTINCTIVE_DF_FRACTION = 0.2


@dataclass
class RetrievalResult:
    hits: list[RetrievalHit] = field(default_factory=list)
    query_vector: list[float] = field(default_factory=list)
    filtered_total: int = 0


def _query_tokens(question: str) -> set[str]:
    tokens = set(non_stop_tokens(question))
    lower = question.lower()
    if "ai" in set(non_stop_tokens(question)) and any(
        word in lower for word in ("quyết định", "decision")
    ):
        tokens.update({"con", "người"})
    return tokens


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
        self._all_chunks = list(all_chunks)
        self._bigram_docs: set[str] = set()
        self._token_docs: set[str] = set()
        self._df_ready: bool = False

    def index_all(self) -> int:
        if isinstance(self.embedder, IdfLocalEmbedder):
            self.embedder.fit([_chunk_text(chunk) for chunk in self._all_chunks])
        pairs = [
            (chunk, self.embedder.embed([_chunk_text(chunk)])[0])
            for chunk in self._all_chunks
        ]
        return self.store.upsert(pairs)

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        topic_filter: list[str] | None = None,
    ) -> RetrievalResult:
        candidates = self._candidates(topic_filter)
        query_vector = self.embedder.embed([question])[0]
        substore = InProcessMockVectorStore()
        substore.upsert(
            [
                (chunk, self.embedder.embed([_chunk_text(chunk)])[0])
                for chunk in candidates
            ]
        )
        hits = substore.search(query_vector, (top_k or self.config.top_k) * _RANK_WINDOW)
        hits = [hit for hit in hits if hit.score >= self.config.min_score]
        hits = self._rerank(hits, question)
        hits = hits[: (top_k or self.config.top_k)]
        return RetrievalResult(
            hits=hits,
            query_vector=query_vector,
            filtered_total=len(candidates),
        )

    def _rerank(
        self, hits: list[RetrievalHit], question: str
    ) -> list[RetrievalHit]:
        query_tokens = _query_tokens(question)
        reranked: list[RetrievalHit] = []
        for hit in hits:
            overlap = len(query_tokens & _chunk_tokens(hit.chunk))
            boost = 0.0
            if query_tokens and overlap:
                coverage = overlap / len(query_tokens)
                boost = _RERANK_BOOST * min(coverage, 1.0)
            reranked.append(
                RetrievalHit(
                    chunk=hit.chunk,
                    score=round(hit.score + boost, 4),
                )
            )
        reranked.sort(key=lambda hit: (hit.score, hit.chunk.chunk_id), reverse=True)
        return reranked

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