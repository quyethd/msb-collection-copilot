from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from hashlib import sha256
from typing import Protocol

from .config import LOCAL_EMBEDDING_DIM, LOCAL_TOKEN_WEIGHT

_TOKEN_RE = re.compile(r"[^\W_]+(?:[’']\w+)?")

STOPWORDS = frozenset(
    "các của và là trong cho có không một những với để thì gì như thế nào "
    "làm sao bao nhiêu đang sẽ phải cần qua bởi từ tại theo này đó trên dưới "
    "giữa khi nào cũng ra vào ở về rằng hoặc bị được đã hơn nhất rất đều mọi "
    "mỗi chính khác cùng sau trước hiện tại hay một số các loại loài the of "
    "and to in on for within into over after then them are was were is what "
    "which when how about with or a an per as at than from gồm mục hạng hôm nay".split()
)


def non_stop_tokens(text: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


class EmbeddingUnavailable(Exception):
    pass


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def dimension(self) -> int: ...


class AvailabilityProbe(Protocol):
    def probe(self) -> dict: ...


class DeterministicLocalEmbedder:
    """Deterministic, dependency-free bag-of-token embedder.

    Explicitly a LOCAL adapter for te foundation/local proof. It is NOT a live
    GreenNode embedding model and must never be presented as one.
    """

    name = "deterministic-local"

    def __init__(self, dim: int = LOCAL_EMBEDDING_DIM):
        self.dim = max(dim, 512)

    def dimension(self) -> int:
        return self.dim

    def _tokens(self, text: str) -> list[str]:
        words = non_stop_tokens(text)
        if not words:
            return []
        if len(words) < 2:
            return words
        bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
        return words + bigrams

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in self._tokens(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            value = 1.0 + LOCAL_TOKEN_WEIGHT
            vector[index] += value
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


class MaasEmbeddingClient:
    """Adapter for a GreenNode MaaS embeddings endpoint.

    A live probe against the authorized catalog returned HTTP 404 for every
    chat model (`EMBEDDING_MODEL_STATUS = NONE_AVAILABLE`), so this client is
    only instantiated when an embedding-capable model is provisioned. It is not
    part of the local foundation proof.
    """

    name = "greennode-maas-embeddings"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def dimension(self) -> int:
        return 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        payload = {"model": self.model, "input": texts}
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self.base_url + "/embeddings",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise EmbeddingUnavailable(f"embedding request failed: {error.code}") from error
        except Exception as error:
            raise EmbeddingUnavailable(f"embedding request failed: {error!r}") from error
        items = result.get("data") or []
        if not items:
            raise EmbeddingUnavailable("embedding response returned no data")
        return [item.get("embedding") or [] for item in items]


def probe_embedding_availability(
    base_url: str | None, api_key: str | None, model: str | None
) -> dict:
    if not (base_url and api_key and model):
        return {"available": False, "status": "NONE_AVAILABLE"}
    client = MaasEmbeddingClient(base_url, api_key, model)
    try:
        vectors = client.embed(["ping"])
        return {
            "available": bool(vectors) and bool(vectors[0]),
            "status": "AVAILABLE" if vectors and vectors[0] else "UNKNOWN",
        }
    except EmbeddingUnavailable as error:
        return {"available": False, "status": "NONE_AVAILABLE", "detail": str(error)}


def default_embedder() -> DeterministicLocalEmbedder:
    return DeterministicLocalEmbedder()


class IdfLocalEmbedder(DeterministicLocalEmbedder):
    """Deterministic local embedder with corpus IDF weighting.

    Fit on the knowledge corpus once so rare diagnostic terms dominate over
    generic ones. Still a LOCAL adapter — never presented as a live GreenNode
    model.
    """

    name = "deterministic-local-idf"

    def __init__(self, dim: int = LOCAL_EMBEDDING_DIM):
        super().__init__(dim=dim)
        self._idf: dict[str, float] = {}

    def fit(self, texts: list[str]) -> "IdfLocalEmbedder":
        document_frequency: dict[str, int] = {}
        total = max(len(texts), 1)
        for text in texts:
            seen = set(self._tokens(text))
            for token in seen:
                document_frequency[token] = document_frequency.get(token, 0) + 1
        self._idf = {
            token: math.log((total + 1) / (frequency + 1)) + 1.0
            for token, frequency in document_frequency.items()
        }
        return self

    def _token_weight(self, token: str) -> float:
        return self._idf.get(token, 1.0)

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in self._tokens(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            vector[index] += self._token_weight(token)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector