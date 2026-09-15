"""Unit tests for the official Zalo Bot API client (nothing leaves the process)."""
import io
import json
import unittest.mock

import pytest

from msb_zalo.client import ZaloBotClient, ZaloBotAPIError, MAX_MESSAGE_TEXT

BASE = "https://example.invalid"
TOKEN = "a" * 24


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


def _client(**kwargs):
    kwargs.setdefault("base_url", BASE)
    kwargs.setdefault("token", TOKEN)
    return ZaloBotClient(**kwargs)


def _http_error(status: int, body: bytes, url: str = f"{BASE}/bot{TOKEN}/getMe"):
    return __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
        url, status, "error", {}, io.BytesIO(body)
    )


def test_token_and_url_never_appear_in_errors():
    client = _client()
    with pytest.raises(ZaloBotAPIError) as info:
        client.get_me()
    text = str(info.value)
    assert TOKEN not in text
    assert BASE not in text


def test_missing_file_and_empty_token_are_safe(tmp_path):
    with pytest.raises(RuntimeError) as info:
        ZaloBotClient(token_file=str(tmp_path / "missing"))
    assert TOKEN not in str(info.value)

    empty = tmp_path / "empty"
    empty.write_text("   \n")
    with pytest.raises(RuntimeError) as info:
        ZaloBotClient(token_file=str(empty))
    assert TOKEN not in str(info.value)


def test_get_me_ok():
    body = json.dumps({"ok": True, "result": {"id": "bot-1", "account_name": "MSB Demo"}}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(body)) as mock:
        result = _client().get_me()
    assert result["id"] == "bot-1"
    request = mock.call_args.args[0]
    assert request.full_url == f"{BASE}/bot{TOKEN}/getMe"
    assert json.loads(request.data) == {}


def test_get_updates_result_kinds():
    envelope = json.dumps({"ok": True, "result": {"message": {}}}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)):
        result = _client().get_updates()
    assert isinstance(result, list) and len(result) == 1

    envelope = json.dumps({"ok": True, "result": [{"message": {}}, {"message": {}}]}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)):
        result = _client().get_updates()
    assert len(result) == 2

    envelope = json.dumps({"ok": True, "result": None}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)):
        assert _client().get_updates() == []

    envelope = json.dumps({"ok": True, "result": "nope"}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)):
        with pytest.raises(ZaloBotAPIError):
            _client().get_updates()


def test_get_updates_forwards_timeout_param():
    envelope = json.dumps({"ok": True, "result": None}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)) as mock:
        _client().get_updates(timeout=30)
    request = mock.call_args.args[0]
    assert json.loads(request.data) == {"timeout": "30"}


def test_empty_long_poll_408_means_no_events():
    envelope = json.dumps({"ok": False, "description": "Request timeout", "error_code": 408}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(envelope)):
        assert _client().get_updates(timeout=30) == []


def test_send_message_validates_input():
    client = _client()
    with pytest.raises(ValueError):
        client.send_message("", "hello")
    with pytest.raises(ValueError):
        client.send_message("123", "")
    with pytest.raises(ValueError):
        client.send_message("123", "x" * (MAX_MESSAGE_TEXT + 1))


def test_send_message_payload_and_result():
    body = json.dumps({"ok": True, "result": {"message_id": "m-1", "date": 123}}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(body)) as mock:
        result = _client().send_message("123", "  Hello  ")
    assert result["message_id"] == "m-1"
    request = mock.call_args.args[0]
    assert request.full_url == f"{BASE}/bot{TOKEN}/sendMessage"
    assert json.loads(request.data) == {"chat_id": "123", "text": "Hello"}


def test_ok_false_maps_error_code_and_hides_description():
    body = json.dumps({"ok": False, "error_code": 401,
                       "description": f"secret {TOKEN} at {BASE}"}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(body)):
        with pytest.raises(ZaloBotAPIError) as info:
            _client().send_message("123", "hello")
    assert info.value.code == 401
    assert TOKEN not in str(info.value)
    assert "description" not in str(info.value)


def test_http_error_maps_status_code():
    body = json.dumps({"error_code": 429}).encode("utf-8")
    with unittest.mock.patch("urllib.request.urlopen", side_effect=_http_error(429, body)):
        with pytest.raises(ZaloBotAPIError) as info:
            _client().get_me()
    assert info.value.code == 429
    assert info.value.http_status == 429


def test_unreachable_maps_safe_code():
    with unittest.mock.patch("urllib.request.urlopen", side_effect=__import__(
            "urllib.error", fromlist=["URLError"]).URLError("down")):
        with pytest.raises(ZaloBotAPIError) as info:
            _client().get_me()
    assert info.value.code == "unreachable"
    assert "down" not in str(info.value)


def test_response_size_bounded():
    big = b"x" * 4096
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(big)):
        with pytest.raises(ZaloBotAPIError) as info:
            _client(max_response_bytes=64).get_me()
    assert info.value.code == "response_too_large"


def test_gzip_response_decoded():
    import gzip as gzip_module
    payload = gzip_module.compress(json.dumps({"ok": True, "result": {"id": "1"}}).encode("utf-8"))
    with unittest.mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
        assert _client().get_me()["id"] == "1"