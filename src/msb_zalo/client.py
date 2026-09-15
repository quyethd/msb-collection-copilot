"""Thin, dependency-free adapter for the official Zalo Bot Platform API.

The bot token is part of the API URL path, so this module never logs an
operation URL and never includes request URLs or tokens in exception text.
References: https://bot.zapps.me/en/docs/
"""
from __future__ import annotations

import gzip
import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_TOKEN_FILE = "/root/.config/msb-collection/zalo-bot-token"
DEFAULT_BASE_URL = "https://bot-api.zaloplatforms.com"

MAX_MESSAGE_TEXT = 2000


class ZaloBotAPIError(Exception):
    """Safe error for the Zalo Bot Platform API.

    The exception text never includes request URLs (the bot token is part of
    the URL path) or provider description text.
    """

    def __init__(self, code: Any, http_status: int | None = None):
        self.code = code
        self.http_status = http_status
        super().__init__(f"Zalo Bot API request failed (code={code})")


def _read_token(token_file: str | Path) -> str:
    path = Path(token_file)
    if not path.is_file():
        raise RuntimeError("Zalo bot token file is unavailable")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("Zalo bot token is unavailable")
    return token


def _error_code_from_body(body: dict[str, Any]) -> Any:
    for key in ("error_code", "code"):
        value = body.get(key)
        if value is not None:
            return value
    return None


class ZaloBotClient:
    """Official Zalo Bot API client (getMe / getUpdates / sendMessage / getWebhookInfo)."""

    def __init__(
        self,
        token: str | None = None,
        token_file: str | Path = DEFAULT_TOKEN_FILE,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 60.0,
        max_response_bytes: int = 262144,
    ):
        self._token = _read_token(token_file) if token is None else token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_response_bytes = max_response_bytes
        if not self._token:
            raise RuntimeError("Zalo bot token is unavailable")
        self._operation_uri = f"{self._base_url}/bot{self._token}/"

    def _url(self, operation: str) -> str:
        return f"{self._operation_uri}{operation}"

    def _call(self, operation: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps(params or {}).encode("utf-8")
        request = urllib.request.Request(
            self._url(operation),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read(self._max_response_bytes + 1)
        except urllib.error.HTTPError as error:
            try:
                body = json.loads(error.read(self._max_response_bytes + 1) or b"{}")
            except (ValueError, json.JSONDecodeError):
                body = {}
            code = _error_code_from_body(body) if isinstance(body, dict) else None
            raise ZaloBotAPIError(code or error.code, error.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ZaloBotAPIError("unreachable", None) from None
        if len(raw) > self._max_response_bytes:
            raise ZaloBotAPIError("response_too_large", None)
        text = self._decode(raw)
        try:
            envelope = json.loads(text)
        except (ValueError, json.JSONDecodeError):
            raise ZaloBotAPIError("invalid_json", None) from None
        if not isinstance(envelope, dict):
            raise ZaloBotAPIError("invalid_envelope", None)
        ok = envelope.get("ok")
        if ok is not True:
            code = _error_code_from_body(envelope)
            raise ZaloBotAPIError(code or "rejected", None)
        return envelope

    def _decode(self, raw: bytes) -> str:
        if len(raw) >= 2 and raw[:2] == b"\x1f\x8b":
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                    raw = stream.read(self._max_response_bytes + 1)
            except OSError:
                pass
        return raw.decode("utf-8", errors="replace")

    def _result(self, operation: str, params: dict[str, Any] | None = None) -> Any:
        return self._call(operation, params).get("result")

    def get_me(self) -> dict[str, Any]:
        result = self._result("getMe")
        if not isinstance(result, dict):
            raise ZaloBotAPIError("invalid_result", None)
        return result

    def get_updates(self, timeout: int | None = None, offset: int | None = None) -> list[dict[str, Any]]:
        params = {}
        if timeout is not None:
            params["timeout"] = str(int(timeout))
        if offset is not None:
            params["offset"] = str(int(offset))
        try:
            result = self._result("getUpdates", params)
        except ZaloBotAPIError as error:
            if error.code == 408:
                return []
            raise
        if result is None:
            return []
        if isinstance(result, dict):
            return [result]
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        raise ZaloBotAPIError("invalid_result", None)

    def send_message(self, chat_id: str, text: str) -> dict[str, Any]:
        if not isinstance(chat_id, str) or not chat_id.strip():
            raise ValueError("Zalo chat target is required")
        if not isinstance(text, str):
            raise ValueError("Zalo message text must be a string")
        text = text.strip()
        if not text:
            raise ValueError("Zalo message text is required")
        if len(text) > MAX_MESSAGE_TEXT:
            raise ValueError("Zalo message exceeds the 2000-character limit")
        result = self._result("sendMessage", {"chat_id": chat_id.strip(), "text": text})
        if not isinstance(result, dict):
            raise ZaloBotAPIError("invalid_result", None)
        return result

    def get_webhook_info(self) -> dict[str, Any]:
        result = self._result("getWebhookInfo")
        if not isinstance(result, dict):
            raise ZaloBotAPIError("invalid_result", None)
        return result