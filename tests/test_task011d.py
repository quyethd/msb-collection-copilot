from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from unittest.mock import PropertyMock, patch
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from msb_synthetic.generator import generate_to


class Task011DDemoAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tool_server

        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_to(cls.data)
        cls.old_data_dir = os.environ.get("SYNTHETIC_DATA_DIR")
        cls.old_key = os.environ.get("COLLECTION_TOOL_API_KEY")
        os.environ["SYNTHETIC_DATA_DIR"] = str(cls.data)
        os.environ["COLLECTION_TOOL_API_KEY"] = "test-only-placeholder"
        tool_server._repository = None
        tool_server.reset_demo_engine()
        server = ThreadingHTTPServer(("127.0.0.1", 0), tool_server.ToolHandler)
        cls.server = server
        cls.thread = threading.Thread(target=server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{server.server_port}"

    @classmethod
    def tearDownClass(cls):
        import tool_server

        cls.server.shutdown()
        cls.server.server_close()
        tool_server._repository = None
        tool_server.reset_demo_engine()
        if cls.old_data_dir is None:
            os.environ.pop("SYNTHETIC_DATA_DIR", None)
        else:
            os.environ["SYNTHETIC_DATA_DIR"] = cls.old_data_dir
        if cls.old_key is None:
            os.environ.pop("COLLECTION_TOOL_API_KEY", None)
        else:
            os.environ["COLLECTION_TOOL_API_KEY"] = cls.old_key
        cls.temp.cleanup()

    def call(self, path: str, payload: dict | None, auth: str | None = None) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if auth is not None:
            headers["Authorization"] = auth
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers,
            method="POST" if payload is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request) as response:
                self.assertEqual(response.headers.get_content_type(), "application/json")
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            self.assertEqual(error.headers.get_content_type(), "application/json")
            return error.code, json.load(error)

    def test_complete_demo_auth_boundary(self):
        import tool_server
        for method, path in [("GET", "/demo/timeline/SYN002846"), ("POST", "/demo/reset/SYN002846")]:
            self.assertTrue(tool_server.is_browser_safe_demo_route(method, path))
        for method, path in [("GET", "/demo/portfolio"), ("POST", "/demo/unknown"), ("POST", "/tools/get_customer_360"), ("POST", "/agent-tools/get_customer_360"), ("GET", "/demo/timeline/a/b")]:
            self.assertFalse(tool_server.is_browser_safe_demo_route(method, path))
        self.assertEqual(self.call("/demo/timeline/SYN002846", None)[0], 200)
        self.assertEqual(self.call("/demo/portfolio", {})[0], 200)
        self.assertEqual(self.call("/demo/impact", {})[0], 200)
        with patch("tool_server._invoke_copilot", return_value={"status": "success", "summary": "test stub"}) as invoke:
            self.assertEqual(self.call("/demo/copilot", {"cif": "SYN002846", "message": "Explain"})[0], 200)
            invoke.assert_called_once()
        event = {"cif": "SYN002846", "event_type": "CASH_IN_RECEIVED", "occurred_at": "2026-08-28T10:00:00Z", "data": {"amount": 1000}}
        self.assertEqual(self.call("/demo/events", event)[0], 200)
        self.assertEqual(self.call("/demo/reset/SYN002846", {})[0], 200)

    def test_demo_rejects_non_demo_unknown_and_malformed(self):
        for path in ("/demo/customer-360", "/demo/next-best-action", "/demo/simulate", "/demo/events", "/demo/copilot"):
            self.assertEqual(self.call(path, {"cif": "REAL123"})[0], 400)
            self.assertEqual(self.call(path, [])[0], 400)
        self.assertEqual(self.call("/demo/timeline/REAL123", None)[0], 400)
        self.assertEqual(self.call("/demo/reset/REAL123", {})[0], 400)
        self.assertEqual(self.call("/demo/customer-360", {"cif": "SYN999999"})[0], 404)
        self.assertEqual(self.call("/demo/timeline/SYN999999", None)[0], 404)
        import tool_server
        with patch.object(tool_server._get_repository().__class__, "cifs", new_callable=PropertyMock, return_value={"REAL123"}):
            self.assertEqual(self.call("/demo/portfolio", {})[0], 403)
            self.assertEqual(self.call("/demo/impact", {})[0], 403)

    def test_protected_routes_still_require_auth(self):
        for path in ("/tools/get_customer_360", "/tools/get_next_best_action", "/agent-tools/get_customer_360"):
            for auth in (None, "Bearer wrong"):
                self.assertEqual(self.call(path, {"cif": "SYN002846"}, auth)[0], 401)
        for path in ("/tools/get_customer_360", "/tools/get_next_best_action"):
            self.assertEqual(self.call(path, {"cif": "SYN002846"}, "Bearer test-only-placeholder")[0], 200)

    def test_browser_safe_customer_and_nba_adapters(self):
        status, customer = self.call("/demo/customer-360", {"cif": "SYN002846"})
        self.assertEqual(status, 200)
        self.assertEqual(customer["data"]["debt"]["total_outstanding_cif"], 273000000)
        self.assertEqual(customer["data"]["cashflow"]["inflow_7d"], 48000000)

        status, nba = self.call("/demo/next-best-action", {"cif": "SYN002846"})
        self.assertEqual(status, 200)
        self.assertEqual(
            {nba["data"][key] for key in ("final_route", "treatment", "channel")},
            {"CALL", "WAIT_SELF_CURE", "NONE"},
        )

    def test_browser_safe_simulate_adapter(self):
        status, result = self.call(
            "/demo/simulate",
            {"cif": "SYN002846", "changes": {"inflow_7d": 0}},
        )
        self.assertEqual(status, 200)
        self.assertIn("before", result["data"])
        self.assertIn("after", result["data"])

    def test_demo_adapters_validate_synthetic_cif_and_tools_stay_protected(self):
        status, body = self.call("/demo/customer-360", {"cif": "REAL123"})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "INVALID_ARGUMENT")

        for auth in (None, "Bearer wrong"):
            status, body = self.call("/tools/get_customer_360", {"cif": "SYN002846"}, auth)
            self.assertEqual(status, 401)
            self.assertEqual(body["error"]["code"], "UNAUTHORIZED")


if __name__ == "__main__":
    unittest.main()
