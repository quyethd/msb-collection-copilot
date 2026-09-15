"""Dedicated long-polling worker for the official Zalo Bot Platform API.

The worker is the only poller for the bot token. It handles inbound private
text events and hands them to the authenticated loopback ZaloBridge control
plane, which runs the existing MSB Copilot orchestration. No conversation text
is ever treated as business truth; only bounded routing hints are forwarded.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

from msb_zalo.client import ZaloBotClient, ZaloBotAPIError

PAIRING_PHRASE = "MSB DEMO"
MAX_UPDATE_TEXT = 4500
DEFAULT_SECRET_FILE = "/root/.config/msb-collection/zalo-inbound-shared-secret"
WELCOME_TEXT = "Đã kết nối Trợ lý Thu hồi Nợ MSB. Bạn có thể hỏi về khách hàng demo; dữ liệu hiển thị là mô phỏng."
ONBOARDING_NO_BINDING = "Chưa có người nhận được cấu hình để ghép nối. Vui lòng đợi người điều phối demo hướng dẫn."

_RECENT_MAX = 256
_RETRY_MAX = 32
_KNOWN_FINAL = frozenset({"ignored", "paired", "responded", "onboarded", "ignored_unknown", "blocked", "duplicate"})

_logger = logging.getLogger("msb.zalo_worker")


def preflight(client: ZaloBotClient) -> dict[str, Any]:
    """Verify the bot is reachable and no webhook blocks long-polling."""
    me = client.get_me()
    try:
        webhook_url = client.get_webhook_info().get("url")
    except ZaloBotAPIError as error:
        if error.code == 404:
            webhook_url = None
        else:
            raise
    if webhook_url:
        raise RuntimeError("Zalo bot has a registered webhook; long-poll conflicts — stop")
    return {"bot_id": str(me.get("id", "")), "display_name": str(me.get("account_name", "")),
            "webhook_configured": bool(webhook_url)}


def _log_failure(operation: str, error: Exception) -> None:
    _logger.warning("zalo %s failed (%s)", operation, type(error).__name__)


class ChatMemory:
    """Bounded rolling per-chat conversation memory (routing hints only)."""

    MAX_CHATS = 200
    MAX_TURNS = 10
    TRUNCATE = 160

    def __init__(self) -> None:
        self._chats: dict[str, list[dict[str, str]]] = {}
        self._lock = threading.Lock()

    def remember_user(self, chat_id: str, text: str) -> None:
        self._append(chat_id, {"role": "user", "text": text[: self.TRUNCATE], "intent": "", "path": ""})

    def remember_assistant(self, chat_id: str, intent: Any, path: Any) -> None:
        self._append(chat_id, {
            "role": "assistant", "text": "",
            "intent": str(intent or "")[: self.TRUNCATE], "path": str(path or "")[: self.TRUNCATE],
        })

    def _append(self, chat_id: str, turn: dict[str, str]) -> None:
        with self._lock:
            turns = self._chats.get(chat_id)
            if turns is None:
                if len(self._chats) >= self.MAX_CHATS:
                    del self._chats[next(iter(self._chats))]
                turns = []
                self._chats[chat_id] = turns
            turns.append(turn)
            if len(turns) > self.MAX_TURNS:
                del turns[: len(turns) - self.MAX_TURNS]

    def context_for(self, chat_id: str) -> dict[str, str]:
        with self._lock:
            turns = list(self._chats.get(chat_id) or [])
        context: dict[str, str] = {}
        for turn in reversed(turns):
            if turn["role"] == "assistant":
                if context.get("previous_intent") is None and turn["intent"]:
                    context["previous_intent"] = turn["intent"]
                    context["previous_path"] = turn["path"]
            elif turn["role"] == "user" and context.get("previous_user_question") is None and turn["text"]:
                context["previous_user_question"] = turn["text"]
            if context.get("previous_intent") is not None and context.get("previous_user_question") is not None:
                break
        if context:
            context["active_cif"] = "SYN002846"
            context["previous_topic"] = context.get("previous_intent", "")
        return context


class ZaloPollingWorker:
    def __init__(
        self,
        client: ZaloBotClient,
        inbound_url: str,
        secret_file: str = DEFAULT_SECRET_FILE,
        *,
        poll_timeout: int = 30,
        loop_interval: float = 1.0,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        request_timeout: float = 15.0,
        forward_retries: int = 2,
        heartbeat_file: str | None = None,
        heartbeat_interval: float = 10.0,
        watermark_file: str | None = None,
    ):
        self._client = client
        self._inbound_url = inbound_url
        self._secret_file = secret_file
        self._poll_timeout = int(poll_timeout)
        self._loop_interval = loop_interval
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max
        self._request_timeout = request_timeout
        self._forward_retries = int(forward_retries)
        self._heartbeat_file = Path(heartbeat_file) if heartbeat_file else None
        self._heartbeat_interval = heartbeat_interval
        self._watermark_file = Path(watermark_file) if watermark_file else None
        self._conversations = ChatMemory()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._secret: str | None = None
        self._secret_lock = threading.Lock()
        self._watermark_lock = threading.Lock()
        self._load_watermark()

    def _load_watermark(self) -> None:
        self._retry: list[dict[str, Any]] = []
        self._recent_ids: set[int] = set()
        self._recent_order: deque[int] = deque(maxlen=_RECENT_MAX)
        self._watermark = 0
        if self._watermark_file is None:
            return
        try:
            with self._watermark_file.open(encoding="utf-8") as stream:
                value = json.load(stream)
        except (OSError, ValueError, json.JSONDecodeError, TypeError):
            return
        tails = value.get("tail") if isinstance(value, dict) else None
        if isinstance(tails, list):
            for item in tails:
                if isinstance(item, int) and not isinstance(item, bool) and item not in self._recent_ids:
                    self._recent_ids.add(item)
                    self._recent_order.append(item)
        maximum = value.get("max_processed") if isinstance(value, dict) else None
        if isinstance(maximum, int) and not isinstance(maximum, bool) and maximum > self._watermark:
            self._watermark = maximum

    def _persist_watermark(self) -> None:
        if self._watermark_file is None:
            return
        payload = json.dumps({"max_processed": self._watermark, "tail": list(self._recent_order),
                              "ts": time.time()})
        try:
            temporary = self._watermark_file.with_suffix(".tmp")
            temporary.write_text(payload)
            temporary.replace(self._watermark_file)
        except OSError as error:
            _log_failure("watermark", error)

    def _note_processed(self, update_id: int) -> None:
        with self._watermark_lock:
            if update_id > self._watermark:
                self._watermark = update_id
            if update_id not in self._recent_ids:
                self._recent_ids.add(update_id)
                self._recent_order.append(update_id)
                while len(self._recent_order) > _RECENT_MAX:
                    old = self._recent_order.popleft()
                    self._recent_ids.discard(old)
            self._persist_watermark()

    def _retry_add(self, update: dict[str, Any]) -> None:
        update_id = update.get("update_id")
        if not isinstance(update_id, int) or isinstance(update_id, bool):
            return
        with self._watermark_lock:
            update_id = int(update_id)
            if update_id in self._recent_ids:
                return
            if any(item.get("update_id") == update_id for item in self._retry):
                return
            self._retry.append(update)
            if len(self._retry) > _RETRY_MAX:
                del self._retry[0]

    def _drain_retry(self) -> list[dict[str, Any]]:
        with self._watermark_lock:
            pending = list(self._retry)
            self._retry.clear()
        return pending

    def _retry_discard(self, update_id: int) -> None:
        with self._watermark_lock:
            self._retry = [item for item in self._retry if item.get("update_id") != update_id]

    def _update_is_known(self, update_id: int) -> bool:
        with self._watermark_lock:
            return update_id in self._recent_ids

    def start(self) -> None:
        if self.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self.run, name="zalo-poller", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def validate(self) -> None:
        self._secret_value()

    def run(self) -> None:
        backoff = float(self._backoff_base)
        last_heartbeat = 0.0
        while not self._stop.is_set():
            try:
                pending = self._drain_retry()
                updates = pending + self._client.get_updates(
                    timeout=self._poll_timeout, offset=self._watermark + 1
                )
                backoff = float(self._backoff_base)
                for update in updates:
                    if self._stop.is_set():
                        break
                    self.process_update(update)
            except Exception as error:
                _log_failure("getUpdates", error)
                self._stop.wait(backoff)
                backoff = min(backoff * 2.0, float(self._backoff_max))
                continue
            now = time.monotonic()
            if self._heartbeat_file is not None and now - last_heartbeat >= self._heartbeat_interval:
                self._write_heartbeat()
                last_heartbeat = now
            self._stop.wait(self._loop_interval)

    def _write_heartbeat(self) -> None:
        try:
            temporary = self._heartbeat_file.with_suffix(".tmp")
            temporary.write_text(json.dumps({"ts": time.time(), "pid": os.getpid()}))
            temporary.replace(self._heartbeat_file)
        except OSError as error:
            _log_failure("heartbeat", error)

    def parse_message_event(self, update: Any) -> tuple[str, str, str] | None:
        if not isinstance(update, dict):
            return None
        message = update.get("message")
        if not isinstance(message, dict):
            return None
        text = message.get("text")
        if not isinstance(text, str) or not text.strip():
            return None
        chat = message.get("chat")
        if not isinstance(chat, dict):
            return None
        if chat.get("chat_type") != "PRIVATE":
            return None
        chat_id = chat.get("id")
        if not isinstance(chat_id, (str, int)) or not str(chat_id).strip():
            return None
        return str(chat_id), text.strip()[:MAX_UPDATE_TEXT], str(update.get("event_name", ""))

    def process_update(self, update: Any) -> str:
        parsed = self.parse_message_event(update)
        if parsed is None:
            return "ignored"
        chat_id, text, _event_name = parsed
        update_id = update.get("update_id") if isinstance(update, dict) else None
        if not isinstance(update_id, int) or isinstance(update_id, bool):
            return self.process_message(chat_id, text, update_key=None)
        update_id = int(update_id)
        if self._update_is_known(update_id):
            return "duplicate"
        status = self.process_message(chat_id, text, update_key=str(update_id))
        if status in _KNOWN_FINAL or not status.startswith("error_"):
            self._note_processed(update_id)
            self._retry_discard(update_id)
        else:
            self._retry_add(update)
        return status

    def process_message(self, chat_id: str, text: str, update_key: str | None = None) -> str:
        text = (text or "").strip()
        if not text:
            return "ignored"
        context = self._conversations.context_for(chat_id)
        status, body = self.forward(chat_id, text, context, update_key)
        if status == 200:
            if not isinstance(body, dict) or not body:
                return "error_no_body"
            if body.get("status") == "already_answered":
                return "duplicate"
            if body.get("status") == "accepted":
                self._conversations.remember_user(chat_id, text)
                self._reply(chat_id, WELCOME_TEXT)
                return "paired"
            self._conversations.remember_user(chat_id, text)
            self._conversations.remember_assistant(chat_id, body.get("question_intent"), body.get("path"))
            return "responded"
        if status == 403:
            code = (body or {}).get("error", {}).get("code")
            if code == "PAIRING_REQUIRED":
                self._conversations.remember_user(chat_id, text)
                self._reply(chat_id, ONBOARDING_NO_BINDING)
                return "onboarded"
            if code == "TARGET_NOT_PAIRED":
                return "ignored_unknown"
            return "blocked"
        if status == 0:
            return "error_forward"
        return f"error_{status}"

    def _reply(self, chat_id: str, text: str) -> None:
        try:
            self._client.send_message(chat_id, text)
        except Exception as error:
            _log_failure("sendMessage", error)

    def forward(self, chat_id: str, text: str, context: dict[str, Any],
                update_key: str | None = None) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {"target_id": chat_id, "text": text, "conversation_context": context}
        if update_key is not None:
            payload["update_key"] = str(update_key)
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._inbound_url,
            data=body,
            headers={"Content-Type": "application/json", "X-Zalo-Bridge-Secret": self._secret_value()},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self._forward_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._request_timeout) as response:
                    raw = response.read(65536)
                parsed = self._parse_body(raw)
                return response.status, parsed
            except urllib.error.HTTPError as error:
                parsed = self._parse_body(error.read(65536))
                return error.code, parsed
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_error = error
                if attempt < self._forward_retries:
                    self._stop.wait(self._backoff_base)
        if last_error is not None:
            _log_failure("inbound forward", last_error)
        return 0, {}

    def _parse_body(self, raw: bytes) -> dict[str, Any]:
        try:
            value = json.loads(raw.decode("utf-8", errors="replace"))
        except (ValueError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _secret_value(self) -> str:
        if self._secret is not None:
            return self._secret
        with self._secret_lock:
            if self._secret is not None:
                return self._secret
            path = Path(self._secret_file)
            if not path.is_file():
                raise RuntimeError("Zalo bridge secret file is unavailable")
            secret = path.read_text(encoding="utf-8").strip()
            if not secret:
                raise RuntimeError("Zalo bridge secret is unavailable")
            self._secret = secret
            return secret