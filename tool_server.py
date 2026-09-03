"""Authenticated local HTTP adapter for the accepted TASK-006 tool layer + TASK-008B demo routes."""
from __future__ import annotations
import hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from msb_tools.registry import invoke_tool
from msb_tools.validate import PUBLIC_TOOL_ALLOWLIST
from msb_demo.engine import DemoEventEngine
from msb_demo.models import DemoEvent
from msb_tools.errors import ToolFailure
from msb_tools.repository import ToolRepository

_demo_engine: DemoEventEngine | None = None


def _get_demo_engine() -> DemoEventEngine:
    global _demo_engine
    if _demo_engine is None:
        repo = ToolRepository(Path(os.environ.get("SYNTHETIC_DATA_DIR", "build/synthetic-data")))
        _demo_engine = DemoEventEngine(repo)
    return _demo_engine


class ToolHandler(BaseHTTPRequestHandler):
    server_version = "MSBCollectionTool/0.4"

    def _send(self, status: int, body: dict) -> None:
        encoded = json.dumps(body, sort_keys=True).encode(); self.send_response(status)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(encoded)))
        self.end_headers(); self.wfile.write(encoded)

    def _authed(self) -> bool:
        expected = os.environ.get("COLLECTION_TOOL_API_KEY", ""); supplied = self.headers.get("Authorization", "")
        return bool(expected) and hmac.compare_digest(supplied, f"Bearer {expected}")

    def _require_auth(self) -> bool:
        if not self._authed():
            self._send(401, {"error": {"code": "UNAUTHORIZED", "message": "Valid bearer authentication required"}})
            return False
        return True

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "healthy"}); return
        if self.path.startswith("/demo/timeline/"):
            if not self._require_auth(): return
            cif = self.path[len("/demo/timeline/"):]
            try:
                entries = _get_demo_engine().get_timeline(cif)
                self._send(200, {"status": "success", "cif": cif, "timeline": entries, "demo_only": True})
            except ToolFailure as error:
                status = 404 if error.code == "NOT_FOUND" else 400
                self._send(status, {"error": {"code": error.code, "message": error.message}})
            return
        self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}})

    def do_POST(self) -> None:
        if not self._require_auth(): return
        try: body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}}); return
        if self.path == "/demo/events":
            self._handle_demo_event(body); return
        if self.path.startswith("/demo/reset/"):
            cif = self.path[len("/demo/reset/"):]
            try:
                result = _get_demo_engine().reset(cif)
                self._send(200, result)
            except ToolFailure as error:
                status = 404 if error.code == "NOT_FOUND" else 400
                self._send(status, {"error": {"code": error.code, "message": error.message}})
            return
        if not self.path.startswith("/tools/"):
            self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}}); return
        tool_name = self.path[len("/tools/"):]
        if tool_name not in PUBLIC_TOOL_ALLOWLIST:
            self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}}); return
        result = invoke_tool(tool_name, body, input_directory=Path(os.environ.get("SYNTHETIC_DATA_DIR", "build/synthetic-data")))
        status = 200 if result["ok"] else 404 if result["error"]["code"] == "NOT_FOUND" else 400
        self._send(status, result)

    def _handle_demo_event(self, body: dict) -> None:
        try:
            event = DemoEvent(
                event_type=body.get("event_type", ""),
                cif=body.get("cif", ""),
                occurred_at=body.get("occurred_at", ""),
                data=body.get("data", {}),
                event_id=body.get("event_id"),
            )
            result = _get_demo_engine().process_event(event)
            self._send(200, result)
        except ToolFailure as error:
            status = 404 if error.code == "NOT_FOUND" else 400
            self._send(status, {"error": {"code": error.code, "message": error.message}})
        except Exception:
            self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "Invalid demo event request"}})

    def log_message(self, format: str, *args: object) -> None: return


def reset_demo_engine() -> None:
    global _demo_engine
    _demo_engine = None


if __name__ == "__main__":
    host = os.environ.get("TOOL_HOST", "127.0.0.1")
    port = int(os.environ.get("TOOL_PORT", "18080"))
    ThreadingHTTPServer((host, port), ToolHandler).serve_forever()
