"""Authenticated local HTTP adapter for the accepted TASK-006 tool layer."""
from __future__ import annotations
import hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from msb_tools.registry import invoke_tool

class ToolHandler(BaseHTTPRequestHandler):
    server_version = "MSBCollectionTool/0.1"
    def _send(self, status: int, body: dict) -> None:
        encoded = json.dumps(body, sort_keys=True).encode(); self.send_response(status)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(encoded)))
        self.end_headers(); self.wfile.write(encoded)
    def do_GET(self) -> None:
        self._send(200, {"status": "healthy"}) if self.path == "/health" else self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}})
    def do_POST(self) -> None:
        expected = os.environ.get("COLLECTION_TOOL_API_KEY", ""); supplied = self.headers.get("Authorization", "")
        if not expected or not hmac.compare_digest(supplied, f"Bearer {expected}"):
            self._send(401, {"error": {"code": "UNAUTHORIZED", "message": "Valid bearer authentication required"}}); return
        if self.path != "/tools/get_customer_360":
            self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}}); return
        try: arguments = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}}); return
        result = invoke_tool("get_customer_360", arguments, input_directory=Path(os.environ.get("SYNTHETIC_DATA_DIR", "build/synthetic-data")))
        status = 200 if result["ok"] else 404 if result["error"]["code"] == "NOT_FOUND" else 400
        self._send(status, result)
    def log_message(self, format: str, *args: object) -> None: return

if __name__ == "__main__":
    host = os.environ.get("TOOL_HOST", "127.0.0.1")
    port = int(os.environ.get("TOOL_PORT", "18080"))
    ThreadingHTTPServer((host, port), ToolHandler).serve_forever()
