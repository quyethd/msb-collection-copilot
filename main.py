"""Minimal TASK-007B.0 AgentBase connectivity-spike agent."""
from __future__ import annotations
import json, os, re, urllib.error, urllib.request
from greennode_agentbase import GreenNodeAgentBaseApp, PingStatus, RequestContext

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

def _maas_summary(cif: str, tool_result: dict) -> tuple[str, str | None]:
    if not tool_result.get("ok"): return "Tool lookup failed; no model interpretation was requested.", None
    prompt = ("This is synthetic prototype collection data. Confirm that the customer record was retrieved for "
              f"{cif}. Do not add, change, or recommend any business action. Reply in one short sentence.\nDATA:\n"
              + json.dumps(tool_result["data"], sort_keys=True))
    result = _post_json(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                        {"model": os.environ["LLM_MODEL"], "messages": [{"role": "user", "content": prompt}],
                         "max_tokens": 80, "temperature": 0}, os.environ["LLM_API_KEY"])
    message = ((result.get("choices") or [{}])[0].get("message") or {})
    return message.get("content") or "Model returned no visible content.", result.get("model")

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
    message = payload.get("message", "")
    match = _CIF.search(message) if isinstance(message, str) else None
    if not match:
        return {"status": "error", "error": {"code": "INVALID_ARGUMENT", "message": "Message must contain one synthetic CIF"}}
    cif = match.group(0); tool_result = _customer_360(cif); summary, canonical_model = _maas_summary(cif, tool_result)
    return {"status": "success" if tool_result.get("ok") else "error", "cif": cif,
            "tool": "get_customer_360", "tool_result": tool_result, "model_summary": summary,
            "canonical_model": canonical_model, "synthetic_data": True}

@app.ping
def health_check() -> PingStatus: return PingStatus.HEALTHY

if __name__ == "__main__": app.run(port=8080, host="0.0.0.0")
