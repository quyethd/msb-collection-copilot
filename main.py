"""TASK-007B GreenNode Collection Decision Agent."""
from __future__ import annotations
import json, os, re, urllib.error, urllib.request
from pathlib import Path
from typing import Any

from greennode_agentbase import GreenNodeAgentBaseApp, PingStatus, RequestContext

from msb_agent.llm import GreenNodeMaaSClient, maas_client_from_env
from msb_agent.models import AGENT_VERSION, CANONICAL_MODEL
from msb_agent.router import parse_payload
from msb_agent.runtime import AgentRuntime
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository

app = GreenNodeAgentBaseApp()
_CIF = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b")


def _post_json(url: str, payload: dict, api_key: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key: headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response: return json.load(response)
    except urllib.error.HTTPError as error:
        try: return json.load(error)
        except Exception: return {"error": {"code": "HTTP_ERROR", "message": "Upstream request failed"}}


def _customer_360(cif: str) -> dict:
    public_url = os.environ.get("COLLECTION_TOOL_PUBLIC_URL")
    if public_url:
        url = public_url.rstrip("/") + "/get_customer_360"
    else:
        url = os.environ["COLLECTION_TOOL_BASE_URL"].rstrip("/") + "/tools/get_customer_360"
    return _post_json(url, {"cif": cif}, os.environ["COLLECTION_TOOL_API_KEY"])


def _tool_url(tool_name: str) -> str:
    public_url = os.environ.get("COLLECTION_TOOL_PUBLIC_URL")
    if public_url:
        return public_url.rstrip("/") + "/" + tool_name
    return os.environ["COLLECTION_TOOL_BASE_URL"].rstrip("/") + "/tools/" + tool_name


def _http_tool_caller(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return _post_json(_tool_url(tool_name), arguments, os.environ["COLLECTION_TOOL_API_KEY"])


def _in_process_tool_caller(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    data_dir = Path(os.environ.get("SYNTHETIC_DATA_DIR", "build/synthetic-data"))
    return invoke_tool(tool_name, arguments, input_directory=data_dir)


def _build_runtime() -> AgentRuntime:
    llm = maas_client_from_env()
    if os.environ.get("COLLECTION_TOOL_BASE_URL") or os.environ.get("COLLECTION_TOOL_PUBLIC_URL"):
        return AgentRuntime(_http_tool_caller, llm)
    return AgentRuntime(_in_process_tool_caller, llm)


def _maas_probe() -> dict:
    result = _post_json(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                        {"model": os.environ["LLM_MODEL"],
                         "messages": [{"role": "user", "content": "Reply with exactly: RUNTIME_MAAS_OK"}],
                         "max_tokens": 16, "temperature": 0}, os.environ["LLM_API_KEY"])
    message = ((result.get("choices") or [{}])[0].get("message") or {})
    return {"status": "success" if message.get("content") else "error",
            "check": "runtime_to_maas", "canonical_model": result.get("model")}


@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    if payload.get("connectivity_check") == "maas":
        return _maas_probe()
    mode, cif, message, changes = parse_payload(payload)
    runtime = _build_runtime()
    response = runtime.invoke(mode, cif, message, changes)
    return response.to_dict()


@app.ping
def health_check() -> PingStatus: return PingStatus.HEALTHY


if __name__ == "__main__": app.run(port=8080, host="0.0.0.0")
