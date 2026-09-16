"""Authenticated local HTTP adapter for the accepted TASK-006 tool layer + TASK-008B demo routes."""
from __future__ import annotations
import hmac, json, logging, os, re, secrets, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from msb_tools.registry import invoke_tool
from msb_tools.validate import PUBLIC_TOOL_ALLOWLIST
from msb_demo.engine import DemoEventEngine
from msb_demo.models import DemoEvent
from msb_tools.errors import ToolFailure
from msb_tools.repository import ToolRepository
from msb_agent.copilot import route_copilot
from msb_impact.engine import build_impact_report
from msb_zalo.bridge import ZaloBridge
from msb_zalo.client import ZaloBotClient
from msb_case_brief.service import CaseBriefService
from msb_case_brief.cache import CaseBriefCache

_demo_engine: DemoEventEngine | None = None
_repository: ToolRepository | None = None
_repository_lock = threading.Lock()
_sessions: set[str] = set()
_sessions_lock = threading.Lock()
_zalo_bridge: ZaloBridge | None = None
_zalo_client: ZaloBotClient | None = None
_case_brief_service: CaseBriefService | None = None
_case_brief_cache = CaseBriefCache()
_logger = logging.getLogger(__name__)
_DEMO_CIF = re.compile(r"(?:SYN\d{6}|GOLDEN_G\d{2})\Z")
_BROWSER_POST_ROUTES = frozenset({
    "/demo/customer-360", "/demo/next-best-action", "/demo/simulate",
    "/demo/events", "/demo/copilot", "/demo/portfolio", "/demo/impact",
    "/demo/zalo/recipient", "/demo/zalo/reset-recipient", "/demo/zalo/send-morning-brief",
    "/demo/case-brief", "/demo/case-brief/question",
})
_DEFAULT_ZALO_TOKEN_FILE = "/root/.config/msb-collection/zalo-bot-token"
_DEFAULT_ZALO_SECRET_FILE = "/root/.config/msb-collection/zalo-inbound-shared-secret"
_DEFAULT_ZALO_HEARTBEAT_FILE = str(Path(__file__).resolve().parent / ".zalo-worker-heartbeat")


def is_browser_safe_demo_route(method: str, path: str) -> bool:
    if method == "POST" and path in _BROWSER_POST_ROUTES:
        return True
    if method == "GET" and path in {"/demo/zalo/status", "/demo/zalo/preview"}:
        return True
    prefix = "/demo/timeline/" if method == "GET" else "/demo/reset/" if method == "POST" else None
    return bool(prefix and path.startswith(prefix) and re.fullmatch(r"[^/?#]+", path[len(prefix):]))


def _get_repository() -> ToolRepository:
    global _repository
    if _repository is None:
        with _repository_lock:
            if _repository is None:
                _repository = ToolRepository(Path(os.environ.get("SYNTHETIC_DATA_DIR", "build/synthetic-data")))
    return _repository


def _get_demo_engine() -> DemoEventEngine:
    global _demo_engine
    if _demo_engine is None:
        repo = _get_repository()
        _demo_engine = DemoEventEngine(repo)
    return _demo_engine


def _get_zalo_bridge() -> ZaloBridge:
    global _zalo_bridge
    if _zalo_bridge is None:
        repository = _get_repository()
        with _repository_lock:
            if _zalo_bridge is None:
                _zalo_bridge = ZaloBridge(repository, _zalo_sender)
    return _zalo_bridge


def _get_zalo_client() -> ZaloBotClient:
    global _zalo_client
    if _zalo_client is None:
        with _repository_lock:
            if _zalo_client is None:
                _zalo_client = ZaloBotClient(
                    token_file=os.environ.get("ZALO_BOT_TOKEN_FILE", _DEFAULT_ZALO_TOKEN_FILE)
                )
    return _zalo_client


def _zalo_sender(target_id: str, text: str) -> dict:
    return _get_zalo_client().send_message(target_id, text)


def _case_brief_tool_caller(name: str, args: dict) -> dict:
    return invoke_tool(name, args, repository=_get_repository())


def _case_brief_llm_complete(prompt: str, max_tokens: int, temperature: float) -> tuple[str | None, str | None]:
    from msb_agent.llm import maas_client_from_env
    client = maas_client_from_env(timeout_seconds=8)
    if client is None:
        return None, None
    return client.complete(prompt, max_tokens=max_tokens, temperature=temperature)


def _case_brief_knowledge_answer(question: str) -> dict:
    try:
        from msb_agent.copilot import _knowledge_service
        service = _knowledge_service()
        answer = service.answer(question)
        return {"answer": answer.answer, "sources": answer.sources or [],
                "knowledge_type": answer.knowledge_type, "status": answer.status}
    except Exception:
        return {"answer": "", "sources": [], "knowledge_type": "PROJECT_KNOWLEDGE", "status": "ERROR"}


def _get_case_brief_service() -> CaseBriefService:
    global _case_brief_service
    if _case_brief_service is None:
        with _repository_lock:
            if _case_brief_service is None:
                _case_brief_service = CaseBriefService(
                    tool_caller=_case_brief_tool_caller,
                    llm_complete=_case_brief_llm_complete,
                    knowledge_answer=_case_brief_knowledge_answer,
                    cache=_case_brief_cache,
                )
    return _case_brief_service


def _zalo_secret() -> str:
    path = Path(os.environ.get("ZALO_INBOUND_SHARED_SECRET_FILE", ""))
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    return os.environ.get("ZALO_INBOUND_SHARED_SECRET", "")


def _zalo_worker_alive() -> bool:
    path = Path(os.environ.get("MSB_ZALO_HEARTBEAT_FILE", _DEFAULT_ZALO_HEARTBEAT_FILE))
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return bool(data.get("ts")) and time.time() - float(data["ts"]) < 45
    except (ValueError, TypeError, json.JSONDecodeError):
        pass
    return False


def _invoke_copilot(payload: dict) -> dict:
    """Browser-safe copilot boundary; deterministic decisions remain in accepted tools."""
    def caller(name: str, args: dict) -> dict:
        return invoke_tool(name, args, repository=_get_repository())
    return route_copilot(payload, caller)


def _demo_cif(payload: dict) -> str | None:
    cif = payload.get("cif")
    if isinstance(cif, str) and _DEMO_CIF.fullmatch(cif.strip()):
        return cif.strip()
    return None


def _invalid_demo_cif() -> dict:
    return {"error": {"code": "INVALID_ARGUMENT", "message": "A synthetic demo CIF is required"}}


def _demo_session_cookie(token: str, secure: bool = False) -> str:
    suffix = "; Secure" if secure else ""
    return f"msb_demo_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800{suffix}"


def _read_json_object(handler: BaseHTTPRequestHandler) -> dict | None:
    """Read a request body and fail closed for valid non-object JSON values."""
    try:
        body = json.loads(handler.rfile.read(int(handler.headers.get("Content-Length", "0"))))
    except (ValueError, json.JSONDecodeError):
        handler._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}})
        return None
    if not isinstance(body, dict):
        handler._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}})
        return None
    return body


def _log_bridge_failure(operation: str, error: Exception) -> None:
    # Log only the exception class; exception text can contain provider URLs or other internals.
    _logger.warning("Zalo bridge %s failed (%s)", operation, type(error).__name__)


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

    def _require_demo_session(self) -> bool:
        if not self._demo_session_valid():
            self._send(401, {"error": {"code": "UNAUTHORIZED", "message": "Demo session required"}})
            return False
        return True

    def _demo_session_valid(self) -> bool:
        cookie = self.headers.get("Cookie", "")
        token = next((part.strip().split("=", 1)[1] for part in cookie.split(";") if part.strip().startswith("msb_demo_session=")), "")
        with _sessions_lock:
            return bool(token and token in _sessions)

    def _https_request(self) -> bool:
        return self.headers.get("X-Forwarded-Proto", "").lower() == "https"

    def _handle_auth_get(self) -> bool:
        if self.path != "/demo/auth/me":
            return False
        if self._demo_session_valid():
            self._send(200, {"authenticated": True, "username": os.environ.get("DEMO_ADMIN_USERNAME", "")})
        else:
            self._send(401, {"authenticated": False})
        return True

    def _validate_demo_request(self, body: dict) -> bool:
        if self.path not in {"/demo/portfolio", "/demo/impact"}:
            payload = {"cif": self.path.rsplit("/", 1)[1]} if self.path.startswith(("/demo/timeline/", "/demo/reset/")) else body
            cif = _demo_cif(payload)
            if cif is None:
                self._send(400, _invalid_demo_cif()); return False
            if "cif" in body:
                body["cif"] = cif
        # Aggregate demo endpoints must also fail closed for a non-demo repository.
        try:
            repo = _get_repository()
            if any(not _DEMO_CIF.fullmatch(cif) for cif in repo.cifs):
                self._send(403, {"error": {"code": "DEMO_ONLY", "message": "Synthetic demo data required"}})
                return False
        except ToolFailure:
            self._send(503, {"error": {"code": "UNAVAILABLE", "message": "Demo data unavailable"}})
            return False
        return True

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "healthy"}); return
        if self._handle_auth_get(): return
        browser_demo = is_browser_safe_demo_route("GET", self.path)
        if self.path.startswith("/demo/zalo/") and not self._require_demo_session(): return
        if not browser_demo and not self._require_auth(): return
        if browser_demo and not self.path.startswith("/demo/zalo/") and not self._validate_demo_request({}): return
        if self.path.startswith("/demo/timeline/"):
            cif = self.path[len("/demo/timeline/"):]
            try:
                entries = _get_demo_engine().get_timeline(cif)
                self._send(200, {"status": "success", "cif": cif, "timeline": entries, "demo_only": True})
            except ToolFailure as error:
                status = 404 if error.code == "NOT_FOUND" else 400
                self._send(status, {"error": {"code": error.code, "message": error.message}})
            return
        if self.path == "/demo/zalo/status":
            status = _get_zalo_bridge().status()
            status["worker_alive"] = _zalo_worker_alive()
            self._send(200, status); return
        if self.path == "/demo/zalo/preview":
            self._send(200, _get_zalo_bridge().preview()); return
        self._send(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}})

    def do_POST(self) -> None:
        if self.path == "/demo/auth/logout":
            cookie = self.headers.get("Cookie", "")
            token = next((part.strip().split("=", 1)[1] for part in cookie.split(";") if part.strip().startswith("msb_demo_session=")), "")
            with _sessions_lock:
                _sessions.discard(token)
            encoded = json.dumps({"authenticated": False}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(encoded))); self.send_header("Set-Cookie", "msb_demo_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"); self.end_headers(); self.wfile.write(encoded)
            return
        if self.path == "/demo/zalo/inbound":
            expected = _zalo_secret()
            supplied = self.headers.get("X-Zalo-Bridge-Secret", "")
            if not expected or not hmac.compare_digest(supplied, expected):
                self._send(401, {"error": {"code": "UNAUTHORIZED", "message": "Inbound bridge authorization required"}}); return
            body = _read_json_object(self)
            if body is None: return
            update_key = body.get("update_key")
            key = str(update_key) if update_key is not None else None
            if key is not None:
                cached = _get_zalo_bridge().lookup(key)
                if cached is not None:
                    self._send(200, cached)
                    return
            try:
                result = _get_zalo_bridge().pair_from_inbound(body.get("target_id", ""), body.get("text", ""), update_key=key)
                self._send(200, {"status": "accepted", "connection_status": result["connection_status"]})
                return
            except PermissionError as error:
                text = body.get("text", "")
                if isinstance(text, str) and text.strip().upper() != "MSB DEMO":
                    try:
                        result = _get_zalo_bridge().handle_inbound(body.get("target_id", ""), text, body.get("conversation_context"), update_key=key)
                        self._send(200, result)
                    except PermissionError as error:
                        _log_bridge_failure("inbound authorization", error)
                        self._send(403, {"error": {"code": "TARGET_NOT_PAIRED", "message": "Unknown Zalo target"}})
                    except RuntimeError as error:
                        _log_bridge_failure("inbound processing", error)
                        self._send(503, {"error": {"code": "ZALO_BRIDGE_UNAVAILABLE", "message": "Zalo bridge is temporarily unavailable"}})
                else:
                    _log_bridge_failure("pairing", error)
                    self._send(403, {"error": {"code": "PAIRING_REQUIRED", "message": "Approved pairing phrase required"}})
            except ValueError as error:
                _log_bridge_failure("inbound validation", error)
                self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "Approved Zalo target ID and text are required"}})
            return
        if self.path == "/demo/auth/login":
            try: body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            except (ValueError, json.JSONDecodeError):
                self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}}); return
            username = body.get("username") if isinstance(body, dict) else None
            password = body.get("password") if isinstance(body, dict) else None
            expected_user = os.environ.get("DEMO_ADMIN_USERNAME", "")
            expected_password = os.environ.get("DEMO_ADMIN_PASSWORD", "")
            if not (isinstance(username, str) and isinstance(password, str) and expected_user and expected_password and hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password)):
                self._send(401, {"error": {"code": "INVALID_CREDENTIALS", "message": "Tên đăng nhập hoặc mật khẩu không đúng"}}); return
            token = secrets.token_urlsafe(32)
            with _sessions_lock:
                _sessions.add(token)
            encoded = json.dumps({"authenticated": True, "username": expected_user}, sort_keys=True).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(encoded))); self.send_header("Set-Cookie", _demo_session_cookie(token, self._https_request())); self.end_headers(); self.wfile.write(encoded)
            return
        browser_demo = is_browser_safe_demo_route("POST", self.path)
        if self.path.startswith("/demo/zalo/"):
            if not self._require_demo_session(): return
        elif not browser_demo and not self._require_auth(): return
        try: body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}}); return
        if not isinstance(body, dict):
            self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": "JSON object required"}}); return
        if browser_demo and not self.path.startswith("/demo/zalo/") and not self._validate_demo_request(body): return
        if self.path in {"/demo/customer-360", "/demo/next-best-action"}:
            cif = _demo_cif(body)
            if cif is None:
                self._send(400, _invalid_demo_cif()); return
            tool_name = "get_customer_360" if self.path.endswith("customer-360") else "get_next_best_action"
            result = invoke_tool(tool_name, {"cif": cif}, repository=_get_repository())
            status = 200 if result["ok"] else 404 if result["error"]["code"] == "NOT_FOUND" else 400
            self._send(status, result); return
        if self.path == "/demo/simulate":
            cif = _demo_cif(body)
            changes = body.get("changes", {})
            if cif is None or not isinstance(changes, dict):
                self._send(400, _invalid_demo_cif()); return
            result = invoke_tool("simulate_decision", {"cif": cif, "changes": changes}, repository=_get_repository())
            status = 200 if result["ok"] else 404 if result["error"]["code"] == "NOT_FOUND" else 400
            self._send(status, result); return
        if self.path == "/demo/events":
            self._handle_demo_event(body); return
        if self.path == "/demo/copilot":
            self._send(200, _invoke_copilot(body)); return
        if self.path == "/demo/case-brief":
            cif = _demo_cif(body)
            if cif is None:
                self._send(400, _invalid_demo_cif()); return
            simulation_changes = body.get("changes") if isinstance(body.get("changes"), dict) else None
            try:
                result = _get_case_brief_service().generate_brief(cif, simulation_changes)
                self._send(200, result.to_dict())
            except Exception:
                self._send(200, {"status": "error", "error": {"code": "CASE_BRIEF_ERROR",
                    "message": "Case brief generation failed"}, "agent_path": "DETERMINISTIC"})
            return
        if self.path == "/demo/case-brief/question":
            cif = _demo_cif(body)
            question = body.get("question")
            if cif is None or not isinstance(question, str) or not question.strip():
                self._send(400, {"error": {"code": "INVALID_ARGUMENT",
                    "message": "A synthetic demo CIF and non-empty question are required"}}); return
            simulation_changes = body.get("changes") if isinstance(body.get("changes"), dict) else None
            try:
                result = _get_case_brief_service().answer_question(cif, question.strip(), simulation_changes)
                self._send(200, result.to_dict())
            except Exception:
                self._send(200, {"status": "error", "error": {"code": "CASE_BRIEF_ERROR",
                    "message": "Case brief question failed"}, "agent_path": "DETERMINISTIC"})
            return
        if self.path == "/demo/zalo/recipient":
            self._send(200, _get_zalo_bridge().configure(body)); return
        if self.path == "/demo/zalo/reset-recipient":
            self._send(200, _get_zalo_bridge().reset_recipient()); return
        if self.path == "/demo/zalo/send-morning-brief":
            try:
                self._send(200, _get_zalo_bridge().send_morning_brief())
            except PermissionError as error:
                _log_bridge_failure("morning brief authorization", error)
                self._send(409, {"error": {"code": "TARGET_NOT_PAIRED", "message": "Approved Zalo target required before sending"}})
            except RuntimeError as error:
                _log_bridge_failure("morning brief send", error)
                self._send(503, {"error": {"code": "ZALO_SEND_UNAVAILABLE", "message": "Zalo sending is temporarily unavailable"}})
            return
        if self.path == "/demo/portfolio":
            repo = _get_repository()
            rows = repo.portfolio()
            self._send(200, {"status": "success", "items": rows[:20], "total": len(rows),
                             "summary": {"portfolio_size": len(rows),
                                         "priority_displayed": min(20, len(rows)),
                                         "call_route_count": sum(1 for row in rows if row["final_route"] == "CALL"),
                                         "decisions_available": len(rows)},
                             **repo.meta, "demo_only": True}); return
        if self.path == "/demo/impact":
            try:
                report = build_impact_report(_get_repository(), body.get("assumptions", {}))
                self._send(200, {**report, **_get_repository().meta, "demo_only": True})
            except ValueError as error:
                self._send(400, {"error": {"code": "INVALID_ARGUMENT", "message": str(error)}})
            return
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
        result = invoke_tool(tool_name, body, repository=_get_repository())
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
