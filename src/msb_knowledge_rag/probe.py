"""Read-only live probes against GreenNode MaaS.

These probes only READ the remote catalog / validate availability. They must be
fault-tolerant and must never print an API key or any secret value.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .config import KnowledgeRagConfig


def probe_chat_models(config: KnowledgeRagConfig) -> dict:
    if not (config.llm_base_url and config.llm_api_key):
        return {"models": [], "attempted": False}
    request = urllib.request.Request(
        config.llm_base_url + "/models",
        headers={"Authorization": f"Bearer {config.llm_api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        return {"models": [], "error": f"HTTP {error.code}"}
    except Exception as error:
        return {"models": [], "error": repr(error)}
    models = []
    for entry in payload.get("data") or payload.get("models") or []:
        if isinstance(entry, dict):
            models.append(entry.get("id") or entry.get("model"))
        elif isinstance(entry, str):
            models.append(entry)
    return {"models": sorted(model for model in models if model)}


def probe_embeddings(config: KnowledgeRagConfig, model: str | None) -> dict:
    if not (config.llm_base_url and config.llm_api_key) or not model:
        return {"available": False, "reason": "no embedding model configured"}
    payload = {"model": model, "input": ["ping"]}
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        config.llm_base_url + "/embeddings",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm_api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        return {"available": False, "reason": f"HTTP {error.code}"}
    except Exception as error:
        return {"available": False, "reason": repr(error)}
    items = result.get("data") or []
    vector = (items[0].get("embedding") or []) if items else []
    return {"available": bool(vector), "vector_dimension": len(vector)}


def run_probe(config: KnowledgeRagConfig) -> dict:
    catalog = probe_chat_models(config)
    qwen_available = any(
        (model or "").startswith("qwen/") for model in catalog.get("models", [])
    )
    embedding_probe = probe_embeddings(config, config.qwen_fast_model)
    return {
        "LLM_BASE_URL": (config.llm_base_url or "").split("//")[-1]
        if config.llm_base_url
        else None,
        "chat_models": catalog.get("models", []),
        "QWEN_FAST_MODEL": config.qwen_fast_model,
        "QWEN_FAST_MODEL_AVAILABLE": "PASS" if qwen_available else "NOT_ON_CATALOG",
        "EMBEDDING_PROBE": embedding_probe,
        "GRENNODE_VDB_AVAILABLE": "NEEDS_APPROVAL",
        "LIVE_QWEN_RAG": "NOT_RUN",
        "PROJECT_KNOWLEDGE_RAG_LIVE": "NOT_PROVEN",
    }