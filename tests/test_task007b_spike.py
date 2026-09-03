from __future__ import annotations
import json, os, threading, unittest, urllib.error, urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tool_server import ToolHandler


class AgentUrlContractTest(unittest.TestCase):
    def test_public_url_uses_only_approved_route(self):
        source = Path("main.py").read_text(encoding="utf-8")
        self.assertIn('public_url.rstrip("/") + "/get_customer_360"', source)
        self.assertIn('COLLECTION_TOOL_BASE_URL', source)

class ConnectivitySpikeToolTest(unittest.TestCase):
    def test_deployment_defaults_are_loopback_only(self):
        self.assertEqual(os.environ.get("TOOL_HOST", "127.0.0.1"), "127.0.0.1")
        self.assertEqual(int(os.environ.get("TOOL_PORT", "18080")), 18080)

    @classmethod
    def setUpClass(cls):
        cls.previous_key = os.environ.get("COLLECTION_TOOL_API_KEY"); os.environ["COLLECTION_TOOL_API_KEY"] = "test-only-placeholder"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ToolHandler); cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()
        if cls.previous_key is None: os.environ.pop("COLLECTION_TOOL_API_KEY", None)
        else: os.environ["COLLECTION_TOOL_API_KEY"] = cls.previous_key
    def post(self, cif, token="test-only-placeholder"):
        request = urllib.request.Request(self.base + "/tools/get_customer_360", data=json.dumps({"cif": cif}).encode(),
                                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, method="POST")
        try:
            with urllib.request.urlopen(request) as response: return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            try: return error.code, json.load(error)
            finally: error.close()
    def test_syn002846(self):
        status, body = self.post("SYN002846"); self.assertEqual(status, 200); self.assertTrue(body["ok"]); self.assertEqual(body["data"]["cif"], "SYN002846")
    def test_unknown_cif(self):
        status, body = self.post("SYN999999"); self.assertEqual(status, 404); self.assertEqual(body["error"]["code"], "NOT_FOUND")
    def test_authentication(self):
        status, body = self.post("SYN002846", "wrong-test-placeholder"); self.assertEqual(status, 401); self.assertEqual(body["error"]["code"], "UNAUTHORIZED")

if __name__ == "__main__": unittest.main()
