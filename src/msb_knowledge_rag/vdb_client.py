from __future__ import annotations

import base64
import json
import math
import urllib.error
import urllib.request
from typing import Protocol

from .models import KnowledgeChunk, RetrievalHit


class VectorStore(Protocol):
    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int: ...
    def search(self, query_vector: list[float], top_k: int) -> list[RetrievalHit]: ...
    def count(self) -> int: ...
    def is_live(self) -> bool: ...


class VdbUnavailable(Exception):
    """Raised when the Live GreenNode VDB cannot be reached or was never
    provisioned. Never includes credentials in the message."""


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

    def is_live(self) -> bool:
        return False

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


class GreennodeVdbOpenSearchClient:
    """Live GreenNode vDB OpenSearch (kNN) client.

    Uses the official vDB OpenSearch REST surface with basic-auth over the
    master user. The index mapping registers a dense vector field (kNN,
    cosinesimil). Upserts are idempotent (document _id = chunk_id). The cosine
    score is recomputed client-side so thresholds calibrated on the local path
    (SEMANTIC_MIN_SCORE = 0.38) remain exactly comparable.

    Requires a provisioned endpoint + master credentials. Until then every
    method raises VdbUnavailable (GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL).
    Credentials are never logged and never included in error messages.
    """

    name = "greennode-vdb-opensearch"

    def __init__(self, config, dimension: int):
        self.config = config
        self.host = (config.grennode_vdb_endpoint or "").rstrip("/")
        self.index = config.grennode_vdb_index or "msb-collection-knowledge"
        self.user = config.grennode_vdb_user
        self.password = config.grennode_vdb_password
        self.dimension = dimension
        self._index_ready = False

    def is_live(self) -> bool:
        return bool(self.host and self.index)

    def _require_configured(self) -> None:
        if not self.is_live():
            raise VdbUnavailable(
                "GreenNode vDB OpenSearch is not provisioned. "
                "GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL; LIVE_VDB_INGEST=NOT_RUN."
            )

    def _request(self, method: str, path: str, body=None) -> dict:
        self._require_configured()
        url = f"{self.host}/{path.lstrip('/')}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        if self.user:
            credentials = f"{self.user}:{self.password or ''}".encode()
            request.add_header("Authorization", "Basic " + base64.b64encode(credentials).decode())
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            raise VdbUnavailable(f"vDB OpenSearch {method} {path} failed: HTTP {error.code} {detail!r}") from error
        except Exception as error:
            raise VdbUnavailable(f"vDB OpenSearch {method} {path} failed: {error!r}") from error

    def _index_exists(self) -> bool:
        try:
            self._request("GET", self.index)
            return True
        except VdbUnavailable:
            return False

    def _ensure_index(self) -> None:
        if self._index_ready:
            return
        mapping = {
            "settings": {
                "index": {"knn": True, "number_of_shards": 1, "number_of_replicas": 0}
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.dimension,
                        "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "lucene"},
                    },
                    "document_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "section": {"type": "keyword"},
                    "topic": {"type": "keyword"},
                    "audience": {"type": "keyword"},
                    "knowledge_version": {"type": "keyword"},
                    "source_commit": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "implementation_status": {"type": "keyword"},
                    "heading": {"type": "text"},
                    "order": {"type": "integer"},
                    "content": {"type": "text"},
                }
            },
        }
        try:
            result = self._request("PUT", self.index, mapping)
        except VdbUnavailable:
            if not self._index_exists():
                raise
        else:
            if result.get("acknowledged") is not True:
                raise VdbUnavailable(
                    f"vDB OpenSearch index creation not acknowledged: {result!r}"
                )
        self._index_ready = True

    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int:
        if not pairs:
            return 0
        self._ensure_index()
        lines: list[str] = []
        for chunk, vector in pairs:
            lines.append(
                json.dumps({"index": {"_index": self.index, "_id": chunk.chunk_id}}, ensure_ascii=False)
            )
            doc = self._document(chunk, vector)
            lines.append(json.dumps(doc, ensure_ascii=False))
        payload = ("\n".join(lines) + "\n").encode()
        result = self._request("POST", "_bulk", payload)
        items = result.get("items", [])
        indexed = 0
        for item in items:
            op = item.get("index") or item.get("create") or {}
            if op.get("error") is None and op.get("status", 0) in (200, 201):
                indexed += 1
        return indexed

    def search(self, query_vector: list[float], top_k: int = 3) -> list[RetrievalHit]:
        self._ensure_index()
        body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": list(query_vector),
                        "k": top_k + 8,
                    }
                }
            },
        }
        result = self._request("POST", f"{self.index}/_search", body)
        hits: list[RetrievalHit] = []
        for hit in (result.get("hits") or {}).get("hits", []):
            source = hit.get("_source") or {}
            chunk = self._chunk_from_source(source)
            if chunk is None:
                continue
            score = cosine_similarity(list(query_vector), source.get("embedding") or [])
            hits.append(RetrievalHit(chunk=chunk, score=round(score, 4)))
        hits.sort(key=lambda hit: (hit.score, hit.chunk.chunk_id), reverse=True)
        return hits

    def count(self) -> int:
        self._ensure_index()
        result = self._request("GET", f"{self.index}/_count")
        return int(result.get("count", 0))

    @staticmethod
    def _document(chunk: KnowledgeChunk, vector: list[float]) -> dict:
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "section": chunk.section,
            "topic": chunk.topic,
            "audience": chunk.audience,
            "knowledge_version": chunk.knowledge_version,
            "source_commit": chunk.source_commit,
            "source_type": chunk.source_type,
            "implementation_status": chunk.implementation_status,
            "heading": chunk.heading,
            "order": chunk.order,
            "content": chunk.content,
            "embedding": list(vector),
        }

    @staticmethod
    def _chunk_from_source(source: dict) -> KnowledgeChunk | None:
        required = ("chunk_id", "document_id")
        if not all(source.get(key) for key in required):
            return None
        return KnowledgeChunk(
            chunk_id=source["chunk_id"],
            document_id=source["document_id"],
            title=source.get("title", ""),
            section=source.get("section", ""),
            topic=source.get("topic", ""),
            audience=source.get("audience", ""),
            knowledge_version=source.get("knowledge_version", ""),
            source_commit=source.get("source_commit", ""),
            source_type=source.get("source_type", ""),
            implementation_status=source.get("implementation_status", ""),
            heading=source.get("heading", ""),
            order=int(source.get("order", 0) or 0),
            content=source.get("content", ""),
        )


class PostgresPGVectorAdapter:
    """Adapter for the future live GreenNode vDB PostgreSQL (pgvector) store."""

    name = "greennode-vdb-postgres-pgvector"

    def __init__(self, dsn: str, table: str, **kwargs):
        self.dsn = dsn
        self.table = table

    def is_live(self) -> bool:
        return False

    def upsert(self, pairs: list[tuple[KnowledgeChunk, list[float]]]) -> int:
        raise VdbUnavailable(
            "pgvector store is not provisioned. "
            "GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL; LIVE_VDB_INGEST=NOT_RUN."
        )

    def search(self, query_vector: list[float], top_k: int = 3) -> list[RetrievalHit]:
        raise VdbUnavailable("LIVE_VDB_RETRIEVAL=NOT_RUN (pgvector endpoint not provisioned)")

    def count(self) -> int:
        raise VdbUnavailable("pgvector endpoint not provisioned")


def build_store(config, dimension: int = 512) -> VectorStore:
    """Local proof uses the in-process mock; a provisioned GreenNode vDB
    OpenSearch endpoint switches the store to the live kNN client."""
    if config.greennode_vdb_configured():
        return GreennodeVdbOpenSearchClient(config, dimension=dimension)
    return InProcessMockVectorStore()