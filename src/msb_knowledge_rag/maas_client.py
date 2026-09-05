"""OpenAI-compatible chat client for the GreenNode MaaS endpoint.

Only `choices[0].message.content` is ever returned. `reasoning_content`,
reasoning_tokens and any other field are deliberately discarded so private
chain-of-thought can never appear in an answer or in logs.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import QWEN_FAST_MODEL, KnowledgeRagConfig


class MaaSChatUnavailable(Exception):
    pass


class MaaSChatClient:
    def __init__(self, base_url: str, api_key: str, model: str = QWEN_FAST_MODEL):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0
    ) -> tuple[str, str]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            raise MaaSChatUnavailable(f"chat request failed: HTTP {error.code}") from error
        except Exception as error:
            raise MaaSChatUnavailable(f"chat request failed: {error!r}") from error
        content = (
            (result.get("choices") or [{}])[0].get("message") or {}
        ).get("content") or ""
        return content, self.model


def build_chat_client(config: KnowledgeRagConfig) -> MaaSChatClient:
    if not config.live_maas_configured():
        raise MaaSChatUnavailable(
            "GreenNode MaaS chat is not configured (LLM_BASE_URL / LLM_API_KEY)"
        )
    return MaaSChatClient(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.qwen_fast_model or QWEN_FAST_MODEL,
    )