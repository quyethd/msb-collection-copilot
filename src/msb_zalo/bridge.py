from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable

from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository
from msb_zalo.chat import MAX_ZALO_TEXT, ZaloConversation, build_morning_brief
from msb_zalo.client import ZaloBotClient
PAIRING_PHRASE = "MSB DEMO"
_zalo_sender_client: ZaloBotClient | None = None
_ANSWERED_MAX = 512


def _official_sender(target_id: str, text: str) -> dict[str, Any]:
    """Send through the official Zalo Bot API (sendMessage)."""
    global _zalo_sender_client
    if _zalo_sender_client is None:
        _zalo_sender_client = ZaloBotClient()
    return _zalo_sender_client.send_message(target_id, text)


@dataclass
class Recipient:
    demo_label: str = ""
    display_name: str = ""
    display_phone: str = ""
    target_id: str | None = None
    status: str = "Chưa kết nối"
    last_send_state: str | None = None


class ZaloBridge:
    """Small protected bridge. Target IDs only come from approved inbound pairing."""

    def __init__(self, repository: ToolRepository, sender: Callable[[str, str], dict[str, Any]] | None = None):
        self.repository = repository
        self._sender = sender or self._configured_sender
        self._recipient = Recipient()
        self._configured = False
        self._lock = threading.Lock()
        self._send_pending = False
        self.conversation = ZaloConversation(repository)
        self._answered: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def record_answer(self, update_key: str, body: dict[str, Any]) -> None:
        with self._lock:
            self._answered[str(update_key)] = dict(body)
            while len(self._answered) > _ANSWERED_MAX:
                self._answered.popitem(last=False)

    def lookup(self, update_key: str) -> dict[str, Any] | None:
        with self._lock:
            cached = self._answered.get(str(update_key))
        if cached is None:
            return None
        result = dict(cached)
        result["original_status"] = result.get("status")
        result["status"] = "already_answered"
        result["deduplicated"] = True
        return result

    def configure(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._recipient.demo_label = str(body.get("demo_label", "Người nhận demo"))[:80]
            self._recipient.display_name = str(body.get("display_name", "Người nhận demo Zalo"))[:120]
            self._recipient.display_phone = str(body.get("display_phone", ""))[:40]
            self._recipient.target_id = None
            self._recipient.status = "Đang chờ ghép nối"
            self._recipient.last_send_state = None
            self._configured = True
            self.conversation.reset()
            return self.status()

    def reset_recipient(self) -> dict[str, Any]:
        with self._lock:
            self._recipient = Recipient()
            self._configured = False
            self.conversation.reset()
            return self.status()

    def status(self) -> dict[str, Any]:
        recipient = self._recipient
        return {"demo_label": recipient.demo_label, "display_name": recipient.display_name,
                "display_phone": recipient.display_phone, "connection_status": recipient.status,
                "configured": self._configured, "paired": bool(recipient.target_id),
                "last_send_state": recipient.last_send_state, "provider": "official-zalo-bot-api",
                "dm_policy_open": "NO", "synthetic_data": True}

    def pair_from_inbound(self, target_id: str, text: str, update_key: str | None = None) -> dict[str, Any]:
        if not isinstance(target_id, str) or not target_id.strip() or not isinstance(text, str):
            raise ValueError("Approved Zalo target ID and text are required")
        if text.strip().upper() != PAIRING_PHRASE:
            raise PermissionError("Pairing phrase required")
        with self._lock:
            if self._recipient.status not in ("Đang chờ ghép nối", "Đã kết nối Zalo"):
                raise PermissionError("Operator-created pending recipient is required")
            self._recipient.target_id = target_id.strip()[:200]
            self._recipient.status = "Đã kết nối Zalo"
            result = {"status": "accepted", "connection_status": self._recipient.status}
        if update_key is not None:
            with self._lock:
                self._answered[str(update_key)] = dict(result)
        return self.status()

    def handle_inbound(self, target_id: str, text: str, conversation_context: dict[str, Any] | None = None,
                       update_key: str | None = None) -> dict[str, Any]:
        """Handle an approved target's message through the existing Copilot."""
        if not isinstance(target_id, str) or not isinstance(text, str):
            raise ValueError("Approved Zalo target ID and text are required")
        if update_key is not None:
            key = str(update_key)
            cached = self.lookup(key)
            if cached is not None:
                return cached
        with self._lock:
            if not self._recipient.target_id or target_id.strip() != self._recipient.target_id:
                raise PermissionError("Unknown Zalo target")
        if text.strip().upper() == PAIRING_PHRASE:
            return self.status()
        answer = self.conversation.respond(
            text, conversation_context if isinstance(conversation_context, dict) else {}
        )
        transport = self._sender(target_id, answer["text"])
        result = {"status": "responded", "message_length": len(answer["text"]),
                  "question_intent": answer["question_intent"],
                  "intent": answer["intent"], "answer_kind": answer["answer_kind"],
                  "path": answer["path"], "transport": transport, "synthetic_data": True}
        if update_key is not None:
            self.record_answer(str(update_key), result)
        return result

    def preview(self) -> dict[str, Any]:
        return build_morning_brief(self.repository)

    def send_morning_brief(self) -> dict[str, Any]:
        with self._lock:
            if not self._recipient.target_id:
                raise PermissionError("Approved Zalo target is required before sending")
            if self._send_pending:
                raise RuntimeError("A Zalo send is already pending")
            self._send_pending = True
            target_id = self._recipient.target_id
        try:
            brief = build_morning_brief(self.repository)
            result = self._sender(target_id, brief["text"])
            with self._lock:
                self._recipient.last_send_state = "Đã gửi"
            return {"status": "sent", "message_length": len(brief["text"]),
                    "brief": brief, "transport": result, "synthetic_data": True}
        except Exception:
            with self._lock:
                self._recipient.last_send_state = "Lỗi gửi"
            raise
        finally:
            with self._lock:
                self._send_pending = False

    @staticmethod
    def _configured_sender(target_id: str, text: str) -> dict[str, Any]:
        """Send only through the official Zalo Bot API (sendMessage)."""
        return _official_sender(target_id, text)
