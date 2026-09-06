from __future__ import annotations

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer


class DemoAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tool_server

        cls.old_user = os.environ.get("DEMO_ADMIN_USERNAME")
        cls.old_password = os.environ.get("DEMO_ADMIN_PASSWORD")
        os.environ["DEMO_ADMIN_USERNAME"] = "admin"
        os.environ["DEMO_ADMIN_PASSWORD"] = "admin"
        server = ThreadingHTTPServer(("127.0.0.1", 0), tool_server.ToolHandler)
        cls.server = server
        cls.thread = threading.Thread(target=server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if cls.old_user is None:
            os.environ.pop("DEMO_ADMIN_USERNAME", None)
        else:
            os.environ["DEMO_ADMIN_USERNAME"] = cls.old_user
        if cls.old_password is None:
            os.environ.pop("DEMO_ADMIN_PASSWORD", None)
        else:
            os.environ["DEMO_ADMIN_PASSWORD"] = cls.old_password

    def request(self, method: str, path: str, body: dict | None = None, cookie: str | None = None):
        headers = {"Content-Type": "application/json"}
        if cookie:
            headers["Cookie"] = cookie
        request = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, dict(response.headers), json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), json.load(error)

    def test_invalid_login_is_rejected(self):
        status, _, body = self.request("POST", "/demo/auth/login", {"username": "admin", "password": "wrong"})
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "INVALID_CREDENTIALS")

    def test_login_me_logout_invalidates_session(self):
        status, headers, body = self.request("POST", "/demo/auth/login", {"username": "admin", "password": "admin"})
        self.assertEqual(status, 200)
        self.assertTrue(body["authenticated"])
        set_cookie = headers["Set-Cookie"]
        cookie = set_cookie.split(";", 1)[0]
        status, _, body = self.request("GET", "/demo/auth/me", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertTrue(body["authenticated"])
        status, headers, body = self.request("POST", "/demo/auth/logout", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn("Max-Age=0", headers["Set-Cookie"])
        self.assertFalse(body["authenticated"])
        status, _, body = self.request("GET", "/demo/auth/me", cookie=cookie)
        self.assertEqual(status, 401)
        self.assertFalse(body["authenticated"])

    def test_auth_endpoints_do_not_change_protected_tool_boundary(self):
        status, _, body = self.request("POST", "/tools/get_customer_360", {"cif": "SYN002846"})
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "UNAUTHORIZED")


if __name__ == "__main__":
    unittest.main()
