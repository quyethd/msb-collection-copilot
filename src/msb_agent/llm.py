from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        ...


class GreenNodeMaaSClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": max_tokens, "temperature": temperature}
        body = json.dumps(payload).encode()
        request = urllib.request.Request(self.base_url + "/chat/completions", data=body,
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {self.api_key}"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result: dict[str, Any] = json.load(response)
        except urllib.error.HTTPError as error:
            try:
                result = json.load(error)
            except Exception:
                return None, None
        except Exception:
            return None, None
        message = ((result.get("choices") or [{}])[0].get("message") or {})
        return message.get("content"), result.get("model")


def maas_client_from_env() -> GreenNodeMaaSClient | None:
    base_url = os.environ.get("LLM_BASE_URL")
    api_key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")
    if base_url and api_key and model:
        return GreenNodeMaaSClient(base_url, api_key, model)
    return None
