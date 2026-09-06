"""Tool-aware and model-aware routing for the browser demo copilot.

This module is orchestration only. Collection decisions continue to come from
the accepted deterministic tools; model output is limited to explanation or
summarization text.
"""
from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from typing import Any, Callable

from .llm import fast_maas_client_from_env, maas_client_from_env
from .runtime import AgentRuntime, _format_amount_vn, _tool_data, _tool_ok
from .models import decision_from_nba

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]
INTENTS = (
    "GREETING_HELP", "KNOWLEDGE", "CUSTOMER_SUMMARY", "CASHFLOW", "PTP",
    "ROUTE_PRIORITY", "DECISION_EXPLANATION", "SIMULATION", "OUT_OF_SCOPE",
)
_DECISION_WORDS = ("tai sao", "sao ", "nen goi", "chua goi", "chua nen", "goi ngay", "de xuat", "hanh dong", "xu ly sao", "bo qua de xuat")
# Concept questions ("... là gì?", "... dùng để làm gì?", "... khác nhau thế nào?")
# route to the Project Knowledge RAG. They deliberately never match customer
# phrasing: "Dòng tiền SYN002846 hiện thế nào?" keeps its CIF-bound intent.
_KNOWLEDGE_MARKERS = (
    "la gi", "de lam gi", "dong vai tro", "khac nhau the nao", "khac nhau nhu the nao",
    "nam o dau", "chay o dau", "duoc tinh nhu the nao", "duoc tinh the nao",
    "tu quyet dinh", "tu dua ra quyet dinh", "ai quyet dinh", "quyen quyet dinh",
    "nghia la",
)
_SECURITY_WORDS = (
    "api_key", "api key", "llm_api_key", "client_secret", "client secret",
    ".env", "password", "mat khau", "credentials", "credential",
    "reasoning_content", "private prompt", "internal endpoint",
)


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(c for c in normalized if not unicodedata.combining(c))


def classify_intent(message: str) -> tuple[str, float, str]:
    text = _plain(message.strip())
    if not text:
        return "OUT_OF_SCOPE", 1.0, "deterministic"
    if any(x in text for x in ("xin chao", "hello", "ban lam gi duoc", "tro giup", "help")) or re.search(r"^hi(?:[ !,.]|$)", text):
        return "GREETING_HELP", 0.99, "deterministic"
    if any(x in text for x in _SECURITY_WORDS):
        return "OUT_OF_SCOPE", 0.99, "deterministic"
    if any(x in text for x in _KNOWLEDGE_MARKERS):
        return "KNOWLEDGE", 0.97, "deterministic"
    if any(x in text for x in ("neu ", "gia su", "mo phong", "tinh huong", "what if", "thay doi")):
        return "SIMULATION", 0.98, "deterministic"
    if any(x in text for x in ("cam ket", "ptp", "hua tra", "hứa trả")):
        return "PTP", 0.96, "deterministic"
    if any(x in text for x in ("dong tien", "tien vao", "tien ve", "cashflow", "tuan nay khong co tien")):
        return "CASHFLOW", 0.96, "deterministic"
    if any(x in text for x in ("call hay cbs", "tuyen", "chay tuyen", "thuoc call", "thuoc cbs")):
        return "ROUTE_PRIORITY", 0.96, "deterministic"
    if any(x in text for x in _DECISION_WORDS):
        return "DECISION_EXPLANATION", 0.96, "deterministic"
    if any(x in text for x in ("tom tat", "tinh trang", "thong tin khach", "ho so")):
        return "CUSTOMER_SUMMARY", 0.92, "deterministic"
    if any(x in text for x in ("thoi tiet", "ke chuyen", "viet code", "dich bai", "mat khau")):
        return "OUT_OF_SCOPE", 0.98, "deterministic"
    # Ambiguous questions may use the separately configured fast classifier.
    # Its output is deliberately restricted to the small taxonomy above.
    fast = fast_maas_client_from_env(timeout_seconds=3)
    if fast is not None:
        prompt = ("Classify the Vietnamese collection-assistant question. "
                  "Return JSON only with intent and confidence. Allowed intents: "
                  + ", ".join(INTENTS) + ". Question: " + message)
        raw, _ = fast.complete(prompt, max_tokens=40, temperature=0)
        if raw:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    candidate = parsed.get("intent")
                    confidence = float(parsed.get("confidence", 0))
                    if candidate in INTENTS and 0 <= confidence <= 1:
                        return candidate, confidence, "fast_qwen_classifier"
                except (ValueError, TypeError, json.JSONDecodeError):
                    pass
    return "CUSTOMER_SUMMARY", 0.35, "general_investigation_fallback"


def _timed_call(caller: ToolCaller, name: str, args: dict[str, Any], tools: list[str], started: float) -> dict[str, Any]:
    result = caller(name, args)
    tools.append(name)
    return result


def _simple_response(cif: str, intent: str, ctx: dict[str, Any], model_path: str, timings: dict[str, float], tools: list[str], generated: str | None = None, model: str | None = None) -> dict[str, Any]:
    debt, cash, ptp = ctx.get("debt", {}), ctx.get("cashflow", {}), ctx.get("ptp", {})
    if intent == "CASHFLOW":
        summary = f"Tiền vào 7 ngày gần nhất: {_format_amount_vn(cash.get('inflow_7d'))}. Dòng tiền ròng 30 ngày: {_format_amount_vn(cash.get('net_cashflow_30d'))}."
        sections = [{"title": "Dòng tiền", "items": [summary]}]
    elif intent == "PTP":
        status = ptp.get("status", "NONE")
        label = {"OPEN": "đang mở", "BROKEN": "không thực hiện", "KEPT": "đã thực hiện", "NONE": "chưa có"}.get(status, "chưa xác định")
        summary = f"Khách hàng hiện {label} cam kết thanh toán."
        sections = [{"title": "Cam kết thanh toán", "content": summary}]
    else:
        summary = f"Khách hàng {cif}: dư nợ {_format_amount_vn(debt.get('total_outstanding_cif'))}, quá hạn {debt.get('max_dpd_cif')} ngày."
        sections = [{"title": "Tóm tắt tình trạng", "items": [summary, f"Tiền vào 7 ngày: {_format_amount_vn(cash.get('inflow_7d'))}.", f"Cam kết thanh toán: {ptp.get('status', 'NONE')}."]}]
    return _response(cif, intent, generated or summary, sections, tools, None, model or model_path, timings, None)


def _response(cif: str, intent: str, summary: str, sections: list[dict[str, Any]], tools: list[str], decision: dict[str, Any] | None, path: str, timings: dict[str, float], error: dict[str, str] | None) -> dict[str, Any]:
    return {"status": "error" if error else "success", "mode": "EXPLAIN", "cif": cif, "decision": decision,
            "evidence": [], "summary": summary, "sections": sections, "tools_used": tools,
            "canonical_model": None if path in ("LOCAL", "FALLBACK") else path, "synthetic_data": True,
            "agent_version": "TASK-011G-V1", "error": error, "question_intent": intent,
            "metadata": {**timings, "path": path, "intent": intent}}


_RAG_LOCK = threading.Lock()
_RAG_SERVICE = None


def _knowledge_service():
    """Lazy live KnowledgeRagService (GreenNode vDB via config + Qwen Flash
    answerer). Built once; a failure here fails soft into the standard
    low-confidence refusal instead of surfacing to the browser."""
    global _RAG_SERVICE
    if _RAG_SERVICE is None:
        with _RAG_LOCK:
            if _RAG_SERVICE is None:
                from msb_knowledge_rag.answerer import MaasRagAnswerer
                from msb_knowledge_rag.config import KnowledgeRagConfig
                from msb_knowledge_rag.service import KnowledgeRagService
                config = KnowledgeRagConfig()
                _RAG_SERVICE = KnowledgeRagService(
                    config=config, answerer=MaasRagAnswerer(config=config)
                )
    return _RAG_SERVICE


def _knowledge_response(
    cif: str, message: str, started: float, confidence: float,
    classifier: str, router_ms: float,
) -> dict[str, Any]:
    """Route a PROJECT_KNOWLEDGE question through the RAG service and map its
    RagAnswer to the copilot response contract. Sources carry human-readable
    document title + section; raw vectors/endpoints/credentials never leave the
    service."""
    from msb_knowledge_rag.config import LOW_CONFIDENCE_REFUSAL
    from msb_knowledge_rag.models import RagAnswer
    service = None
    try:
        service = _knowledge_service()
        answer = service.answer(message)
    except Exception:
        answer = RagAnswer(
            status="LOW_CONFIDENCE",
            path="rag_qwen",
            knowledge_type="PROJECT_KNOWLEDGE",
            answer=LOW_CONFIDENCE_REFUSAL,
            classification="LOW_CONFIDENCE",
            sources=[],
            meta={},
        )
    rags = answer.sources or []
    sections: list[dict[str, Any]] = []
    if answer.status == "ANSWERED" and answer.answer:
        sections.append({"title": "Câu trả lời", "content": answer.answer})
    if rags:
        sections.append({
            "title": "Nguồn tham khảo",
            "items": [
                f"{index + 1}. {src.get('title', '')} — {src.get('section', '')}"
                for index, src in enumerate(rags)
            ],
        })
    timings: dict[str, float] = {
        "router_ms": round(router_ms, 2), "tool_ms": 0.0, "model_ms": 0.0,
        "classification_ms": 0.0, "embedding_ms": 0.0, "retrieval_ms": 0.0,
        "knowledge_ms": 0.0,
        "total_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    for key in ("classification_ms", "embedding_ms", "retrieval_ms", "model_ms"):
        if answer.meta.get(key) is not None:
            timings[key] = round(float(answer.meta[key]), 3)
    timings["knowledge_ms"] = round(
        max(0.0, timings["total_ms"] - timings["router_ms"]), 2
    )
    result = _response(
        cif, "KNOWLEDGE", answer.answer or LOW_CONFIDENCE_REFUSAL, sections,
        [], None, "RAG_QWEN", timings, None,
    )
    result["mode"] = "KNOWLEDGE"
    result["canonical_model"] = None
    result["answer"] = answer.answer
    result["sources"] = rags
    result["knowledge_type"] = answer.knowledge_type
    result["knowledge_status"] = answer.status
    result["metadata"].update({
        "confidence": confidence,
        "classifier": classifier,
        "path": "RAG_QWEN",
        "intent": "KNOWLEDGE",
        "knowledge_status": answer.status,
        "knowledge_type": answer.knowledge_type,
        "knowledge_version": answer.meta.get("knowledge_version"),
        "qwen_fast_model": getattr(getattr(service, "config", None), "qwen_fast_model", None),
        "total_ms": timings["total_ms"],
    })
    return result


def _simulation_changes(message: str, changes: dict[str, Any]) -> dict[str, Any]:
    result = dict(changes)
    text = _plain(message)
    if "dong tien 7 ngay" in text and ("bang 0" in text or "khong co tien" in text):
        result.setdefault("inflow_7d", 0)
    if "cam ket thanh toan" in text and ("pha vo" in text or "bi pha" in text):
        result.setdefault("ptp_state", "BROKEN")
    return result


def route_copilot(payload: dict[str, Any], caller: ToolCaller) -> dict[str, Any]:
    started = time.perf_counter(); router_start = started
    cif = payload.get("cif"); message = payload.get("message")
    if not isinstance(cif, str) or not cif.strip() or not isinstance(message, str):
        return {"status": "error", "error": {"code": "INVALID_ARGUMENT", "message": "cif and message are required"}}
    cif = cif.strip(); message = message.strip()
    intent, confidence, classifier = classify_intent(message)
    router_ms = (time.perf_counter() - router_start) * 1000
    timings = {"router_ms": round(router_ms, 2), "tool_ms": 0.0, "model_ms": 0.0, "total_ms": 0.0}
    tool_durations: list[float] = []
    def timed_caller(name: str, args: dict[str, Any]) -> dict[str, Any]:
        call_started = time.perf_counter()
        try:
            return caller(name, args)
        finally:
            tool_durations.append((time.perf_counter() - call_started) * 1000)
    if intent == "GREETING_HELP":
        result = _response(cif, intent, "Chào bạn. Tôi có thể hỗ trợ giải thích quyết định thu hồi, dòng tiền, cam kết thanh toán, tuyến CALL/CBS và mô phỏng tình huống khi dữ liệu thay đổi.", [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result
    if intent == "OUT_OF_SCOPE":
        result = _response(cif, intent, "Tôi chỉ hỗ trợ thông tin và quyết định trong quy trình thu hồi nợ của MSB trên dữ liệu mô phỏng.", [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "KNOWLEDGE":
        return _knowledge_response(cif, message, started, confidence, classifier, router_ms)

    tools: list[str] = []; tool_start = time.perf_counter()
    if intent == "SIMULATION":
        runtime = AgentRuntime(timed_caller, maas_client_from_env(timeout_seconds=8))
        result = runtime.invoke("SIMULATE", cif, message, _simulation_changes(message, payload.get("changes", {}) if isinstance(payload.get("changes", {}), dict) else {})).to_dict()
        tools = result.get("tools_used", []); path = "MAAS_GLM" if result.get("canonical_model") else "FALLBACK"
    elif intent == "DECISION_EXPLANATION":
        runtime = AgentRuntime(timed_caller, maas_client_from_env(timeout_seconds=8))
        result = runtime.invoke("EXPLAIN", cif, message).to_dict()
        tools = result.get("tools_used", []); path = "MAAS_GLM" if result.get("canonical_model") else "FALLBACK"
    elif intent == "ROUTE_PRIORITY":
        nba_envelope = _timed_call(timed_caller, "get_next_best_action", {"cif": cif}, tools, started)
        if not _tool_ok(nba_envelope):
            err = nba_envelope.get("error", {"code": "NOT_FOUND", "message": "Customer not found"})
            return _response(cif, intent, "Không tìm thấy quyết định cho khách hàng mô phỏng.", [], tools, None, "LOCAL", timings, err)
        nba = _tool_data(nba_envelope)
        route = {"CALL": "tuyến gọi", "CBS": "tuyến CBS"}.get(nba.get("final_route"), "tuyến chưa xác định")
        channel = {"CALL": "gọi điện", "NONE": "chưa cần liên hệ"}.get(nba.get("channel"), "kênh theo đề xuất")
        summary = f"Khách hàng thuộc {route}. Kênh đề xuất: {channel}."
        result = _response(cif, intent, summary, [{"title": "Tuyến xử lý", "content": summary}], tools, decision_from_nba(nba), "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["tool_ms"] = round((time.perf_counter()-tool_start)*1000, 2); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result
    else:
        ctx_envelope = _timed_call(timed_caller, "get_customer_360", {"cif": cif}, tools, started)
        if not _tool_ok(ctx_envelope):
            err = ctx_envelope.get("error", {"code": "NOT_FOUND", "message": "Customer not found"})
            return _response(cif, intent, "Không tìm thấy dữ liệu khách hàng mô phỏng.", [], tools, None, "LOCAL", timings, err)
        ctx = _tool_data(ctx_envelope)
        fast = fast_maas_client_from_env(timeout_seconds=6)
        generated = None; model = None; path = "LOCAL"
        if fast:
            fast_prompt = ("Tóm tắt ngắn gọn bằng tiếng Việt, chỉ dùng dữ liệu đã cung cấp, "
                           "không đưa ra quyết định nghiệp vụ mới. Dữ liệu: " + json.dumps(ctx, ensure_ascii=False))
            model_start = time.perf_counter()
            generated, model = fast.complete(fast_prompt, max_tokens=120, temperature=0)
            timings["model_ms"] = round((time.perf_counter()-model_start)*1000, 2)
            if generated:
                path = "FAST_QWEN"
            else:
                path = "FALLBACK"
        result = _simple_response(cif, intent, ctx, path, timings, tools, generated, model)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["tool_ms"] = round((time.perf_counter()-tool_start)*1000, 2); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result
    timings["tool_ms"] = round(sum(tool_durations), 2)
    elapsed_ms = (time.perf_counter() - started) * 1000
    timings["model_ms"] = round(max(0.0, elapsed_ms - timings["router_ms"] - timings["tool_ms"]), 2)
    result["question_intent"] = intent
    result.setdefault("metadata", {}).update(timings); result["metadata"].update({"confidence": confidence, "classifier": classifier, "path": path, "intent": intent}); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2)
    return result
