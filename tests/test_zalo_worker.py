"""Unit tests for the Zalo long-polling worker (loopback only, nothing leaves the process)."""
import json
import time
import unittest.mock

import pytest
import urllib.error

from msb_zalo.client import MAX_MESSAGE_TEXT
from msb_zalo.worker import ChatMemory, ZaloPollingWorker, WELCOME_TEXT, ONBOARDING_NO_BINDING

BASE = "https://example.invalid"
TOKEN = "b" * 24


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1):
        return self._body if size < 0 else self._body[:size]


class FakeClient:
    def __init__(self):
        self.updates = []
        self.sent = []
        self.get_updates_calls = 0
        self.last_offset = None

    def get_updates(self, timeout=None, offset=None):
        self.get_updates_calls += 1
        self.last_offset = offset
        pending = self.updates
        self.updates = []
        return pending

    def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))
        return {"message_id": f"m-{len(self.sent)}"}


def _secret_file(tmp_path):
    path = tmp_path / "secret"
    path.write_text("shared-secret-value\n")
    return str(path)


def _worker(tmp_path, client=None, **kwargs):
    kwargs.setdefault("inbound_url", f"{BASE}/demo/zalo/inbound")
    kwargs.setdefault("secret_file", _secret_file(tmp_path))
    kwargs.setdefault("backoff_base", 0.01)
    kwargs.setdefault("poll_timeout", 1)
    kwargs.setdefault("loop_interval", 0.01)
    return ZaloPollingWorker(client or FakeClient(), **kwargs)


def _private(text, chat_id="u-1", chat_type="PRIVATE", update_id=None, **extra):
    event = {"message": {"from": {"id": chat_id, "is_bot": False},
                         "chat": {"id": chat_id, "chat_type": chat_type},
                         "text": text}, "event_name": "message.text.received"}
    if update_id is not None:
        event["update_id"] = update_id
    event.update(extra)
    return event


def test_private_text_event_parsed(tmp_path):
    worker = _worker(tmp_path)
    parsed = worker.parse_message_event(_private("MSB DEMO"))
    assert parsed == ("u-1", "MSB DEMO", "message.text.received")


def test_non_private_traffic_ignored(tmp_path):
    worker = _worker(tmp_path)
    assert worker.parse_message_event(_private("hi", chat_type="GROUP")) is None
    assert worker.parse_message_event(_private("hi", chat_type="IM")) is None
    assert worker.parse_message_event(_private("hi", chat_type="SD")) is None


def test_malformed_and_non_text_ignored(tmp_path):
    worker = _worker(tmp_path)
    assert worker.parse_message_event(None) is None
    assert worker.parse_message_event("nope") is None
    assert worker.parse_message_event({}) is None
    assert worker.parse_message_event({"message": {"chat": {}, "text": "hi"}}) is None
    assert worker.parse_message_event({"message": {"chat": {"id": "u", "chat_type": "PRIVATE"}}}) is None
    image = {"message": {"from": {"id": "u"}, "chat": {"id": "u", "chat_type": "PRIVATE"},
                         "photo": {"payload": []}}}
    assert worker.parse_message_event(image) is None
    event = _private("hi")
    event["message"]["chat"] = {"chat_type": "PRIVATE"}
    assert worker.parse_message_event(event) is None


def test_integer_chat_id_normalized(tmp_path):
    worker = _worker(tmp_path)
    parsed = worker.parse_message_event(_private("hi", chat_id=42))
    assert parsed == ("42", "hi", "message.text.received")


def test_group_update_rejected_by_process_update(tmp_path):
    worker = _worker(tmp_path)
    assert worker.process_update(_private("MSB DEMO", chat_type="GROUP")) == "ignored"


def test_pairing_binds_and_welcomes(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (200, {"status": "accepted"})
    status = worker.process_message("u-1", "  msb demo  ")
    assert status == "paired"
    assert worker._client.sent == [("u-1", WELCOME_TEXT)]
    assert worker._conversations.context_for("u-1")["previous_user_question"] == "msb demo"


def test_responded_remembers_bounded_context(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (
        200, {"status": "responded", "question_intent": "DECISION_EXPLANATION", "path": "LOCAL"})
    assert worker.process_message("u-1", "Vì sao số tiền này?") == "responded"
    assert worker.process_message("u-1", "Và thời hạn?") == "responded"
    assert worker._client.sent == []
    context = worker._conversations.context_for("u-1")
    assert context["active_cif"] == "SYN002846"
    assert context["previous_intent"] == "DECISION_EXPLANATION"
    assert context["previous_path"] == "LOCAL"
    assert context["previous_user_question"] == "Và thời hạn?"


def test_no_recipient_onboarding(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (403, {"error": {"code": "PAIRING_REQUIRED"}})
    status = worker.process_message("u-9", "MSB DEMO")
    assert status == "onboarded"
    assert worker._client.sent == [("u-9", ONBOARDING_NO_BINDING)]


def test_unknown_target_ignored_without_reply(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (403, {"error": {"code": "TARGET_NOT_PAIRED"}})
    assert worker.process_message("u-2", "hello") == "ignored_unknown"
    assert worker._client.sent == []


def test_blocked_and_forward_failure(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (403, {"error": {"code": "OTHER"}})
    assert worker.process_message("u-2", "hello") == "blocked"
    worker.forward = lambda chat, text, context, update_key=None: (0, {})
    assert worker.process_message("u-2", "hello") == "error_forward"


def test_bounded_chat_memory(tmp_path):
    memory = ChatMemory()
    chat_id = "u-3"
    for index in range(15):
        memory.remember_user(chat_id, f"message {index}")
    assert len(memory._chats[chat_id]) == ChatMemory.MAX_TURNS
    context = memory.context_for(chat_id)
    assert context["previous_user_question"] == "message 14"
    for index in range(ChatMemory.MAX_CHATS):
        memory.remember_user(f"other-{index}", "x")
    assert len(memory._chats) == ChatMemory.MAX_CHATS


def test_forward_retries_then_succeeds(tmp_path):
    worker = _worker(tmp_path, forward_retries=2)
    attempts = []

    def _flake(request, timeout=None):
        attempts.append(1)
        if len(attempts) < 3:
            raise urllib.error.URLError("down")
        return FakeResponse(json.dumps({"status": "accepted"}).encode("utf-8"), 200)

    with unittest.mock.patch("urllib.request.urlopen", side_effect=_flake):
        status, body = worker.forward("u-1", "MSB DEMO", {})
    assert len(attempts) == 3
    assert status == 200
    assert body.get("status") == "accepted"


def test_forward_gives_up_after_retries(tmp_path):
    worker = _worker(tmp_path, forward_retries=2)
    with unittest.mock.patch("urllib.request.urlopen",
                             side_effect=urllib.error.URLError("down")):
        status, body = worker.forward("u-1", "MSB DEMO", {})
    assert (status, body) == (0, {})


def test_forward_sends_shared_secret_header(tmp_path):
    worker = _worker(tmp_path)
    captured = {}

    def _capture(request, timeout=None):
        values = [value for key, value in request.header_items()
                  if key.lower() == "x-zalo-bridge-secret"]
        captured["secret"] = values[0] if values else None
        captured["payload"] = json.loads(request.data)
        raise urllib.error.URLError("down")

    with unittest.mock.patch("urllib.request.urlopen", side_effect=_capture):
        worker.forward("u-1", "MSB DEMO", {"active_cif": "SYN002846"})
    assert captured["secret"] == "shared-secret-value"
    assert captured["payload"]["target_id"] == "u-1"
    assert captured["payload"]["text"] == "MSB DEMO"
    assert captured["payload"]["conversation_context"]["active_cif"] == "SYN002846"


def test_forward_includes_update_key(tmp_path):
    worker = _worker(tmp_path)
    captured = {}

    def _capture(request, timeout=None):
        captured["payload"] = json.loads(request.data)
        raise urllib.error.URLError("down")

    with unittest.mock.patch("urllib.request.urlopen", side_effect=_capture):
        worker.forward("u-1", "MSB DEMO", {"active_cif": "SYN002846"}, update_key="42")
    assert captured["payload"]["update_key"] == "42"


def test_same_update_returned_three_times_processes_once(tmp_path):
    watermark = tmp_path / "watermark.json"
    client = FakeClient()
    worker = _worker(tmp_path, client=client, watermark_file=str(watermark))
    states = []
    worker.forward = lambda chat, text, context, update_key=None: (
        states.append(update_key) or (200, {"status": "accepted"}))
    update = _private("MSB DEMO", update_id=7)
    assert worker.process_update(update) == "paired"
    assert worker.process_update(update) == "duplicate"
    assert worker.process_update(update) == "duplicate"
    assert len(states) == 1
    assert states == ["7"]
    assert worker._client.sent == [("u-1", WELCOME_TEXT)]
    assert worker._watermark == 7


def test_timeout_after_bridge_processing_does_not_reply_twice(tmp_path):
    watermark = tmp_path / "watermark.json"
    worker = _worker(tmp_path, watermark_file=str(watermark))
    calls = {"count": 0}

    def _flaky(chat, text, context, update_key=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return 0, {}
        return 200, {"status": "already_answered", "deduplicated": True, "original_status": "responded"}

    worker.forward = _flaky
    update = _private("Hỏi gì đó", update_id=10)
    assert worker.process_update(update) == "error_forward"
    assert worker._watermark == 0
    assert len(worker._retry) == 1
    assert worker.process_update(update) == "duplicate"
    assert calls["count"] == 2
    assert worker._client.sent == []
    assert worker._watermark == 10


def test_restart_does_not_replay_answered_updates(tmp_path):
    watermark = tmp_path / "watermark.json"
    first = _worker(tmp_path, watermark_file=str(watermark))
    first.forward = lambda chat, text, context, update_key=None: (
        200, {"status": "responded", "question_intent": "DECISION_EXPLANATION", "path": "LOCAL"})
    update = _private("Tại sao chưa cần gọi?", update_id=15)
    assert first.process_update(update) == "responded"
    assert first._watermark == 15
    assert watermark.is_file()

    second = _worker(tmp_path, watermark_file=str(watermark))
    assert second._watermark == 15
    assert second.process_update(update) == "duplicate"
    second.forward = lambda chat, text, context, update_key=None: (
        (200, {"status": "responded", "question_intent": "DECISION_EXPLANATION", "path": "LOCAL"}))
    assert second.process_update(_private("Câu hỏi mới sau restart", update_id=16)) == "responded"


def test_two_distinct_updates_with_same_text_both_processed(tmp_path):
    worker = _worker(tmp_path)
    handled = []
    worker.forward = lambda chat, text, context, update_key=None: (
        handled.append((chat, text, update_key)) or
        (200, {"status": "responded", "question_intent": "KNOWLEDGE", "path": "RAG_QWEN"}))
    first = _private("Hôm nay xem khách nào?", update_id=20)
    second = _private("Hôm nay xem khách nào?", update_id=21)
    assert worker.process_update(first) == "responded"
    assert worker.process_update(second) == "responded"
    assert len(handled) == 2
    assert [item[2] for item in handled] == ["20", "21"]


def test_already_answered_body_returns_duplicate(tmp_path):
    worker = _worker(tmp_path)
    worker.forward = lambda chat, text, context, update_key=None: (
        200, {"status": "already_answered", "deduplicated": True})
    assert worker.process_message("u-1", "Điểm là bao nhiêu?", update_key="99") == "duplicate"
    assert worker._client.sent == []


def test_run_loop_polls_with_offset_and_replies(tmp_path):
    client = FakeClient()
    worker = _worker(tmp_path, client=client)
    worker.forward = lambda chat, text, context, update_key=None: (200, {"status": "accepted"})
    client.updates = [_private("MSB DEMO", update_id=5)]
    worker.start()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and client.get_updates_calls < 2:
        time.sleep(0.02)
    worker.stop()
    assert not worker.is_alive()
    assert client.sent == [("u-1", WELCOME_TEXT)]
    assert client.last_offset == 6


def test_heartbeat_written(tmp_path):
    beats = tmp_path / "heartbeat"
    worker = _worker(tmp_path)
    worker._heartbeat_file = beats
    worker._write_heartbeat()
    data = json.loads(beats.read_text())
    assert "ts" in data and "pid" in data


def test_welcome_text_within_zalo_limit():
    assert len(WELCOME_TEXT) <= MAX_MESSAGE_TEXT
    assert len(ONBOARDING_NO_BINDING) <= MAX_MESSAGE_TEXT