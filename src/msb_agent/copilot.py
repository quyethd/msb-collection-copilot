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
from . import semantics

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]
INTENTS = (
    "GREETING_HELP", "KNOWLEDGE", "CUSTOMER_SUMMARY", "CASHFLOW", "PTP",
    "ROUTE_PRIORITY", "DECISION_EXPLANATION", "SIMULATION", "OUT_OF_SCOPE",
    "TODAY_WORKLIST", "SCORE_VALUE", "SCORE_BREAKDOWN", "EXPLAIN_PRIORITY",
    "CLARIFICATION", "CLARIFICATION_RESPONSE", "SIMULATION_FOLLOWUP",
    "RETURN_TO_BASELINE", "ACTIVE_CIF_QUERY", "UNKNOWN",
)
_DECISION_WORDS = ("tai sao", "sao ", "nen goi", "chua goi", "chua nen", "goi ngay", "de xuat", "hanh dong", "xu ly sao", "bo qua de xuat", "bo qua rule", "chuyen khach", "contact")
# Concept questions ("... là gì?", "... dùng để làm gì?", "... khác nhau thế nào?")
# route to the Project Knowledge RAG. They deliberately never match customer
# phrasing: "Dòng tiền SYN002846 hiện thế nào?" keeps its CIF-bound intent.
_KNOWLEDGE_MARKERS = (
    "la gi", "de lam gi", "dong vai tro", "khac nhau the nao", "khac nhau nhu the nao",
    "nam o dau", "chay o dau", "duoc tinh nhu the nao", "duoc tinh the nao",
    "tu quyet dinh", "tu dua ra quyet dinh", "ai quyet dinh", "quyen quyet dinh", "lien quan gi",
    "nghia la",
)
_SECURITY_WORDS = (
    "api_key", "api key", "llm_api_key", "client_secret", "client secret",
    ".env", "password", "mat khau", "credentials", "credential",
    "reasoning_content", "private prompt", "internal endpoint",
)

_FOLLOWUP_WORDS = ("vi sao", "vì sao", "the con", "thế còn", "vay nen lam gi", "vậy nên làm gì", "lien quan gi", "liên quan gì", "the gio lam gi", "gio lam gi", "bay gio lam gi", "diem no", "diem cua no")
_CUSTOMER_CIF_RE = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b", re.IGNORECASE)
_INFLOW_7D_ZERO_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\b(?:tien vao|dong tien) 7 ngay (?:bang|la) 0\b",
    r"\bkhong co (?:tien vao|dong tien) 7 ngay\b",
    r"\b7 ngay toi khong co (?:tien vao|dong tien)\b",
    r"\b(?:tien vao|dong tien) tuan nay (?:bang|la) 0\b",
    r"\bkhong co (?:tien vao|dong tien) tuan nay\b",
    r"\btuan nay khong co (?:tien vao|dong tien)\b",
    r"\bdong tien 7 ngay khong co tien\b",
))


def _mentions_zero_inflow_7d(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INFLOW_7D_ZERO_PATTERNS)


def _conversation_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Return only bounded, non-authoritative routing hints from the UI."""
    raw = payload.get("conversation_context")
    if not isinstance(raw, dict):
        return {}
    allowed = ("active_cif", "previous_intent", "previous_topic", "previous_user_question",
               "previous_path", "last_simulation_field", "last_simulation_changes",
               "pending_clarification", "last_cif")
    context: dict[str, Any] = {}
    for key in allowed:
        value = raw.get(key)
        if isinstance(value, str):
            context[key] = value[:160]
        elif key == "last_simulation_changes" and isinstance(value, dict):
            safe = {}
            for field in ("inflow_7d", "inflow_3d", "net_cashflow_30d", "ptp_state"):
                if field in value and isinstance(value[field], (int, float, str)):
                    safe[field] = value[field]
            context[key] = safe
    return context


def _resolve_followup(message: str, context: dict[str, Any]) -> str | None:
    """Resolve short references for routing only; never supplies business facts."""
    if not context or not any(token in _plain(message) for token in _FOLLOWUP_WORDS):
        return None
    previous = context.get("previous_intent")
    text = _plain(message)
    if previous == "DECISION_EXPLANATION" and any(token in text for token in ("vi sao", "vì sao")):
        return "DECISION_EXPLANATION"
    if previous == "CASHFLOW" and any(token in text for token in ("the con", "thế còn")):
        return "CASHFLOW"
    if previous == "SIMULATION" and any(token in text for token in ("vay nen lam gi", "vậy nên làm gì", "the gio lam gi", "gio lam gi", "bay gio lam gi")):
        return "SIMULATION"
    if previous in ("SCORE_BREAKDOWN", "SCORE_VALUE") and "diem" in text:
        return previous
    if previous == "KNOWLEDGE" and any(token in text for token in ("lien quan gi", "liên quan gì")):
        return "KNOWLEDGE"
    return None


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
    if _mentions_zero_inflow_7d(text) or any(x in text for x in ("neu ", "gia su", "mo phong", "tinh huong", "what if", "thay doi")):
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
        label = semantics.map_ptp_status(status)
        summary = f"Khách hàng hiện {label.lower()} cam kết thanh toán." if status != "NONE" else "Khách hàng chưa có cam kết thanh toán."
        sections = [{"title": "Cam kết thanh toán", "content": summary}]
    else:
        summary = f"Khách hàng {cif}: dư nợ {_format_amount_vn(debt.get('total_outstanding_cif'))}, quá hạn {debt.get('max_dpd_cif')} ngày."
        sections = [{"title": "Tóm tắt tình trạng", "items": [summary, f"Tiền vào 7 ngày: {_format_amount_vn(cash.get('inflow_7d'))}.", f"Cam kết thanh toán: {semantics.map_ptp_status(ptp.get('status', 'NONE'))}."]}]
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
    if _mentions_zero_inflow_7d(text):
        result.setdefault("inflow_7d", 0)
    if "cam ket thanh toan" in text and ("pha vo" in text or "bi pha" in text):
        result.setdefault("ptp_state", "BROKEN")
    return result


def _finish_local(cif: str, intent: str, summary: str, sections: list[dict[str, Any]],
                  started: float, confidence: float, classifier: str, router_ms: float,
                  *, last_topic: str = "", pending: str = "", decision: dict[str, Any] | None = None) -> dict[str, Any]:
    timings = {"router_ms": round(router_ms, 2), "tool_ms": 0.0, "model_ms": 0.0,
               "total_ms": round((time.perf_counter() - started) * 1000, 2)}
    result = _response(cif, intent, summary, sections, [], decision, "LOCAL", timings, None)
    meta = {"confidence": confidence, "classifier": classifier}
    if last_topic:
        meta["last_topic"] = last_topic
    if pending:
        meta["pending_clarification"] = pending
    result["metadata"].update(meta)
    return result


def _today_worklist_response(cif: str, started: float, confidence: float, classifier: str,
                             router_ms: float, timed_caller: ToolCaller) -> dict[str, Any]:
    portfolio_envelope = timed_caller("get_portfolio", {})
    items = []
    if _tool_ok(portfolio_envelope):
        items = _tool_data(portfolio_envelope).get("items") or []
    scored = [row for row in items if isinstance(row.get("recovery_opportunity_score"), (int, float))]
    scored.sort(key=lambda row: (-int(row["recovery_opportunity_score"]), str(row["cif"])))
    top = scored[:3]
    call_no_now = 0
    for row in scored:
        route = row.get("final_route")
        if route == "CALL":
            nba_env = timed_caller("get_next_best_action", {"cif": row["cif"]})
            if _tool_ok(nba_env) and _tool_data(nba_env).get("channel") == "NONE":
                call_no_now += 1
    lines = [
        f"• {len(scored)} hồ sơ có quyết định từ hệ thống",
        f"• {call_no_now} hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay",
        "", "Top hồ sơ cần xem:",
    ]
    for index, row in enumerate(top, start=1):
        lines.append(f"{index}. {row['cif']} · Điểm {row.get('recovery_opportunity_score', 0)} · {semantics.map_route(row.get('final_route'))}")
    summary = f"Hôm nay có {len(scored)} hồ sơ có quyết định; {call_no_now} hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay."
    sections = [{"title": "Ưu tiên hôm nay", "items": lines}]
    return _finish_local(cif, "TODAY_WORKLIST", summary, sections, started, confidence, classifier, router_ms)


def _score_response(cif: str, target: str, intent: str, started: float, confidence: float,
                    classifier: str, router_ms: float, timed_caller: ToolCaller) -> dict[str, Any]:
    if not target:
        return _finish_local(cif, intent, "Anh/Chị đang hỏi về điểm của hồ sơ nào? Vui lòng gửi CIF để tôi giải thích.",
                             [], started, confidence, classifier, router_ms)
    envelope = timed_caller("get_recovery_opportunity", {"cif": target})
    if not _tool_ok(envelope):
        return _finish_local(cif, intent, f"Không tìm thấy dữ liệu điểm cho hồ sơ {target}.",
                             [], started, confidence, classifier, router_ms)
    data = _tool_data(envelope)
    score = data.get("recovery_opportunity_score")
    if intent == "SCORE_VALUE":
        summary = f"Điểm cơ hội thu hồi của {target} là {score}/100."
        return _finish_local(cif, intent, summary, [{"title": "Điểm cơ hội thu hồi", "content": summary}],
                             started, confidence, classifier, router_ms)
    breakdown = data.get("component_breakdown") or []
    lines = [f"Điểm cơ hội thu hồi của {target} là {score}/100."]
    total = 0
    for component in breakdown:
        if not isinstance(component, dict):
            continue
        name = component.get("name")
        value, maximum = component.get("score"), component.get("max_score")
        if not isinstance(value, (int, float)):
            continue
        total += int(value)
        maximum = int(maximum) if isinstance(maximum, (int, float)) else None
        label = semantics.TREATMENT_VN.get(name, str(name))
        lines.append(f"• {label}: {int(value)}" + (f"/{maximum}" if maximum is not None else ""))
    if total:
        lines.append(f"Tổng hợp các thành phần: {total}.")
    summary = f"Điểm cơ hội thu hồi của {target} là {score}/100."
    return _finish_local(cif, "SCORE_BREAKDOWN", summary, [{"title": "Cách tính điểm", "items": lines}],
                         started, confidence, classifier, router_ms)


def _explain_priority_response(cif: str, target: str, started: float, confidence: float,
                               classifier: str, router_ms: float, timed_caller: ToolCaller) -> dict[str, Any]:
    if not target:
        return _finish_local(cif, "EXPLAIN_PRIORITY", "Anh/Chị vui lòng cho tôi mã CIF để giải thích ưu tiên.",
                             [], started, confidence, classifier, router_ms)
    nba_env = timed_caller("get_next_best_action", {"cif": target})
    ro_env = timed_caller("get_recovery_opportunity", {"cif": target})
    nba = _tool_data(nba_env) if _tool_ok(nba_env) else {}
    ro = _tool_data(ro_env) if _tool_ok(ro_env) else {}
    score = ro.get("recovery_opportunity_score") or nba.get("recovery_opportunity_score")
    treatment = semantics.map_treatment(nba.get("treatment"))
    route = semantics.map_route(nba.get("final_route"))
    summary = (f"Hồ sơ {target} nằm trong danh sách cần xem hôm nay theo dữ liệu mô phỏng. "
               f"Điểm cơ hội thu hồi hiện tại là {score}/100; tuyến {route}; hành động đề xuất {treatment.lower()}.")
    sections = [{"title": f"Vì sao xem {target}", "items": [
        f"Điểm cơ hội thu hồi: {score}/100",
        f"Tuyến xử lý: {route}",
        f"Hành động đề xuất: {treatment}",
    ]}]
    return _finish_local(cif, "EXPLAIN_PRIORITY", summary, sections, started, confidence, classifier, router_ms)


def _static_knowledge_response(cif: str, intent: str, text: str, started: float, confidence: float,
                               classifier: str, router_ms: float, last_topic: str) -> dict[str, Any]:
    sections = [{"title": "Kiến thức", "content": text}]
    return _finish_local(cif, intent, text, sections, started, confidence, classifier, router_ms, last_topic=last_topic)


def _map_canonical_to_web(intent: str) -> str:
    """Map a shared canonical intent to the Web handler taxonomy."""
    if intent in (semantics.GREETING, semantics.HELP):
        return "GREETING_HELP"
    if intent == semantics.KNOWLEDGE_EVALUATION:
        return "KNOWLEDGE"
    if intent == semantics.CURRENT_CASE_SUMMARY:
        return "CUSTOMER_SUMMARY"
    if intent == semantics.CURRENT_CASE_ACTION:
        return "DECISION_EXPLANATION"
    if intent == semantics.UNKNOWN:
        return "UNKNOWN"
    return intent


def route_copilot(payload: dict[str, Any], caller: ToolCaller) -> dict[str, Any]:
    started = time.perf_counter(); router_start = started
    cif = payload.get("cif"); message = payload.get("message")
    if not isinstance(cif, str) or not cif.strip() or not isinstance(message, str):
        return {"status": "error", "error": {"code": "INVALID_ARGUMENT", "message": "cif and message are required"}}
    cif = cif.strip(); message = message.strip()
    context = _conversation_context(payload)
    if context.get("active_cif") and context["active_cif"] != cif:
        context = {}
    resolved_kind = ""
    resolved_cif: str | None = None
    resolved_changes: dict[str, Any] = {}
    if any(token in _plain(message) for token in (".env", "api key", "api_key", "llm_api_key", "mat khau", "password", "reasoning_content", "system prompt", "private prompt")):
        intent, confidence, classifier = "OUT_OF_SCOPE", 1.0, "security_boundary"
    else:
        # Shared semantic resolver runs first. A high-confidence explicit/global
        # intent (precedence 1-4) beats the generic decision anchor and the
        # generic followup fallback. active_cif is context only and never
        # becomes the default intent (the resolver returns UNKNOWN for it).
        state = semantics.ConversationState.from_context(context)
        resolved = semantics.resolve(message, state)
        resolved_kind = resolved.kind
        resolved_cif = resolved.cif
        resolved_changes = resolved.changes or {}
        if resolved.intent != semantics.UNKNOWN and resolved.confidence >= 0.9:
            confidence, classifier = resolved.confidence, "shared_semantic_resolver"
            intent = _map_canonical_to_web(resolved.intent)
        elif _CUSTOMER_CIF_RE.search(message) and any(token in _plain(message) for token in _DECISION_WORDS):
            # An explicit customer decision question wins over a mixed conceptual
            # phrase; the accepted Decision Core remains authoritative.
            intent, confidence, classifier = "DECISION_EXPLANATION", 0.99, "customer_decision_anchor"
            resolved_cif = _CUSTOMER_CIF_RE.search(message).group(0).upper()
        else:
            resolved_followup = _resolve_followup(message, context)
            if resolved_followup:
                intent, confidence, classifier = resolved_followup, 0.98, "bounded_conversation_context"
            elif context and any(token in _plain(message) for token in _FOLLOWUP_WORDS):
                intent, confidence, classifier = "AMBIGUOUS_FOLLOWUP", 1.0, "clarification_boundary"
            elif _plain(message).strip(" ?!.,") in ("vi sao", "sao"):
                intent, confidence, classifier = "AMBIGUOUS_FOLLOWUP", 1.0, "clarification_boundary"
            elif any(token in _plain(message) for token in _DECISION_WORDS):
                intent, confidence, classifier = "DECISION_EXPLANATION", 0.96, "deterministic_decision_words"
            else:
                confidence, classifier = resolved.confidence, "shared_semantic_resolver"
                intent = _map_canonical_to_web(resolved.intent)
    router_ms = (time.perf_counter() - router_start) * 1000
    timings = {"router_ms": round(router_ms, 2), "tool_ms": 0.0, "model_ms": 0.0, "total_ms": 0.0}
    tool_durations: list[float] = []
    def timed_caller(name: str, args: dict[str, Any]) -> dict[str, Any]:
        call_started = time.perf_counter()
        try:
            return caller(name, args)
        finally:
            tool_durations.append((time.perf_counter() - call_started) * 1000)
    if intent == "AMBIGUOUS_FOLLOWUP":
        result = _response(cif, "AMBIGUOUS_FOLLOWUP", "Anh/Chị muốn hỏi tiếp về quyết định, dòng tiền hay mô phỏng nào?", [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": 1.0, "classifier": "clarification_boundary"})
        result["question_intent"] = "AMBIGUOUS_FOLLOWUP"
        return result
    if intent == "GREETING_HELP":
        result = _response(cif, intent, "Chào bạn. Tôi có thể hỗ trợ giải thích quyết định thu hồi, dòng tiền, cam kết thanh toán, tuyến CALL/CBS và mô phỏng tình huống khi dữ liệu thay đổi.", [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result
    if intent == "OUT_OF_SCOPE":
        result = _response(cif, intent, "Tôi chỉ hỗ trợ thông tin và quyết định trong quy trình thu hồi nợ của MSB trên dữ liệu mô phỏng.", [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier}); result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "UNKNOWN":
        target = resolved_cif or cif
        if target:
            summary = (f"Tôi chưa hiểu rõ câu hỏi. Anh/Chị đang xem hồ sơ {target} — "
                       f"muốn xem tóm tắt, cách tính điểm, quyết định hay mô phỏng?")
        else:
            summary = ("Tôi chưa hiểu rõ câu hỏi. Anh/Chị có thể hỏi về ưu tiên hôm nay, "
                       "quyết định của một khách hàng, cách tính điểm, hoặc kiến thức thu hồi nợ.")
        result = _response(cif, "UNKNOWN", summary, [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier, "last_topic": ""})
        result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "TODAY_WORKLIST":
        return _today_worklist_response(cif, started, confidence, classifier, router_ms, timed_caller)

    if intent in ("SCORE_VALUE", "SCORE_BREAKDOWN"):
        target = resolved_cif or cif
        return _score_response(cif, target, intent, started, confidence, classifier, router_ms, timed_caller)

    if intent == "EXPLAIN_PRIORITY":
        target = resolved_cif or cif
        return _explain_priority_response(cif, target, started, confidence, classifier, router_ms, timed_caller)

    if intent == "CLARIFICATION":
        summary = ("Anh/Chị muốn: 1. mô phỏng khách không thực hiện cam kết hiện tại, "
                   "hay 2. hỏi quy trình xử lý chung?")
        result = _response(cif, "CLARIFICATION", summary, [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier, "pending_clarification": "NONPAYMENT"})
        result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "RETURN_TO_BASELINE":
        summary = ("Đã quay lại dữ liệu thực của hồ sơ. Các kết quả mô phỏng trước đó "
                   "không làm thay đổi quyết định gốc.")
        result = _response(cif, "RETURN_TO_BASELINE", summary, [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier})
        result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "SIMULATION_FOLLOWUP":
        summary = ("Kết quả chỉ thay đổi khi giả định làm thay đổi điều kiện mà Simulation Core "
                   "đang sử dụng. Với dữ liệu hiện tại, tôi không thể tự đề xuất hay bịa thêm biến; "
                   "Anh/Chị có thể thử một giả định được hỗ trợ như tiền vào 7 ngày hoặc trạng thái cam kết.")
        result = _response(cif, "SIMULATION_FOLLOWUP", summary, [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier})
        result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "ACTIVE_CIF_QUERY":
        target = resolved_cif or cif
        summary = f"Hiện tôi đang xử lý theo hồ sơ {target}." if target else "Hiện chưa có khách hàng nào được chọn."
        result = _response(cif, "ACTIVE_CIF_QUERY", summary, [], [], None, "LOCAL", timings, None)
        result["metadata"].update({"confidence": confidence, "classifier": classifier})
        result["metadata"]["total_ms"] = round((time.perf_counter()-started)*1000, 2); return result

    if intent == "KNOWLEDGE":
        if resolved_kind == "call":
            return _static_knowledge_response(cif, "KNOWLEDGE", semantics.CALL_TEXT, started, confidence, classifier, router_ms, "ROUTING_CALL_CBS")
        if resolved_kind == "cbs":
            return _static_knowledge_response(cif, "KNOWLEDGE", semantics.CBS_TEXT, started, confidence, classifier, router_ms, "ROUTING_CALL_CBS")
        if resolved_kind == "comparison":
            return _static_knowledge_response(cif, "KNOWLEDGE", semantics.CALL_CBS_COMPARISON, started, confidence, classifier, router_ms, "ROUTING_CALL_CBS")
        return _knowledge_response(cif, message, started, confidence, classifier, router_ms)

    tools: list[str] = []; tool_start = time.perf_counter()
    if intent == "SIMULATION":
        runtime = AgentRuntime(timed_caller, maas_client_from_env(timeout_seconds=8))
        incoming_changes = dict(resolved_changes)
        if not incoming_changes:
            incoming_changes = payload.get("changes", {}) if isinstance(payload.get("changes", {}), dict) else {}
        if not incoming_changes and isinstance(context.get("last_simulation_changes"), dict):
            incoming_changes = context["last_simulation_changes"]
        sim_cif = resolved_cif or cif
        result = runtime.invoke("SIMULATE", sim_cif, message, _simulation_changes(message, incoming_changes)).to_dict()
        tools = result.get("tools_used", []); path = "MAAS_GLM" if result.get("canonical_model") else "FALLBACK"
    elif intent == "DECISION_EXPLANATION":
        runtime = AgentRuntime(timed_caller, maas_client_from_env(timeout_seconds=8))
        explain_cif = resolved_cif or cif
        result = runtime.invoke("EXPLAIN", explain_cif, message).to_dict()
        tools = result.get("tools_used", []); path = "MAAS_GLM" if result.get("canonical_model") else "FALLBACK"
    elif intent == "ROUTE_PRIORITY":
        nba_envelope = _timed_call(timed_caller, "get_next_best_action", {"cif": cif}, tools, started)
        if not _tool_ok(nba_envelope):
            err = nba_envelope.get("error", {"code": "NOT_FOUND", "message": "Customer not found"})
            return _response(cif, intent, "Không tìm thấy quyết định cho khách hàng mô phỏng.", [], tools, None, "LOCAL", timings, err)
        nba = _tool_data(nba_envelope)
        route = semantics.map_route(nba.get("final_route"))
        channel = semantics.map_channel(nba.get("channel"))
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
