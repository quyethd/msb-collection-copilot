from __future__ import annotations

import math
from typing import Protocol

from .models import KnowledgeChunk, RetrievalHit


class VectorStore(Protocol):
    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int: ...
    def search(self, query_vector: list[float], top_k: int) -> list[RetrievalHit]: ...
    def count(self) -> int: ...


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(v * v for v in vector))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    denom = _norm(a) * _norm(b)
    if denom == 0:
        return 0.0
    return dot / denom


class InProcessMockVectorStore:
    """Deterministic in-process vector store used for the LOCAL_MOCKED_VDB
    foundation proof and unit tests. Not a live GreenNode resource.
    """

    name = "greennode-vdb-inprocess-mock"

    def __init__(self) -> None:
        self._entries: list[tuple[KnowledgeChunk, list[float]]] = []

    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int:
        self._entries = list(pairs)
        return len(self._entries)

    def search(self, query_vector: list[float], top_k: int = 3) -> list[RetrievalHit]:
        scored = [
            RetrievalHit(chunk=chunk, score=cosine_similarity(query_vector, vector))
            for chunk, vector in self._entries
        ]
        scored.sort(key=lambda hit: (hit.score, hit.chunk.chunk_id), reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        return len(self._entries)


class OpenSearchVectorStoreAdapter:
    """Adapter for the future live GreenNode vDB OpenSearch (kNN) store.

    This path requires a provisioned endpooint (waiting for product-owner
    approval). Nothing in the foundation proof uses this class; it is provided
    so the integration plan has a real wiring point.
    """

    name = "greennode-vdb-opensearch"

    def __init__(self, host: str, index: str, **kwargs):
        self.host = host.rstrip("/")
        self.index = index

    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int:
        raise RuntimeError(
            "OpenSearch kNN store is not provisioned. "
            "GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL; LIVE_VDB_INGEST=NOT_RUN."
        )

    def search(self, query_vector: list[float], top_k: int = 3) -> list[RetrievalHit]:
        raise RuntimeError("LIVE_VDB_RETRIEVAL=NOT_RUN (OpenSearch endpoint not provisioned)")

    def count(self) -> int:
        raise RuntimeError("OpenSearch endpoint not provisioned")


class PostgresPGVectorAdapter:
    """Adapter for the future live GreenNode vDB PostgreSQL (pgvector) store."""

    name = "greennode-vdb-postgres-pgvector"

    def __init__(self, dsn: str, table: str, **kwargs):
        self.dsn = dsn
        self.table = table

    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int:
        raise RuntimeError(
            "pgvector store is not provisioned. "
            "GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL; LIVE_VDB_INGEST=NOT_RUN."
        )

    def search(self, query_vector: list[float], top_k: int = 3) -> list[RetrievalHit]:
        raise RuntimeError("LIVE_VDB_RETRIEVAL=NOT_RUN (pgvector endpoint not provisioned)")

    def count(self) -> int:
        raise RuntimeError("pgvector endpoint not provisioned")