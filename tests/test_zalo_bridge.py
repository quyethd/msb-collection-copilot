import unittest
import json
from io import BytesIO
from pathlib import Path

from msb_tools.repository import ToolRepository
from msb_zalo.bridge import ZaloBridge, MAX_ZALO_TEXT


DATA = Path("build/synthetic-data")


class ZaloBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = ToolRepository(DATA)

    def test_preview_is_deterministic_and_safe(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        first, second = bridge.preview(), bridge.preview()
        self.assertEqual(first, second)
        self.assertLessEqual(len(first["text"]), MAX_ZALO_TEXT)
        self.assertEqual(first["portfolio_count"], len(self.repo.portfolio()))
        self.assertEqual(len(first["top_cifs"]), 3)
        self.assertTrue(all(cif.startswith(("SYN", "GOLDEN_G")) for cif in first["top_cifs"]))

    def test_phone_is_label_not_delivery_target(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        state = bridge.configure({"demo_label": "Judge", "display_phone": "0900000000"})
        self.assertFalse(state["paired"])
        with self.assertRaises(PermissionError): bridge.send_morning_brief()

    def test_pairing_and_one_send(self):
        sent = []
        bridge = ZaloBridge(self.repo, lambda target, text: sent.append((target, text)) or {"accepted": True})
        bridge.configure({"demo_label": "Judge", "display_name": "Demo", "display_phone": "synthetic"})
        with self.assertRaises(PermissionError): bridge.pair_from_inbound("target-1", "hello")
        bridge.pair_from_inbound("target-1", "MSB DEMO")
        result = bridge.send_morning_brief()
        self.assertEqual(result["status"], "sent")
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], "target-1")

    def test_unknown_target_is_isolated_and_no_secret_boundary(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({"display_phone": "target-1"})
        self.assertIsNone(bridge.status().get("target_id"))
        self.assertNotIn("target_id", bridge.status())
        self.assertNotIn("token", bridge.status())

    def test_duplicate_pending_send_is_blocked(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        def sender(*_):
            entered.set(); release.wait(2); return {"accepted": True}
        bridge = ZaloBridge(self.repo, sender)
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        thread = threading.Thread(target=bridge.send_morning_brief)
        thread.start(); self.assertTrue(entered.wait(10))
        with self.assertRaises(RuntimeError): bridge.send_morning_brief()
        release.set(); thread.join(20)

    def test_approved_inbound_uses_existing_copilot_and_unknown_is_blocked(self):
        sent = []
        bridge = ZaloBridge(self.repo, lambda target, text: sent.append((target, text)) or {"accepted": True})
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        result = bridge.handle_inbound("target-1", "Tại sao SYN002846 hôm nay chưa cần gọi?")
        self.assertEqual(result["status"], "responded")
        self.assertEqual(result["question_intent"], "DECISION_EXPLANATION")
        self.assertIn(result["path"], {"LOCAL", "FALLBACK"})
        self.assertEqual(len(sent), 1)
        with self.assertRaises(PermissionError): bridge.handle_inbound("unknown", "Tóm tắt danh mục")

    def test_inbound_requires_json_object(self):
        import tool_server
        class FakeHandler:
            def __init__(self, payload):
                self.rfile = BytesIO(json.dumps(payload).encode())
                self.headers = {"Content-Length": str(len(self.rfile.getvalue()))}
                self.responses = []
            def _send(self, status, body): self.responses.append((status, body))
        for payload in (["target-1", "MSB DEMO"], "MSB DEMO", 7, None):
            handler = FakeHandler(payload)
            self.assertIsNone(tool_server._read_json_object(handler))
            self.assertEqual(handler.responses, [(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}})])

    def test_inbound_runtime_error_has_safe_public_message(self):
        bridge = ZaloBridge(self.repo, lambda *_: (_ for _ in ()).throw(RuntimeError("internal-token-or-url")))
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        with self.assertRaises(RuntimeError) as raised:
            bridge.handle_inbound("target-1", "Tóm tắt danh mục")
        self.assertEqual(str(raised.exception), "internal-token-or-url")

    def test_inbound_http_runtime_error_is_safe(self):
        import os
        from unittest.mock import patch
        import tool_server

        class FakeHandler:
            path = "/demo/zalo/inbound"

            def __init__(self, payload):
                raw = json.dumps(payload).encode()
                self.rfile = BytesIO(raw)
                self.headers = {"Content-Length": str(len(raw)), "X-Zalo-Bridge-Secret": "shared"}
                self.responses = []

            def _send(self, status, body):
                self.responses.append((status, body))

        bridge = ZaloBridge(self.repo, lambda *_: (_ for _ in ()).throw(RuntimeError("internal-token-or-url")))
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        handler = FakeHandler({"target_id": "target-1", "text": "Tóm tắt danh mục"})
        with patch.dict(os.environ, {"ZALO_INBOUND_SHARED_SECRET": "shared"}), patch.object(
            tool_server, "_get_zalo_bridge", return_value=bridge
        ):
            tool_server.ToolHandler.do_POST(handler)
        self.assertEqual(handler.responses[0][0], 503)
        self.assertEqual(handler.responses[0][1], {"error": {"code": "ZALO_BRIDGE_UNAVAILABLE", "message": "Zalo bridge is temporarily unavailable"}})
        self.assertNotIn("internal-token-or-url", json.dumps(handler.responses[0][1]))

    def test_inbound_http_unknown_target_is_safe(self):
        import os
        from unittest.mock import patch
        import tool_server

        class FakeHandler:
            path = "/demo/zalo/inbound"

            def __init__(self, payload):
                raw = json.dumps(payload).encode()
                self.rfile = BytesIO(raw)
                self.headers = {"Content-Length": str(len(raw)), "X-Zalo-Bridge-Secret": "shared"}
                self.responses = []

            def _send(self, status, body):
                self.responses.append((status, body))

        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        handler = FakeHandler({"target_id": "unknown", "text": "Tóm tắt danh mục"})
        with patch.dict(os.environ, {"ZALO_INBOUND_SHARED_SECRET": "shared"}), patch.object(
            tool_server, "_get_zalo_bridge", return_value=bridge
        ):
            tool_server.ToolHandler.do_POST(handler)
        self.assertEqual(handler.responses, [(403, {"error": {"code": "TARGET_NOT_PAIRED", "message": "Unknown Zalo target"}})])

    def test_no_binding_without_operator_created_recipient(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        with self.assertRaises(PermissionError): bridge.pair_from_inbound("target-1", "MSB DEMO")
        self.assertFalse(bridge.status()["configured"])

    def test_pairing_phrase_is_case_and_whitespace_insensitive(self):
        sent = []
        bridge = ZaloBridge(self.repo, lambda target, text: sent.append((target, text)) or {"accepted": True})
        bridge.configure({})
        bridge.pair_from_inbound("target-1", "  msb demo  ")
        self.assertTrue(bridge.status()["paired"])
        self.assertEqual(bridge.status()["connection_status"], "Đã kết nối Zalo")
        bridge.send_morning_brief()
        self.assertEqual(len(sent), 1)

    def test_reset_recipient_clears_and_blocks_again(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({})
        bridge.pair_from_inbound("target-1", "MSB DEMO")
        self.assertTrue(bridge.status()["paired"])
        state = bridge.reset_recipient()
        self.assertFalse(state["configured"] or state["paired"])
        with self.assertRaises(PermissionError): bridge.pair_from_inbound("target-1", "MSB DEMO")
        with self.assertRaises(PermissionError): bridge.send_morning_brief()

    def test_status_exposes_provider_without_target(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({"demo_label": "Judge"})
        state = bridge.status()
        self.assertEqual(state["provider"], "official-zalo-bot-api")
        self.assertEqual(state["dm_policy_open"], "NO")
        self.assertTrue(state["synthetic_data"])
        self.assertNotIn("target_id", state)
        self.assertNotIn("token", state)

    def test_reconfigure_clears_previous_target(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({})
        bridge.pair_from_inbound("target-old", "MSB DEMO")
        bridge.configure({"demo_label": "New"})
        self.assertFalse(bridge.status()["paired"])
        with self.assertRaises(PermissionError): bridge.send_morning_brief()

    def test_reused_update_key_dedups_responded_reply(self):
        sent = []
        bridge = ZaloBridge(self.repo, lambda target, text: sent.append((target, text)) or {"accepted": True})
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        first = bridge.handle_inbound("target-1", "Tại sao hôm nay chưa cần gọi?", update_key="1001")
        self.assertEqual(first["status"], "responded")
        self.assertEqual(len(sent), 1)
        second = bridge.handle_inbound("target-1", "Tại sao hôm nay chưa cần gọi?", update_key="1001")
        self.assertEqual(second["status"], "already_answered")
        self.assertTrue(second["deduplicated"])
        self.assertEqual(second["original_status"], "responded")
        self.assertEqual(second["question_intent"], first["question_intent"])
        self.assertEqual(len(sent), 1, "no second user-visible send for the same update")

    def test_reused_update_key_dedups_pairing(self):
        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({})
        bridge.pair_from_inbound("target-1", "MSB DEMO", update_key="77")
        cached = bridge.lookup("77")
        self.assertEqual(cached["status"], "already_answered")
        self.assertTrue(cached["deduplicated"])
        self.assertEqual(cached["original_status"], "accepted")
        self.assertTrue(bridge.status()["paired"])

    def test_distinct_update_keys_both_answered(self):
        sent = []
        bridge = ZaloBridge(self.repo, lambda target, text: sent.append((target, text)) or {"accepted": True})
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        bridge.handle_inbound("target-1", "Tại sao hôm nay chưa cần gọi?", update_key="2001")
        bridge.handle_inbound("target-1", "Điểm cơ hội thu hồi là bao nhiêu?", update_key="2002")
        self.assertEqual(len(sent), 2)

    def test_inbound_dedup_short_circuits_before_pairing(self):
        import os
        from unittest.mock import patch
        import tool_server

        class FakeHandler:
            path = "/demo/zalo/inbound"

            def __init__(self, payload):
                raw = json.dumps(payload).encode()
                self.rfile = BytesIO(raw)
                self.headers = {"Content-Length": str(len(raw)), "X-Zalo-Bridge-Secret": "shared"}
                self.responses = []

            def _send(self, status, body):
                self.responses.append((status, body))

        bridge = ZaloBridge(self.repo, lambda *_: {"accepted": True})
        bridge.configure({}); bridge.pair_from_inbound("target-1", "MSB DEMO")
        body = {"target_id": "target-1", "text": "Tóm tắt danh mục", "update_key": "555"}
        bridge.record_answer("555", {"status": "responded", "question_intent": "CUSTOMER_SUMMARY"})
        handler = FakeHandler(body)
        with patch.dict(os.environ, {"ZALO_INBOUND_SHARED_SECRET": "shared"}), patch.object(
            tool_server, "_get_zalo_bridge", return_value=bridge
        ):
            tool_server.ToolHandler.do_POST(handler)
        self.assertEqual(handler.responses[0][0], 200)
        self.assertEqual(handler.responses[0][1]["status"], "already_answered")
        self.assertTrue(handler.responses[0][1]["deduplicated"])

    def test_get_zalo_bridge_does_not_deadlock_and_is_singleton(self):
        import threading
        import tool_server
        tool_server._zalo_bridge = None
        tool_server._repository = None
        results = []
        def probe():
            try:
                results.append(("status", tool_server._get_zalo_bridge()))
            except Exception as error:  # noqa: BLE001
                results.append(("error", type(error).__name__))
        threads = [threading.Thread(target=probe) for _ in range(4)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=20)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(kind == "status" for kind, _ in results), results)
        bridges = [bridge for _, bridge in results]
        self.assertTrue(all(bridge is bridges[0] for bridge in bridges), "bridge must be a singleton")
        self.assertEqual(bridges[0].status()["provider"], "official-zalo-bot-api")
        tool_server._zalo_bridge = None
        tool_server._repository = None


if __name__ == "__main__": unittest.main()
