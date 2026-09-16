from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .models import CaseBrief, PROMPT_VERSION, TOOL_REGISTRY_VERSION


class CaseBriefCache:
    """Version-aware cache for Case Briefs.

    Cache key includes: cif, data_version_hash, decision_version_hash,
    simulation_hash, prompt_version, tool_registry_version.
    Not just CIF.
    """

    def __init__(self, ttl_seconds: int = 600):
        self._store: dict[str, tuple[float, dict[str, Any]]] = {}
        self._ttl = ttl_seconds

    def _key(self, cif: str, context_hash: str, decision_hash: str,
             simulation_hash: str) -> str:
        parts = [
            cif,
            context_hash,
            decision_hash,
            simulation_hash,
            PROMPT_VERSION,
            TOOL_REGISTRY_VERSION,
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def get(self, cif: str, context_hash: str, decision_hash: str,
            simulation_hash: str) -> dict[str, Any] | None:
        key = self._key(cif, context_hash, decision_hash, simulation_hash)
        entry = self._store.get(key)
        if entry is None:
            return None
        cached_at, data = entry
        if time.time() - cached_at > self._ttl:
            del self._store[key]
            return None
        return data

    def put(self, cif: str, context_hash: str, decision_hash: str,
            simulation_hash: str, data: dict[str, Any]) -> None:
        key = self._key(cif, context_hash, decision_hash, simulation_hash)
        self._store[key] = (time.time(), data)

    def invalidate(self, cif: str) -> None:
        keys_to_remove = [k for k, (_, v) in self._store.items() if v.get("cif") == cif]
        for key in keys_to_remove:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)
