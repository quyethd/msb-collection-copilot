from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

try:
    import requests
except ImportError:  # pragma: no cover - urllib remains the minimal fallback
    requests = None


class LLMClient(Protocol):
    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        ...


class GreenNodeMaaSClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: float = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": max_tokens, "temperature": temperature}
        body = json.dumps(payload).encode()
        request = urllib.request.Request(self.base_url + "/chat/completions", data=body,
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {self.api_key}"}, method="POST")
        try:
            if requests is not None:
                session = requests.Session()
                session.trust_env = False
                response = session.post(self.base_url + "/chat/completions", json=payload,
                                        headers={"Content-Type": "application/json",
                                                 "Authorization": f"Bearer {self.api_key}"},
                                        timeout=self.timeout_seconds)
                response.raise_for_status()
                result = response.json()
            else:
                result = None
            if result is None:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    result = json.load(response)
        except urllib.error.HTTPError as error:
            try:
                result = json.load(error)
            except Exception:
                return None, None
        except Exception:
            return None, None
        message = ((result.get("choices") or [{}])[0].get("message") or {})
        return message.get("content"), result.get("model")


def maas_client_from_env(timeout_seconds: float = 60) -> GreenNodeMaaSClient | None:
    base_url = os.environ.get("LLM_BASE_URL")
    api_key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")
    if base_url and api_key and model:
        return GreenNodeMaaSClient(base_url, api_key, model, timeout_seconds=timeout_seconds)
    return None


def fast_maas_client_from_env(timeout_seconds: float = 8) -> GreenNodeMaaSClient | None:
    """Optional separate fast path; absent configuration intentionally stays local."""
    base_url = os.environ.get("LLM_FAST_BASE_URL")
    api_key = os.environ.get("LLM_FAST_API_KEY")
    model = os.environ.get("LLM_FAST_MODEL")
    if base_url and api_key and model:
        return GreenNodeMaaSClient(base_url, api_key, model, timeout_seconds=timeout_seconds)
    return None
