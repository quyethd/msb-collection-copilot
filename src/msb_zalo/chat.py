"""Zalo conversation routing and channel presentation.

This is a Zalo-only layer: it routes intents BEFORE applying any customer
context, keeps a bounded per-chat memory of routing hints, and renders Copilot
structured answers as plain concise Vietnamese text for the Zalo channel. The
shared Web Copilot and its response contract are not modified.
"""
from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable

from msb_agent.copilot import route_copilot
from msb_agent.llm import maas_client_from_env
from msb_agent.planner import plan_conversation, agent_first_enabled
from msb_agent import semantics as shared_semantics
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository

MAX_ZALO_TEXT = 2000
DEFAULT_DEMO_CIF = "SYN002846"

INTENTS = (
    "META_IDENTITY",
    "HELP",
    "CURRENT_CONTEXT",
    "TODAY_PRIORITIES",
    "RECOVERY_SCORE_EXPLANATION",
    "CUSTOMER_EXPLICIT",
    "SIMULATION",
    "KNOWLEDGE",
    "CONTEXTUAL_FOLLOWUP",
    "FALLBACK",
)

# V3 canonical NLU intent set (hybrid conversational copilot)
NLU_INTENTS = (
    "GREETING", "IDENTITY", "HELP", "TODAY_PRIORITIES", "TODAY_CALL_LIST",
    "CUSTOMER_SUMMARY", "CUSTOMER_DECISION", "CUSTOMER_SHOULD_CALL",
    "RECOVERY_SCORE", "RECOVERY_SCORE_EXPLANATION",
    "SIMULATION", "SIMULATION_FOLLOWUP", "KNOWLEDGE", "CURRENT_CONTEXT",
    "FOLLOWUP_WHY", "FOLLOWUP_WHAT_NEXT", "EXPLAIN_PRIORITY",
    "CLARIFICATION_RESPONSE", "UNKNOWN",
)

_NLU_TO_LEGACY: dict[str, str] = {
    "GREETING": "HELP", "IDENTITY": "META_IDENTITY", "HELP": "HELP",
    "TODAY_PRIORITIES": "TODAY_PRIORITIES", "TODAY_CALL_LIST": "TODAY_PRIORITIES",
    "CUSTOMER_SUMMARY": "CUSTOMER_EXPLICIT", "CUSTOMER_DECISION": "CUSTOMER_EXPLICIT",
    "CUSTOMER_SHOULD_CALL": "CUSTOMER_EXPLICIT",
    "RECOVERY_SCORE": "RECOVERY_SCORE_EXPLANATION",
    "RECOVERY_SCORE_EXPLANATION": "RECOVERY_SCORE_EXPLANATION",
    "SIMULATION": "SIMULATION", "SIMULATION_FOLLOWUP": "CONTEXTUAL_FOLLOWUP",
    "KNOWLEDGE": "KNOWLEDGE", "CURRENT_CONTEXT": "CURRENT_CONTEXT",
    "FOLLOWUP_WHY": "CONTEXTUAL_FOLLOWUP",
    "FOLLOWUP_WHAT_NEXT": "CONTEXTUAL_FOLLOWUP",
    "UNKNOWN": "FALLBACK",
}

_NLU_TOOL_MAP: dict[str, str] = {
    "CUSTOMER_SUMMARY": "get_customer_360",
    "CUSTOMER_DECISION": "get_next_best_action",
    "CUSTOMER_SHOULD_CALL": "get_next_best_action",
    "RECOVERY_SCORE": "get_recovery_opportunity",
    "RECOVERY_SCORE_EXPLANATION": "get_recovery_opportunity",
    "SIMULATION": "simulate_decision",
    "SIMULATION_FOLLOWUP": "simulate_decision",
    "TODAY_PRIORITIES": "get_next_best_action",
    "TODAY_CALL_LIST": "get_next_best_action",
}

_NLU_LOCAL_CONFIDENCE = 0.85

_NLU_CLARIFICATION_TEXT = (
    "Tôi chưa chắc Anh/Chị đang hỏi về hồ sơ nào. "
    "Vui lòng gửi CIF hoặc nói rõ muốn xem quyết định, điểm hay mô phỏng."
)

_IDENTITY_TEXT = (
    "Tôi là Trợ lý Thu hồi Nợ MSB bản demo. Tôi giúp xem quyết định, "
    "tóm tắt khách hàng, mô phỏng dữ liệu và giải thích kiến thức thu hồi nợ. "
    "Dữ liệu đều là mô phỏng."
)

_HELP_TEXT = (
    "Tao giúp được: giải thích quyết định (ví dụ 'Tại sao chưa cần gọi?'), "
    "tóm tắt khách hàng, mô phỏng (ví dụ 'Nếu tiền vào 7 ngày bằng 0 thì sao?'), "
    "và kiến thức thu hồi nợ (ví dụ 'CALL và CBS khác nhau thế nào?')."
)

_FALLBACK_TEXT = (
    "Tôi chưa hiểu câu hỏi này trong phạm vi trợ lý thu hồi nợ demo. Bạn có thể "
    "hỏi về quyết định của một khách hàng (ví dụ 'Tại sao hôm nay chưa cần gọi?'), "
    "mô phỏng khi dữ liệu thay đổi, hoặc kiến thức như 'CALL và CBS khác nhau "
    "thế nào?'."
)

_SECURITY_TEXT = (
    "Tôi không truy cập các khóa, mật khẩu hay thông tin bí mật hệ thống. Tôi chỉ "
    "hỗ trợ thông tin trong quy trình thu hồi nợ của bản demo."
)

_SIM_NO_CONTEXT_TEXT = (
    "Để mô phỏng, bạn chưa cho tôi biết khách hàng nào. Hãy hỏi kèm mã khách hàng, "
    "ví dụ 'Nếu tiền vào 7 ngày bằng 0 của SYN002846 thì sao?'."
)

_SCORE_NO_CONTEXT_TEXT = (
    "Bạn đang hỏi về điểm cơ hội thu hồi của khách hàng nào? Cho tôi mã hồ sơ "
    "(ví dụ SYN002846) để tôi giải thích cách tính."
)

_CURRENT_CONTEXT_MARKERS = (
    "cif nao", "cif hien tai", "khach nao", "khach hang nao", "dang noi den",
    "dang tra loi", "dang xu ly hô so", "hien dang hoi ve khach",
)

_TODAY_PRIORITIES_MARKERS = (
    "lam gi", "can lam", "phai lam", "can thao tac", "xem khach", "uu tien", "viec gi", "can xu ly",
    "noi bat", "diem dang chu y",
)

_SCORE_MARKERS = (
    "co hoi", "thu hoi", "diem tinh", "la gi", "bao nhieu", "tinh nhu the nao",
)

_ROUTE_VN = {
    "CALL": "Tuyến: CALL (gọi điện khi cần)",
    "CBS": "Tuyến: CBS (nhắc thanh toán và theo dõi cam kết)",
    "OTHER": "Tuyến: OTHER (xử lý khác)",
}

_CHANNEL_VN = {
    "CALL": "Gọi điện", "NONE": "Chưa cần liên hệ", "SMS": "Tin nhắn SMS",
    "ZALO": "Zalo", "EMAIL": "Email", "FIELD": "Lực lượng hiện trường",
}

_TREATMENT_VN = {
    "CALLBACK": "Gọi lại sau",
    "CONTACT": "Liên hệ khách hàng",
    "ESCALATE": "Chuyển bậc xử lý",
    "PARTIAL_PAYMENT": "Thu hồi một phần",
    "PTP_FOLLOW_UP": "Theo dõi cam kết thanh toán",
    "PTP_RECOVERY": "Xử lý cam kết không thực hiện",
    "REMIND": "Nhắc thanh toán",
    "VERIFY_CONTACT": "Xác minh thông tin liên hệ",
    "WAIT": "Tiếp tục theo dõi",
    "WAIT_SELF_CURE": "Chờ khách hàng tự thanh toán",
}

_SCORE_COMPONENT_VN = shared_semantics.SCORE_COMPONENT_VN

_RAW_WORD_VN = {
    "None": "chưa có", "null": "chưa có", "N/A": "chưa có", "NaN": "chưa có",
}

_ENUM_VN = {
    "WAIT_SELF_CURE": "Chờ khách hàng tự thanh toán",
    "CALL_SELF_CURE": "khách tự thanh toán",
    "CALL_DEFAULT": "liên hệ theo mặc định",
    "CONTACT": "Liên hệ khách hàng",
    "CALLBACK": "Gọi lại sau",
    "ESCALATE": "Chuyển bậc xử lý",
    "PARTIAL_PAYMENT": "Thu hồi một phần",
    "PTP_FOLLOW_UP": "Theo dõi cam kết thanh toán",
    "PTP_RECOVERY": "Xử lý cam kết không thực hiện",
    "REMIND": "Nhắc thanh toán",
    "VERIFY_CONTACT": "Xác minh thông tin liên hệ",
    "BROKEN": "bị phá vỡ",
    "OPEN": "đang mở",
    "PENDING": "đang chờ",
    "NONE": "chưa có",
    "PAYMENT": "thanh toán",
    "BEST_WINDOW": "khung giờ tốt nhất",
}

_REMOVE_BLOCK_RE = re.compile(
    r"^\s*(?:Tuyến[^:\n]*|Kenh|Kênh|Điểm cơ hội thu hồi|Diem co hoi thu hoi|Hành động hiện tại|Hanh dong hien tai)(?:[^:\n]*)[:\s][^\n]*$",
    flags=re.M,
)

_WHY_BARE_MARKERS = ("vi sao", "tai sao", "sao vay", "sao the", "vi gi", "ly do gi")

_PRONOUNS = ("ban", "may", "em", "anh", "chi", "cau", "tao", "minh", "chi minh")

_CALL_TEXT = shared_semantics.CALL_TEXT

_CBS_TEXT = shared_semantics.CBS_TEXT

_CALL_CBS_COMPARISON = shared_semantics.CALL_CBS_COMPARISON

_META_IDENTITY = frozenset({
    "ban la ai", "may la ai", "em la ai", "anh la ai", "chi la ai", "cau la ai",
    "ban la ai the", "may la ai the", "cau la ai the",
    "ban la gi", "may la gi", "ban la gi the",
    "ban lam gi", "ban lam gi the", "ban lam gi day",
    "ban lam viec gi", "ban lam viec gi day", "ban lam cong viec gi",
    "ban gioi thieu ve minh", "gioi thieu ban than", "ban gioi thieu mot chut",
})

_HELP = frozenset({
    "ban giup duoc gi", "ban giup gi", "ban giup duoc nhung gi",
    "ban co the giup gi", "ban co the giup duoc gi", "ban lam duoc gi",
    "ban lam duoc nhung gi", "giup duoc gi", "giup gi", "can giup do",
    "toi can giup", "tro giup", "giup toi", "huong dan su dung",
    "cach su dung", "lam sao de su dung", "lam the nao de su dung",
    "nhung gi ban lam duoc", "ban gioi thieu",
})

_GREETING_MARKERS = ("xin chao", "chao ban", "chao em", "chao chi", "chao anh")

_SECURITY_MARKERS = (
    ".env", "api key", "api_key", "llm api key", "llm_api_key", "mat khau",
    "password", "credentials", "reasoning content", "reasoning_content",
    "private prompt", "secret", "system prompt",
)

_KNOWLEDGE_MARKERS = (
    " la gi", "la gi vay", "la gi the", "de lam gi", "lam gi de", "dong vai tro",
    "khac nhau the nao", "khac nhau gi", "khac nhau giua", "khac nhau nhu the nao",
    "nam o dau", "chay o dau", "duoc tinh nhu the nao", "duoc tinh the nao",
    "tu quyet dinh", "ai quyet dinh", "quyen quyet dinh", "quyet dinh gi",
    "lien quan gi", "lien quan the nao", "nghia la", "la nhu the nao",
    "gom nhung gi", "gom nhung thanh phan gi", "co y nghia gi",
)

_SIMULATION_MARKERS = (
    "neu ", "neu nhu", "gia su", "mo phong", "tinh huong", "what if", "thay doi",
)

_FOLLOWUP_MARKERS = (
    "vi sao", "tai sao", "sao vay", "sao the", "vay nen lam gi", "toi nen lam gi",
    "nen lam gi", "thi sao", "khach nay", "con khach", "the con", "cu the hon",
    "noi ro hon", "nghia la sao",
)

_CIF_RE = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b", re.IGNORECASE)

_CITATION_RE = re.compile(r"\s*\[\d+(?:[,.\s-]+\d+)*\]")

_APPROVED_CHANNEL_VN = {
    "CALL": "Gọi điện", "SMS": "Tin nhắn SMS", "ZALO": "Zalo", "EMAIL": "Email",
    "FIELD": "Lực lượng hiện trường", "NONE": "Chưa cần liên hệ",
}

_KIND_FOR_INTENT = {
    "DECISION_EXPLANATION": "decision",
    "CUSTOMER_SUMMARY": "customer_summary",
    "CASHFLOW": "cashflow",
    "PTP": "ptp",
    "ROUTE_PRIORITY": "route",
    "SIMULATION": "simulation",
    "KNOWLEDGE": "knowledge",
    "GREETING_HELP": "help",
    "OUT_OF_SCOPE": "fallback",
    "AMBIGUOUS_FOLLOWUP": "fallback",
    "CURRENT_CONTEXT": "context",
    "TODAY_PRIORITIES": "today",
    "RECOVERY_SCORE_EXPLANATION": "score",
}


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(char for char in normalized if not unicodedata.combining(char))
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normalize(value: str) -> str:
    text = _plain(value)
    text = re.sub(r"\bdc\b", "duoc", text)
    text = re.sub(r"\bđc\b", "duoc", text)
    text = re.sub(r"\bntn\b", "nhu the nao", text)
    text = text.replace("vi sai", "vi sao")
    text = re.sub(r"\bcac tinh\b", "cach tinh", text)
    text = re.sub(r"\btao ngay\b", "tao nay", text)
    text = re.sub(r"\bhnay\b", "hom nay", text)
    text = re.sub(r"^nay\b", "hom nay", text)
    text = re.sub(r"\b(?:lam|lm) j\b", "lam gi", text)
    text = text.replace("/", " ")
    text = re.sub(r"[?!.,;:]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_pronoun(text: str) -> str:
    for pronoun in _PRONOUNS:
        if text == pronoun or text.startswith(pronoun + " "):
            stripped = text[len(pronoun):].strip()
            return stripped
    return text


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _match_phrases(text: str, phrases: frozenset[str]) -> bool:
    for phrase in phrases:
        if text == phrase or text.startswith(phrase + " "):
            return True
    return False


def _is_greeting(text: str) -> bool:
    if text in ("chao", "hello", "hi", "alo", "xin chao"):
        return True
    return any(text.startswith(marker + " ") for marker in _GREETING_MARKERS)


def _call_cbs_kind(text: str) -> str | None:
    has_call = "call" in text
    has_cbs = "cbs" in text
    concept = _has_any(text, ("la gi", "la gi vay", "la gi the", "nghia la", "de lam gi", "khac nhau", "khac nhau giua", "thi sao", "sao"))
    if has_call and has_cbs and (concept or _has_any(text, ("khac nhau", "so sanh"))):
        return "comparison"
    if has_call and concept:
        return "call"
    if has_cbs and (concept or _has_any(text, ("khac nhau", "so sanh"))):
        return "cbs"
    return None


def _extract_cif(message: str) -> str | None:
    """Extract a CIF without making broad fuzzy corrections.

    ``sny`` is the one-character transcription error observed in the production
    corpus; its format is otherwise unambiguous, so correcting that prefix does
    not select between customers. Other malformed identifiers stay unresolved.
    """
    matched = _CIF_RE.search(message)
    if matched:
        return matched.group(0).upper()
    typo = re.search(r"\bSNY(\d{6})\b", message, re.IGNORECASE)
    return f"SYN{typo.group(1)}" if typo else None


def _extract_changes(text: str) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    inflow_phrases = (
        "tien vao 7 ngay", "dong tien 7 ngay", "tien trong 7 ngay",
        "co tien trong 7 ngay", "dong tien trong 7 ngay", "tien vao 7 nay",
        "tien vao tuan nay", "co tien vao tuan nay", "dong tien tuan nay",
        "co tien trong tuan", "tien trong tuan nay",
    )
    if any(phrase in text for phrase in inflow_phrases) and any(
        token in text for token in ("bang 0", "khong co tien", "khong ve tien", "bang khong", "la 0")
    ):
        changes["inflow_7d"] = 0
    if "cam ket" in text and any(token in text for token in ("pha vo", "bi pha", "khong thuc hien")):
        changes["ptp_state"] = "BROKEN"
    return changes


def _format_vnd(value: Any) -> str:
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return str(value)
    if amount == 0:
        return "0 đồng"
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} tỷ đồng"
    if amount >= 1_000_000:
        return f"{amount // 1_000_000} triệu đồng"
    return f"{amount:,} đồng".replace(",", ".")


def _strip_markdown(value: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    text = re.sub(r"^\s{0,3}#{1,6}[ \t]+", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.M)
    text = text.replace("**", "").replace("`", "").replace("*", "")
    return text.strip()


def _strip_citations(value: str) -> str:
    return _CITATION_RE.sub("", value).strip()


def _clean_blank_lines(value: str) -> str:
    lines = [line.strip() for line in value.splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _fit(value: str, limit: int = MAX_ZALO_TEXT) -> str:
    text = re.sub(r"[ \t]+", " ", value).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    candidates = [position for position in (cut.rfind(". "), cut.rfind("。"), cut.rfind("\n")) if position > 0]
    if candidates:
        cut = cut[: max(candidates) + 1]
    return cut.rstrip() + "…"


_LATENCY_LOCK = threading.Lock()
_LATENCY: dict[str, list[float]] = {}
_LATENCY_REMOTE: dict[str, bool] = {}


def _record_latency(label: str, seconds: float, remote_call: bool) -> None:
    with _LATENCY_LOCK:
        bucket = _LATENCY.setdefault(label, [])
        bucket.append(seconds * 1000.0)
        del bucket[:-500]
        _LATENCY_REMOTE[label] = _LATENCY_REMOTE.get(label, False) or bool(remote_call)


def latency_stats() -> dict[str, dict[str, Any]]:
    """Per-intent latency summary in milliseconds (reporting only)."""
    with _LATENCY_LOCK:
        items = {label: list(values) for label, values in _LATENCY.items()}
        remote = dict(_LATENCY_REMOTE)
    summary: dict[str, dict[str, Any]] = {}
    for label, values in items.items():
        if not values:
            continue
        ordered = sorted(values)
        count = len(ordered)
        total = sum(ordered)
        summary[label] = {
            "count": count,
            "total_ms": round(total, 1),
            "min_ms": round(ordered[0], 1),
            "median_ms": round(ordered[count // 2], 1),
            "avg_ms": round(total / count, 1),
            "p95_ms": round(ordered[min(count - 1, int(count * 0.95))], 1),
            "max_ms": round(ordered[-1], 1),
            "remote_call": bool(remote.get(label)),
        }
    return summary


_LOCAL_INTENTS = frozenset({
    "META_IDENTITY", "HELP", "CURRENT_CONTEXT", "TODAY_PRIORITIES",
    "RECOVERY_SCORE_EXPLANATION", "GREETING_HELP",
})


def build_morning_brief(repository: ToolRepository) -> dict[str, Any]:
    """Deterministic morning priority shared by the chat and morning-brief flows."""
    rows = repository.portfolio()
    scored = sorted(rows, key=lambda row: (-int(row.get("recovery_opportunity_score", 0)), row["cif"]))
    # Top-5 decisions for display
    top_decisions = [invoke_tool("get_next_best_action", {"cif": row["cif"]}, repository=repository)
                     for row in scored[:5]]
    by_cif = {item["data"]["cif"]: item["data"] for item in top_decisions if item.get("ok") and item.get("data")}
    # Count CALL+NONE across the FULL portfolio, not just top-5
    call_no_now = 0
    for row in rows:
        if row.get("final_route") != "CALL":
            continue
        nba = invoke_tool("get_next_best_action", {"cif": row["cif"]}, repository=repository)
        if nba.get("ok") and nba.get("data", {}).get("channel") == "NONE":
            call_no_now += 1
    top = scored[:3]
    lines = ["☀️ Trợ lý Thu hồi Nợ — Ưu tiên hôm nay", "", "Danh mục demo:",
             f"• {len(rows)} hồ sơ có quyết định từ hệ thống",
             f"• {call_no_now} hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay", "", "Top cơ hội cần xem:"]
    for row in top:
        decision = by_cif.get(row["cif"])
        treatment_label = _TREATMENT_VN.get(decision["treatment"], "Theo quyết định hệ thống") if decision else "Theo quyết định hệ thống"
        lines.append(f"• {row['cif']} · Điểm {row.get('recovery_opportunity_score', 0)} · {treatment_label}")
    lines += ["", "Bạn có thể trả lời tin nhắn này để hỏi Trợ lý Thu hồi Nợ."]
    text = "\n".join(lines)
    if len(text) > MAX_ZALO_TEXT:
        raise ValueError("Morning brief exceeds the supported Zalo text limit")
    return {"text": text, "portfolio_count": len(rows), "call_route_no_call_now": call_no_now,
            "top_cifs": [row["cif"] for row in top], "synthetic_data": True}


def _render_sections(response: dict[str, Any]) -> str | None:
    sections = response.get("sections")
    if not isinstance(sections, list) or not sections:
        return None
    summary = response.get("summary")
    lines: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or "").strip()
        if title.casefold() in ("nguồn tham khảo", "nguon tham khao"):
            continue
        body = section.get("content")
        items = section.get("items")
        fragment = None
        if isinstance(body, str) and body.strip():
            fragment = body
        elif isinstance(items, list) and items:
            fragment = " ".join(str(item) for item in items if item and str(item).strip())
        if not fragment:
            continue
        if summary and isinstance(summary, str) and fragment.strip() == summary.strip():
            continue
        clean = _strip_citations(_strip_markdown(fragment))
        if not clean:
            continue
        heading = title.rstrip(" ?!.:;")
        lines.append(f"{heading}: {clean}" if heading else clean)
    return "\n".join(lines) if lines else None


def _render_summary(response: dict[str, Any]) -> str:
    summary = response.get("summary")
    return _strip_citations(_strip_markdown(str(summary if isinstance(summary, str) else ""))).strip()


def render_zalo_text(response: dict[str, Any]) -> str:
    intent = str(response.get("question_intent") or "")
    if intent == "KNOWLEDGE":
        answer = response.get("answer") or response.get("summary")
        text = _strip_citations(_strip_markdown(str(answer or ""))).strip()
        sources = response.get("sources")
        names: list[str] = []
        if isinstance(sources, list):
            for source in sources[:3]:
                if not isinstance(source, dict):
                    continue
                title = str(source.get("title") or "").strip()
                section = str(source.get("section") or "").strip()
                name = f"{title} — {section}" if title and section else title or section
                if name:
                    names.append(name[:140])
        if names:
            text = f"{text}\nNguồn: {'; '.join(names)}" if text else f"Nguồn: {'; '.join(names)}"
    else:
        text = _render_sections(response)
        if text is None:
            text = _render_summary(response)
    return _clean_blank_lines(_fit(text))


def _append_line(text: str, line: str) -> str:
    if not line:
        return text
    return f"{text}\n{line}".strip() if text else line


@dataclass
class _Memory:
    last_intent: str = ""
    last_cif: str = ""
    last_answer_kind: str = ""
    last_path: str = ""
    previous_user_question: str = ""
    last_decision_context: dict[str, Any] | None = None
    last_score_context: dict[str, Any] | None = None
    last_simulation_context: dict[str, Any] | None = None
    active_cif: str = ""
    last_actionable_intent: str = ""
    previous_cif: str = ""
    opener_sent: bool = False
    previous_user_message: str = ""
    last_topic: str = ""
    pending_clarification: str = ""
    last_worklist: list[str] | None = None
    last_tool_context: dict[str, Any] | None = None
    last_response_kind: str = ""
    last_message_id: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "last_intent": self.last_intent,
            "last_cif": self.last_cif,
            "last_answer_kind": self.last_answer_kind,
            "last_path": self.last_path,
            "previous_user_question": self.previous_user_question,
            "last_decision_context": dict(self.last_decision_context or {}),
            "last_score_context": dict(self.last_score_context or {}),
            "last_simulation_context": dict(self.last_simulation_context or {}),
            "active_cif": self.active_cif,
            "last_actionable_intent": self.last_actionable_intent,
            "previous_cif": self.previous_cif,
            "opener_sent": self.opener_sent,
            "previous_user_message": self.previous_user_message,
            "last_topic": self.last_topic,
            "pending_clarification": self.pending_clarification,
            "last_worklist": list(self.last_worklist or []),
            "last_tool_context": dict(self.last_tool_context or {}),
            "last_response_kind": self.last_response_kind,
            "last_message_id": self.last_message_id,
        }


@dataclass
class _Intent:
    label: str
    direct: str | None = None
    cif: str | None = None
    changes: dict[str, Any] | None = None
    kind: str = ""


@dataclass
class NLUResult:
    intent: str
    cif: str | None = None
    entities: dict[str, Any] | None = None
    use_context: bool = True
    confidence: float = 0.0
    needs_clarification: bool = False


_TODAY_CALL_MARKERS = (
    "goi ai", "goi truoc", "call cho ai", "call ai", "nen goi", "phai call", "phai goi",
)

_SHOULD_CALL_MARKERS = (
    "co can goi", "can goi khong", "co nen goi", "nen goi khong", "can call", "co can call",
)

_FOLLOWUP_WHAT_NEXT_MARKERS = (
    "gio lam gi", "lam gi tiep", "the gio lam gi", "gio thi lam gi", "bay gio lam gi",
    "nay lam gi", "lam gi bay gio",
)

_SCORE_EXPLAIN_MARKERS = (
    "sao cao", "sao thap", "cao the", "thap the", "diem cao", "diem thap",
    "vi sao lai", "tai sao lai",
)

_SCORE_AMBIGUOUS_MARKERS = (
    "diem tinh sao", "diem tinh the nao", "diem tinh ra sao", "diem sao lai",
    "sao diem vay", "sao diem lai", "vi sao diem nay", "vi sao diem lai",
)

_TINH_DIEM_MARKERS = ("tinh diem", "cach tinh diem")

_BARE_SIMULATION_MARKERS = ("khong co tien vao tuan nay", "khong co tien trong tuan", "tuan nay khong co tien")

_COMPARE_CUSTOMERS_MARKERS = (
    "uu tien hon", "thang nao dang uu tien", "ai nen goi truoc", "ho so nao uu tien hon",
)


def _ask_knowledge(message: str, cif: str, caller: Callable[[str, dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    response = route_copilot(
        {"cif": cif, "message": message, "conversation_context": {"active_cif": cif}},
        caller,
    )
    if response.get("status") != "success":
        raise RuntimeError("Copilot knowledge could not answer the Zalo message")
    return response


def _is_bare_why(norm: str) -> bool:
    core = norm
    for prefix in ("em oi", "ban oi", "chi oi", "anh oi", "em", "ban", "may", "de"):
        stripped = core[len(prefix):].strip()
        if core.startswith(prefix + " ") and stripped and len(stripped) < len(core):
            core = stripped
    if len(core) > 18:
        return False
    return any(core == marker or core.startswith(marker + " ") for marker in _WHY_BARE_MARKERS)


def _sanitize_answer(text: str) -> str:
    value = text or ""
    if not value:
        return value
    value = re.sub(
        r"Cam kết thanh toán:\s*(?:None|NONE|null)\s*\.?",
        "Cam kết thanh toán: Hiện chưa có cam kết thanh toán.",
        value,
        flags=re.IGNORECASE,
    )
    for raw, word in _RAW_WORD_VN.items():
        value = re.sub(rf"\b{raw}\b", word, value)
    for raw, word in _ENUM_VN.items():
        value = re.sub(rf"\b{raw}\b", word, value)
    value = re.sub(r"^\s*\{[^{}\n]*\}\s*$", "", value, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _action_block(decision: dict[str, Any]) -> str:
    bits: list[str] = []
    route = decision.get("route")
    treatment = decision.get("treatment")
    channel = decision.get("channel")
    score = decision.get("score")
    if route:
        bits.append(_ROUTE_VN.get(route, f"Tuyến: {route}"))
    if treatment:
        bits.append(f"Hành động hiện tại: {_TREATMENT_VN.get(treatment, 'Theo quyết định hệ thống')}")
    if channel:
        bits.append(f"Kênh hôm nay: {_CHANNEL_VN.get(channel, 'Cần xác định')}")
    if score is not None:
        bits.append(f"Điểm cơ hội thu hồi: {score}")
    return "\n".join(bits)


class ZaloConversation:
    """Bounded per-chat routing memory. Never a business authority."""

    def __init__(self, repository: Any):
        self.repository = repository
        self._memory = _Memory()
        self._lock = threading.Lock()
        self._last_nlu: NLUResult | None = None

    def _caller(self) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
        repository = self.repository
        return lambda name, args: invoke_tool(name, args, repository=repository)

    def reset(self) -> None:
        with self._lock:
            self._memory = _Memory()
            self._last_nlu = None

    def memory(self) -> dict[str, Any]:
        with self._lock:
            return self._memory.snapshot()

    def respond(self, message: str, conversation_context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = (message or "").strip()
        if not isinstance(text, str):
            text = str(text)
        with self._lock:
            return self._respond_locked(text, conversation_context)

    def _respond_locked(self, message: str, conversation_context: dict[str, Any] | None) -> dict[str, Any]:
        start = time.monotonic()
        if not self._memory.last_intent:
            self._seed(conversation_context)
        norm = _normalize(message)
        intent = self._classify(message, norm)
        answer = intent.direct
        question_intent = intent.label
        path = "LOCAL"
        cif: str | None = intent.cif
        response: dict[str, Any] | None = None
        remote_call = False
        if answer is None:
            if intent.kind == "call_list":
                answer = self._call_list_answer()
                question_intent = "TODAY_CALL_LIST"
            elif intent.kind == "should_call":
                if not cif:
                    answer = _NLU_CLARIFICATION_TEXT
                    question_intent = "AMBIGUOUS_FOLLOWUP"
                else:
                    self._memory.last_cif = cif
                    self._memory.active_cif = cif
                    answer = self._should_call_answer(cif)
                    question_intent = "CUSTOMER_SHOULD_CALL"
            elif intent.kind == "compare":
                answer = self._compare_customers_answer(cif or self._memory.last_cif,
                                                        self._memory.previous_cif)
                question_intent = "CUSTOMER_COMPARE"
            elif intent.kind == "decision":
                target = cif or self._memory.last_cif
                if not target:
                    answer = _NLU_CLARIFICATION_TEXT
                    question_intent = "AMBIGUOUS_FOLLOWUP"
                else:
                    decision = self._decision_enrich(target)
                    if decision:
                        answer = _append_line(f"Quyết định hiện tại cho {target}:", _action_block(decision))
                        question_intent = "DECISION_EXPLANATION"
                    else:
                        answer = f"Không tìm thấy quyết định cho hồ sơ {target}."
                        question_intent = "AMBIGUOUS_FOLLOWUP"
            elif intent.kind == "what_next":
                if not cif:
                    answer = _NLU_CLARIFICATION_TEXT
                    question_intent = "AMBIGUOUS_FOLLOWUP"
                else:
                    answer = self._what_next_answer(cif)
                    question_intent = "FOLLOWUP_WHAT_NEXT"
                    self._memory.last_decision_context = self._decision_enrich(cif)
            elif intent.kind == "priority":
                if not cif:
                    answer = "Anh/Chị vui lòng cho tôi mã CIF để giải thích ưu tiên."
                    question_intent = "AMBIGUOUS_FOLLOWUP"
                else:
                    decision = self._decision_enrich(cif)
                    if decision:
                        treatment = _TREATMENT_VN.get(decision.get("treatment"), "theo quyết định hệ thống")
                        answer = (f"Hồ sơ {cif} nằm trong danh sách cần xem hôm nay theo dữ liệu mô phỏng. "
                                  f"Điểm cơ hội thu hồi hiện tại là {decision.get('score')}/100; "
                                  f"hành động hệ thống đề xuất là {treatment.lower()}. "
                                  "Thứ tự ưu tiên chi tiết chỉ được khẳng định khi nguồn worklist cung cấp.")
                        question_intent = "EXPLAIN_PRIORITY"
                    else:
                        answer = f"Không tìm thấy hồ sơ {cif} trong dữ liệu mô phỏng."
                        question_intent = "AMBIGUOUS_FOLLOWUP"
            elif intent.kind == "clarify_nonpayment":
                answer = ("Anh/Chị muốn: 1. mô phỏng khách không thực hiện cam kết hiện tại, "
                          "hay 2. hỏi quy trình xử lý chung?")
                question_intent = "AMBIGUOUS_FOLLOWUP"
                self._memory.pending_clarification = "NONPAYMENT"
            elif intent.kind == "clarification_response":
                if self._memory.pending_clarification == "NONPAYMENT":
                    if norm in ("mo phong", "quyet dinh"):
                        cif = self._memory.last_cif
                        if cif:
                            intent = _Intent("SIMULATION", cif=cif, changes={"ptp_state": "BROKEN"}, kind="simulation")
                            self._memory.pending_clarification = ""
                            answer = self._replay_new_simulation(cif, intent.changes)
                            question_intent = "SIMULATION"
                        else:
                            answer = _SIM_NO_CONTEXT_TEXT
                            question_intent = "SIMULATION"
                    else:
                        self._memory.pending_clarification = ""
                        answer = ("Với quy trình xử lý chung, Trợ lý chỉ có thể giải thích theo tài liệu "
                                  "nghiệp vụ; Anh/Chị có thể gửi CIF để xem quyết định hiện tại.")
                        question_intent = "KNOWLEDGE"
                else:
                    answer = _FALLBACK_TEXT
            elif intent.label == "KNOWLEDGE":
                response = _ask_knowledge(message, self._memory.last_cif or DEFAULT_DEMO_CIF, self._caller())
                answer = render_zalo_text(response)
                question_intent = "KNOWLEDGE"
                path = response.get("metadata", {}).get("path", "RAG_QWEN")
                cif = None
                remote_call = True
            elif intent.label == "TODAY_PRIORITIES":
                brief = build_morning_brief(self.repository)
                lines = [
                    "Ưu tiên hôm nay (dữ liệu mô phỏng):",
                    f"• {brief['portfolio_count']} hồ sơ có quyết định từ hệ thống",
                    f"• {brief['call_route_no_call_now']} hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay",
                    "", "Top 3 hồ sơ cần xem:",
                ]
                for index, row in enumerate(brief["top_cifs"], start=1):
                    lines.append(f"{index}. {row}")
                lines.append("Điểm cơ hội và hành động đề xuất của từng hồ sơ đã có trong bảng tin sáng.")
                answer = "\n".join(lines)
                question_intent = "TODAY_PRIORITIES"
                self._memory.last_worklist = list(brief["top_cifs"])
            elif intent.label == "CURRENT_CONTEXT":
                answer = self._current_context_answer()
                question_intent = "CURRENT_CONTEXT"
            elif intent.label == "RECOVERY_SCORE_EXPLANATION" and not cif:
                answer = _SCORE_NO_CONTEXT_TEXT
                question_intent = "RECOVERY_SCORE_EXPLANATION"
            elif intent.label == "RECOVERY_SCORE_EXPLANATION":
                self._memory.last_cif = cif
                answer = self._score_explanation(cif)
                question_intent = "RECOVERY_SCORE_EXPLANATION"
                self._memory.last_decision_context = self._decision_enrich(cif)
                self._memory.last_score_context = self._score_context(cif)
            elif intent.label == "SIMULATION" and not cif:
                answer = _SIM_NO_CONTEXT_TEXT
            elif (
                intent.label == "CONTEXTUAL_FOLLOWUP"
                and _is_bare_why(norm)
                and self._memory.last_answer_kind == "decision"
                and self._memory.last_cif == (cif or self._memory.last_cif)
            ):
                decision = self._decision_enrich(self._memory.last_cif or cif)
                if decision:
                    answer = (f"Vì sao hồ sơ {self._memory.last_cif or cif} như vậy: "
                              f"quyết định hiện tại do hệ thống tính toán từ hồ sơ demo.")
                    question_intent = "DECISION_EXPLANATION"
                    path = "LOCAL"
                else:
                    answer = self._why_clarification()
                    question_intent = "AMBIGUOUS_FOLLOWUP"
            elif (
                intent.label == "CONTEXTUAL_FOLLOWUP"
                and _is_bare_why(norm)
                and self._memory.last_answer_kind == "score"
                and self._memory.last_score_context
                and self._memory.last_score_context.get("cif") == self._memory.last_cif
            ):
                replay_score = self._score_explanation(self._memory.last_cif)
                if replay_score and replay_score != _SCORE_NO_CONTEXT_TEXT:
                    answer = replay_score
                    question_intent = "RECOVERY_SCORE_EXPLANATION"
                    path = "LOCAL"
                else:
                    answer = self._why_clarification()
                    question_intent = "AMBIGUOUS_FOLLOWUP"
                    path = "LOCAL"
            elif (
                intent.label == "CONTEXTUAL_FOLLOWUP"
                and _is_bare_why(norm)
                and self._memory.last_answer_kind == "simulation"
                and self._memory.last_simulation_context
                and self._simulation_context_matches(cif or self._memory.last_cif)
            ):
                replay = self._memory.last_simulation_context
                answer = self._replay_simulation(replay.get("cif") or self._memory.last_cif or cif,
                                                 replay.get("changes") or {})
                question_intent = "SIMULATION"
                path = "LOCAL"
            elif (
                intent.label == "CONTEXTUAL_FOLLOWUP"
                and _is_bare_why(norm)
            ):
                answer = self._why_clarification()
                question_intent = "AMBIGUOUS_FOLLOWUP"
                path = "LOCAL"
            else:
                payload = self._copilot_payload(message, intent, cif)
                response = route_copilot(payload, self._caller())
                remote_call = True
                if response.get("status") != "success":
                    raise RuntimeError("Copilot could not answer the Zalo message")
                answer = render_zalo_text(response)
                question_intent = str(response.get("question_intent") or intent.label)
                path = response.get("metadata", {}).get("path", "LOCAL")
                cif = str(response.get("cif") or cif or "")
        if question_intent == "DECISION_EXPLANATION":
            decision = self._decision_enrich(cif)
            if decision:
                answer = _append_line(_clean_blank_lines(_REMOVE_BLOCK_RE.sub("", answer or "")), _action_block(decision))
        if intent.label == "SIMULATION":
            self._memory.last_simulation_context = {
                "cif": cif or "",
                "changes": dict(intent.changes or _extract_changes(norm)),
            }
            self._memory.pending_clarification = ""
        if question_intent == "SIMULATION" and intent.label == "CUSTOMER_EXPLICIT":
            self._memory.last_simulation_context = {
                "cif": cif or "",
                "changes": dict(intent.changes or _extract_changes(norm)),
            }
        if question_intent == "SIMULATION" and self._memory.last_simulation_context:
            replay = self._replay_simulation(
                self._memory.last_simulation_context.get("cif") or cif or "",
                self._memory.last_simulation_context.get("changes") or {},
            )
            if replay and replay != self._why_clarification():
                answer = replay
        if intent.label == "KNOWLEDGE":
            self._memory.last_topic = "ROUTING_CALL_CBS" if (
                intent.direct in (_CALL_TEXT, _CBS_TEXT, _CALL_CBS_COMPARISON)
            ) else "KNOWLEDGE"
        answer_kind = _KIND_FOR_INTENT.get(question_intent, intent.kind or "fallback")
        if answer_kind in ("identity", "help", "knowledge"):
            question_intent = intent.label
        answer = _sanitize_answer(answer or "")
        self._update_memory(message, intent, question_intent, answer_kind, cif or intent.cif, path, answer or "")
        _record_latency(intent.label, time.monotonic() - start, remote_call)
        nlu_intent = self._last_nlu.intent if self._last_nlu else "UNKNOWN"
        confidence = self._last_nlu.confidence if self._last_nlu else 0.0
        if question_intent == "SIMULATION" and nlu_intent == "FOLLOWUP_WHY":
            nlu_intent = "SIMULATION_FOLLOWUP"
        elif nlu_intent == "RECOVERY_SCORE" and answer and "khách hàng nào" in answer:
            nlu_intent = "RECOVERY_SCORE"
        return {
            "text": answer or "Tôi chưa thể trả lời câu hỏi này.",
            "intent": intent.label,
            "question_intent": question_intent,
            "nlu_intent": nlu_intent,
            "confidence": round(float(confidence), 3),
            "path": path,
            "answer_kind": answer_kind,
            "cif": cif or intent.cif or None,
        }

    def _current_context_answer(self) -> str:
        cif = self._memory.last_cif
        if not cif:
            return "Hiện chưa có khách hàng nào được chọn trong cuộc trò chuyện này."
        kind = self._memory.last_answer_kind
        hint = {
            "decision": "Nội dung gần nhất là về quyết định xử lý.",
            "simulation": "Nội dung gần nhất là về mô phỏng.",
            "customer_summary": "Nội dung gần nhất là tổng quan hồ sơ.",
            "score": "Nội dung gần nhất là điểm cơ hội thu hồi.",
        }.get(kind, "")
        base = f"Hiện tôi đang xử lý theo hồ sơ {cif}."
        return f"{base} {hint}".strip() if hint else base

    def _why_clarification(self) -> str:
        first = (f"vì sao hồ sơ {self._memory.last_cif} chưa cần gọi"
                 if self._memory.last_cif else "vì sao một hồ sơ chưa cần gọi")
        second = self._why_score_question()
        return (f"Bạn muốn hỏi \"{first}\" hay \"{second}\"? "
                f"Cho tôi biết thêm ý cụ thể hơn để tôi trả lời chính xác.")

    def _why_score_question(self) -> str:
        """Reference the current CIF's score only, never a stale previous-CIF value."""
        if not self._memory.last_cif:
            return "vì sao điểm cơ hội thu hồi là bao nhiêu"
        context = self._memory.last_score_context or {}
        if context.get("cif") == self._memory.last_cif:
            return f"vì sao điểm cơ hội thu hồi là {context.get('score')}"
        try:
            envelope = invoke_tool(
                "get_recovery_opportunity",
                {"cif": self._memory.last_cif},
                repository=self.repository,
            )
            data = envelope.get("data") or {}
            if envelope.get("ok") and data.get("recovery_opportunity_score") is not None:
                self._memory.last_score_context = {
                    "cif": self._memory.last_cif,
                    "score": data.get("recovery_opportunity_score"),
                }
                return f"vì sao điểm cơ hội thu hồi là {data.get('recovery_opportunity_score')}"
        except Exception:
            pass
        return f"vì sao điểm cơ hội thu hồi của {self._memory.last_cif} là bao nhiêu"

    def _simulation_context_matches(self, cif: str | None) -> bool:
        """Simulation context is only used when it was produced for the active CIF."""
        context = self._memory.last_simulation_context or {}
        return bool(context.get("cif")) and context.get("cif") == (cif or self._memory.last_cif)

    def _replay_simulation(self, cif: str, changes: dict[str, Any]) -> str:
        if not cif or not changes:
            return self._why_clarification()
        if not self._simulation_context_matches(cif):
            return self._why_clarification()
        try:
            envelope = invoke_tool("simulate_decision", {"cif": cif, "changes": dict(changes)},
                                   repository=self.repository)
        except Exception:
            return self._why_clarification()
        data = envelope.get("data") or {}
        if not envelope.get("ok") or not isinstance(data, dict):
            return self._why_clarification()

        def _field_label(field: str) -> str:
            return {
                "treatment": "Hành động đề xuất",
                "channel": "Kênh xử lý",
                "when": "Thời điểm xử lý",
                "recovery_opportunity_score": "Điểm cơ hội thu hồi",
                "reason_code": "Lý do quyết định",
                "final_route": "Tuyến xử lý",
                "rule_id": "Mã quy tắc",
                "objective": "Mục tiêu",
                "inflow_7d": "Tiền vào 7 ngày gần nhất",
                "net_cashflow_30d": "Dòng tiền ròng 30 ngày",
                "ptp_state": "Trạng thái cam kết thanh toán",
                "promise_date": "Ngày cam kết thanh toán",
                "source_next_action_date": "Ngày dự kiến xử lý tiếp theo",
                "latest_business_outcome": "Kết quả tương tác gần nhất",
            }.get(field, field)

        def _value_label(field: str, value: Any) -> str:
            if value is None:
                return "—"
            if field == "treatment":
                return _TREATMENT_VN.get(str(value), str(value))
            if field == "channel":
                return _CHANNEL_VN.get(str(value), str(value))
            if field == "when" and isinstance(value, dict):
                wtype = value.get("type", "NONE")
                if wtype == "NONE":
                    return "Chưa cần xử lý ngay"
                if wtype == "BEST_WINDOW":
                    return f"Khung giờ tốt nhất {value.get('window')} ngày {value.get('date')}"
                if wtype == "SOURCE_DATETIME":
                    return f"Theo lịch nguồn: {value.get('datetime')}"
                if wtype == "SOURCE_DATE":
                    return f"Theo ngày cam kết: {value.get('date')}"
                if wtype == "TODAY":
                    return f"Hôm nay ({value.get('date')})"
                return str(wtype)
            if field in ("inflow_7d", "net_cashflow_30d"):
                return _format_vnd(value)
            if field == "ptp_state":
                return {
                    "NONE": "Chưa có cam kết", "OPEN": "Đang cam kết",
                    "KEPT": "Đã thực hiện cam kết", "PARTIAL": "Thanh toán một phần",
                    "BROKEN": "Không thực hiện cam kết",
                }.get(str(value), str(value))
            return str(value)

        def _describe(decision: dict[str, Any]) -> str:
            treatment = _TREATMENT_VN.get(decision.get("treatment"), "Theo quyết định hệ thống")
            rule_id = decision.get("rule_id")
            return f"{treatment} ({rule_id})" if rule_id else treatment

        lines = ["Kết quả mô phỏng:"]
        diff = data.get("diff") or []
        if not diff:
            lines.append("Không có thay đổi giữa trước và sau khi áp dụng điều kiện.")
        else:
            contained = False
            for entry in diff:
                if not isinstance(entry, dict):
                    continue
                field = entry.get("field")
                if field not in ("treatment", "rule_id", "channel", "when", "recovery_opportunity_score",
                                 "final_route", "reason_code", "objective"):
                    continue
                contained = True
                lines.append(f"{_field_label(field)}: {_value_label(field, entry.get('before'))} → "
                             f"{_value_label(field, entry.get('after'))}")
            if not contained:
                for entry in diff:
                    if not isinstance(entry, dict):
                        continue
                    field = entry.get("field")
                    lines.append(f"{_field_label(field)}: {_value_label(field, entry.get('before'))} → "
                                 f"{_value_label(field, entry.get('after'))}")
                lines.append("Quyết định giữ nguyên khi áp dụng điều kiện.")
        before = _describe(data.get("before") or {})
        after = _describe(data.get("after") or {})
        if before != after:
            lines.append(f"Hành động đề xuất thay đổi: {before} → {after}")
        return _sanitize_answer("\n".join(lines))

    def _replay_new_simulation(self, cif: str, changes: dict[str, Any]) -> str:
        """Run an explicitly selected clarification simulation once, then replay.

        The selected change is limited to Simulation Core's existing supported
        fields and remains bound to this CIF.
        """
        self._memory.last_simulation_context = {"cif": cif, "changes": dict(changes)}
        return self._replay_simulation(cif, changes)

    def _score_explanation(self, cif: str) -> str:
        try:
            envelope = invoke_tool("get_recovery_opportunity", {"cif": cif}, repository=self.repository)
        except Exception:
            return _SCORE_NO_CONTEXT_TEXT
        data = envelope.get("data") or {}
        if not envelope.get("ok") or not isinstance(data, dict):
            return _SCORE_NO_CONTEXT_TEXT
        score = data.get("recovery_opportunity_score")
        breakdown = data.get("component_breakdown")
        if score is None or not isinstance(breakdown, list):
            return _SCORE_NO_CONTEXT_TEXT
        lines = [f"Điểm cơ hội thu hồi của {cif} là {score}/100."]
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
            lines.append(f"• {_SCORE_COMPONENT_VN.get(name, str(name))}: {int(value)}"
                         + (f"/{maximum}" if maximum is not None else ""))
        if total:
            lines.append(f"Tổng hợp các thành phần: {total}.")
        return _sanitize_answer("\n".join(lines))

    def _score_context(self, cif: str) -> dict[str, Any]:
        """Score context is always bound to its owning CIF; never stored bare."""
        try:
            envelope = invoke_tool("get_recovery_opportunity", {"cif": cif}, repository=self.repository)
        except Exception:
            return {"cif": cif}
        data = envelope.get("data") or {}
        score = data.get("recovery_opportunity_score") if envelope.get("ok") else None
        return {"cif": cif, "score": int(score) if isinstance(score, (int, float)) else None}

    def _copilot_payload(self, message: str, intent: _Intent, cif: str | None) -> dict[str, Any]:
        context: dict[str, Any] = {"active_cif": cif or DEFAULT_DEMO_CIF}
        payload: dict[str, Any] = {"cif": cif or DEFAULT_DEMO_CIF, "message": message}
        if intent.label in ("CONTEXTUAL_FOLLOWUP", "SIMULATION"):
            if self._memory.last_intent:
                context["previous_intent"] = self._memory.last_intent
            if self._memory.previous_user_question:
                context["previous_user_question"] = self._memory.previous_user_question
            if self._memory.last_path:
                context["previous_path"] = self._memory.last_path
        if intent.changes:
            payload["changes"] = dict(intent.changes)
        if intent.label == "CONTEXTUAL_FOLLOWUP" and self._memory.last_simulation_context:
            changes = self._memory.last_simulation_context.get("changes") or {}
            if self._memory.last_simulation_context.get("cif") == self._memory.last_cif and changes:
                context["last_simulation_changes"] = dict(changes)
                payload["changes"] = dict(changes)
        payload["conversation_context"] = context
        return payload

    def _classify(self, message: str, norm: str) -> _Intent:
        if not norm:
            self._last_nlu = NLUResult(intent="UNKNOWN", confidence=1.0, needs_clarification=True)
            return _Intent("FALLBACK", direct=_FALLBACK_TEXT, kind="fallback")
        if agent_first_enabled():
            planner_intent = self._classify_with_planner(message, norm)
            if planner_intent is not None:
                return planner_intent
        nlu = self._fast_local_intent(message, norm)
        if nlu.confidence < _NLU_LOCAL_CONFIDENCE:
            nlu = self._nlu_interpret(message, norm, nlu)
        self._last_nlu = nlu
        return self._intent_from_nlu(message, nlu)

    def _classify_with_planner(self, message: str, norm: str) -> _Intent | None:
        """Agent-first classification using the shared semantic planner.

        Returns None when the planner fell back to the deterministic resolver,
        signaling the caller to use the existing Zalo NLU path (which includes
        Zalo-specific followup and context logic that the deterministic fallback
        alone does not cover).
        """
        context = {
            "active_cif": self._memory.active_cif or self._memory.last_cif,
            "last_cif": self._memory.last_cif,
            "previous_cif": self._memory.previous_cif,
            "last_intent": self._memory.last_intent,
            "last_topic": self._memory.last_topic,
            "pending_clarification": self._memory.pending_clarification,
            "last_simulation_context": self._memory.last_simulation_context,
        }
        if self._memory.last_worklist:
            context["last_worklist"] = self._memory.last_worklist
        plan = plan_conversation(message, context, channel="zalo")
        if plan.source == "deterministic_fallback":
            return None
        self._last_nlu = NLUResult(
            intent=plan.intent, cif=plan.cif, confidence=plan.confidence,
            needs_clarification=plan.needs_clarification,
        )
        return self._intent_from_plan(message, plan)

    def _intent_from_plan(self, message: str, plan) -> _Intent:
        """Map a StructuredPlan to the Zalo _Intent taxonomy."""
        cif = plan.cif
        changes = plan.changes or _extract_changes(_normalize(message))
        intent = plan.intent
        if intent in (shared_semantics.GREETING, shared_semantics.HELP):
            return _Intent("HELP", direct=f"Chào bạn. {_HELP_TEXT}", kind="help")
        if intent == shared_semantics.TODAY_WORKLIST:
            return _Intent("TODAY_PRIORITIES", kind="today")
        if intent == shared_semantics.KNOWLEDGE:
            kind = plan.kind or ""
            if kind == "comparison":
                return _Intent("KNOWLEDGE", direct=_CALL_CBS_COMPARISON, kind="knowledge")
            if kind == "call":
                return _Intent("KNOWLEDGE", direct=_CALL_TEXT, kind="knowledge")
            if kind == "cbs":
                return _Intent("KNOWLEDGE", direct=_CBS_TEXT, kind="knowledge")
            return _Intent("KNOWLEDGE", kind="knowledge")
        if intent == shared_semantics.KNOWLEDGE_GOVERNANCE:
            return _Intent("KNOWLEDGE", direct=shared_semantics.AI_GOVERNANCE_TEXT, kind="knowledge")
        if intent == shared_semantics.KNOWLEDGE_SCORE_SEMANTICS:
            return _Intent("KNOWLEDGE", direct=shared_semantics.SCORE_NOT_PROBABILITY_TEXT, kind="knowledge")
        if intent == shared_semantics.KNOWLEDGE_EVALUATION:
            return _Intent("KNOWLEDGE", kind="knowledge")
        if intent == shared_semantics.KNOWLEDGE_EVALUATION:
            return _Intent("KNOWLEDGE", kind="knowledge")
        if intent == shared_semantics.EXPLAIN_PRIORITY:
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="priority")
        if intent == shared_semantics.SCORE_VALUE:
            return _Intent("RECOVERY_SCORE_EXPLANATION", cif=cif, kind="score_ask")
        if intent == shared_semantics.SCORE_BREAKDOWN:
            return _Intent("RECOVERY_SCORE_EXPLANATION", cif=cif, kind="score")
        if intent == shared_semantics.CURRENT_CASE_SUMMARY:
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="customer")
        if intent == shared_semantics.CURRENT_CASE_ACTION:
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="decision")
        if intent == shared_semantics.SIMULATION:
            return _Intent("SIMULATION", cif=cif, changes=dict(changes), kind="simulation")
        if intent == shared_semantics.SIMULATION_FOLLOWUP:
            return _Intent("CONTEXTUAL_FOLLOWUP", cif=cif, kind="simulation_followup")
        if intent == shared_semantics.RETURN_TO_BASELINE:
            return _Intent(
                "CONTEXTUAL_FOLLOWUP",
                direct=("Đã quay lại dữ liệu thực của hồ sơ. Các kết quả mô phỏng trước đó "
                        "không làm thay đổi quyết định gốc."),
                cif=cif, kind="baseline",
            )
        if intent == shared_semantics.CLARIFICATION:
            return _Intent("CONTEXTUAL_FOLLOWUP", kind="clarify_nonpayment")
        if intent == shared_semantics.CLARIFICATION_RESPONSE:
            return _Intent("CONTEXTUAL_FOLLOWUP", kind="clarification_response")
        if intent == shared_semantics.ACTIVE_CIF_QUERY:
            return _Intent("CURRENT_CONTEXT", kind="context")
        if intent == shared_semantics.UNKNOWN:
            if plan.source == "security_guard":
                return _Intent("FALLBACK", direct=_SECURITY_TEXT, kind="fallback")
            return _Intent("FALLBACK", direct=_FALLBACK_TEXT, kind="fallback")
        return _Intent("FALLBACK", direct=_FALLBACK_TEXT, kind="fallback")

    def _fast_local_intent(self, message: str, norm: str) -> NLUResult:
        """Fast deterministic NLU path. High-confidence only; anything that is
        not clearly expressed falls to the LLM interpreter."""
        if not norm:
            return NLUResult(intent="UNKNOWN", confidence=1.0, needs_clarification=True)
        if _has_any(norm, _SECURITY_MARKERS):
            return NLUResult(intent="UNKNOWN", entities={"reason": "security"}, confidence=1.0)
        if _match_phrases(norm, _META_IDENTITY) or _match_phrases(_strip_pronoun(norm), _META_IDENTITY):
            return NLUResult(intent="IDENTITY", confidence=1.0)
        if _is_greeting(norm):
            return NLUResult(intent="GREETING", confidence=1.0)
        if _match_phrases(norm, _HELP) or _match_phrases(_strip_pronoun(norm), _HELP):
            return NLUResult(intent="HELP", confidence=1.0)
        # A pending question owns short replies. This is intentionally before
        # generic case matching so "quyết định" cannot fall through to RAG.
        if self._memory.pending_clarification == "NONPAYMENT" and norm in (
            "mo phong", "quyet dinh", "quy trinh",
        ):
            return NLUResult(intent="CLARIFICATION_RESPONSE", confidence=1.0)
        cbs_kind = _call_cbs_kind(norm)
        if cbs_kind == "comparison":
            return NLUResult(intent="KNOWLEDGE", entities={"kind": "comparison"}, confidence=1.0)
        if cbs_kind == "call":
            return NLUResult(intent="KNOWLEDGE", entities={"kind": "call"}, confidence=1.0)
        if cbs_kind == "cbs":
            return NLUResult(intent="KNOWLEDGE", entities={"kind": "cbs"}, confidence=1.0)
        if self._memory.last_topic == "ROUTING_CALL_CBS":
            if norm in ("cbs thi sao", "cbs sao", "con cbs", "cbs"):
                return NLUResult(intent="KNOWLEDGE", entities={"kind": "cbs"}, confidence=1.0)
            if norm in ("khac nhau o dau", "khac nhau gi", "so sanh di"):
                return NLUResult(intent="KNOWLEDGE", entities={"kind": "comparison"}, confidence=1.0)

        # AI governance question — must be before decision markers
        if _has_any(norm, ("ai quyet dinh", "ai co tu quyet dinh", "tu quyet dinh", "ai co the quyet dinh", "may quyet dinh", "ai ra quyet dinh")):
            return NLUResult(intent="KNOWLEDGE", entities={"kind": "governance"}, confidence=1.0)

        # Score-is-not-probability question
        if "diem" in norm and _has_any(norm, ("xac suat", "khac nang", "kha nang khach", "kha nang tra no")):
            return NLUResult(intent="KNOWLEDGE", entities={"kind": "score_semantics"}, confidence=1.0)

        cif = _extract_cif(message)

        # Decision explanation — "chua can goi" / "chua goi" / "chua lien he"
        # must be detected even for longer phrases (GAP-08 parity fix)
        effective_cif = cif or self._memory.last_cif
        if _has_any(norm, ("chua can goi", "chua goi", "chua can lien he", "chua lien he", "sao chua goi", "sao chua lien he")):
            return NLUResult(intent="CUSTOMER_DECISION", cif=effective_cif, use_context=True, confidence=0.95)

        if "khach khong tra no" in norm or "khach hang khong tra no" in norm:
            return NLUResult(intent="CLARIFICATION_RESPONSE", confidence=1.0)
        if (cif and (("can xem" in norm and _has_any(norm, ("vi sao", "tai sao")))
                     or _has_any(norm, ("vi sao lai xem", "phai uu tien", "nam top")))):
            return NLUResult(intent="EXPLAIN_PRIORITY", cif=cif, confidence=1.0)
        if self._memory.last_cif and _has_any(norm, ("tai sao khach nay nam top", "vi sao phai uu tien ho so nay")):
            return NLUResult(intent="EXPLAIN_PRIORITY", cif=self._memory.last_cif, confidence=0.95)

        if norm in ("quyet dinh", "quyet dinh cua khach", "xem quyet dinh") and (cif or self._memory.last_cif):
            return NLUResult(intent="CUSTOMER_DECISION", cif=cif or self._memory.last_cif,
                             use_context=True, confidence=0.9)

        if _is_bare_why(norm) or _has_any(norm, ("vi sao lai", "tai sao lai")):
            return NLUResult(
                intent="FOLLOWUP_WHY", cif=cif or self._memory.last_cif, use_context=True,
                confidence=0.9, needs_clarification=not (cif or self._memory.last_cif),
            )
        if cif and _has_any(norm, _SHOULD_CALL_MARKERS):
            return NLUResult(
                intent="CUSTOMER_SHOULD_CALL", cif=cif, entities={"question": "should_call"},
                confidence=0.95,
            )
        if _has_any(norm, _TODAY_CALL_MARKERS):
            return NLUResult(intent="TODAY_CALL_LIST", use_context=False, confidence=0.9)
        if (("hom nay" in norm and _has_any(norm, _TODAY_PRIORITIES_MARKERS))
                or norm in ("toi can lam gi", "viec hom nay")):
            return NLUResult(intent="TODAY_PRIORITIES", confidence=0.95)
        if _has_any(norm, _COMPARE_CUSTOMERS_MARKERS):
            return NLUResult(
                intent="CUSTOMER_DECISION", cif=cif or self._memory.last_cif,
                entities={"compare": True}, use_context=True, confidence=0.88,
                needs_clarification=not (cif or self._memory.last_cif),
            )
        if _has_any(norm, _TINH_DIEM_MARKERS) or ("diem" in norm and "bao nhieu" in norm):
            effective_cif = cif or self._memory.last_cif
            return NLUResult(
                intent="RECOVERY_SCORE_EXPLANATION" if effective_cif else "RECOVERY_SCORE",
                cif=effective_cif, use_context=True, confidence=0.92,
                needs_clarification=not effective_cif,
            )
        if "diem" in norm and (
            "co hoi thu hoi" in norm or "diem cua" in norm
            or "diem duoc tinh" in norm or "diem tinh dua tren" in norm
            or _has_any(norm, _SCORE_EXPLAIN_MARKERS)
            or _has_any(norm, _SCORE_AMBIGUOUS_MARKERS)
        ):
            effective_cif = cif or self._memory.last_cif
            return NLUResult(
                intent="RECOVERY_SCORE_EXPLANATION", cif=effective_cif,
                use_context=True, confidence=0.9, needs_clarification=not effective_cif,
            )
        if "lam sao de thay" in norm and "thay doi" in norm:
            return NLUResult(intent="SIMULATION_FOLLOWUP", cif=self._memory.last_cif,
                             confidence=0.95)
        if _has_any(norm, _BARE_SIMULATION_MARKERS) or _has_any(norm, _SIMULATION_MARKERS):
            return NLUResult(
                intent="SIMULATION", cif=cif or self._memory.last_cif,
                entities={"changes": _extract_changes(norm)}, use_context=True,
                confidence=0.92, needs_clarification=not (cif or self._memory.last_cif),
            )
        if _has_any(norm, _FOLLOWUP_WHAT_NEXT_MARKERS):
            return NLUResult(
                intent="FOLLOWUP_WHAT_NEXT", cif=cif or self._memory.last_cif,
                use_context=True, confidence=0.88,
                needs_clarification=not (cif or self._memory.last_cif),
            )
        if norm in ("quay lai du lieu that", "quay lai du lieu goc", "tro ve du lieu that"):
            return NLUResult(intent="SIMULATION_FOLLOWUP", cif=self._memory.last_cif,
                             entities={"baseline": True}, confidence=1.0)
        if _has_any(norm, _CURRENT_CONTEXT_MARKERS):
            return NLUResult(intent="CURRENT_CONTEXT", confidence=0.95)
        if cif:
            return NLUResult(intent="CUSTOMER_DECISION", cif=cif, confidence=0.9)
        if self._memory.last_cif and _has_any(norm, _FOLLOWUP_MARKERS):
            return NLUResult(
                intent="FOLLOWUP_WHY", cif=self._memory.last_cif, use_context=True,
                confidence=0.9,
            )
        if "khong lien quan" in norm or "khong lien quan gi" in norm:
            return NLUResult(intent="UNKNOWN", confidence=1.0)
        if _has_any(norm, _KNOWLEDGE_MARKERS):
            return NLUResult(intent="KNOWLEDGE", confidence=0.9)
        return NLUResult(intent="UNKNOWN", confidence=0.3, needs_clarification=True)

    def _nlu_interpret(self, message: str, norm: str, fallback: NLUResult) -> NLUResult:
        """LLM NLU interpreter (OpenNLU fallback). It never answers the user
        directly; it only returns the canonical intent + entities."""
        if fallback and fallback.intent == "UNKNOWN" and fallback.confidence >= 1.0:
            return fallback
        client = maas_client_from_env(timeout_seconds=6)
        if client is None:
            return NLUResult(
                intent="UNKNOWN", cif=fallback.cif if fallback else None,
                use_context=True, confidence=0.2, needs_clarification=True,
            )
        prompt = (
            "Bạn là bộ phân loại ý định tiếng Việt cho trợ lý thu hồi nợ "
            "của ngân hàng. Chọn đúng một intent trong danh sách: "
            + ", ".join(NLU_INTENTS)
            + ". Trả về JSON duy nhất dạng {\"intent\":\"...\",\"cif\":\"...\","
              "\"confidence\":0-1,\"needs_clarification\":true/false}. "
              "cif chỉ điền khi câu hỏi nhắc khách cụ thể (SYNxxxxxx hoặc GOLDEN_Gxx). "
              "Câu hỏi: " + message
        )
        raw, _model = client.complete(prompt, max_tokens=120, temperature=0)
        parsed: dict[str, Any] = {}
        if raw:
            extracted = re.search(r"\{.*\}", raw, re.DOTALL)
            if extracted:
                try:
                    parsed = json.loads(extracted.group(0))
                except (ValueError, TypeError):
                    parsed = {}
        intent = parsed.get("intent") or (fallback.intent if fallback else "UNKNOWN")
        if intent not in NLU_INTENTS:
            intent = fallback.intent if fallback and fallback.intent in NLU_INTENTS else "UNKNOWN"
        try:
            confidence = float(parsed.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        cif = str(parsed.get("cif") or "").upper()
        if not _CIF_RE.fullmatch(cif):
            cif = None
        needs_clarification = bool(parsed.get("needs_clarification", False))
        return NLUResult(intent=intent, cif=cif, use_context=True,
                         confidence=confidence, needs_clarification=needs_clarification)

    def _intent_from_nlu(self, message: str, nlu: NLUResult) -> _Intent:
        intent = nlu.intent
        cif = nlu.cif
        if intent == "IDENTITY":
            return _Intent("META_IDENTITY", direct=_IDENTITY_TEXT, kind="identity")
        if intent == "GREETING":
            return _Intent("HELP", direct=f"Chào bạn. {_HELP_TEXT}", kind="help")
        if intent == "HELP":
            return _Intent("HELP", direct=_HELP_TEXT, kind="help")
        if intent == "KNOWLEDGE":
            kind = (nlu.entities or {}).get("kind")
            if kind == "comparison":
                return _Intent("KNOWLEDGE", direct=_CALL_CBS_COMPARISON, kind="knowledge")
            if kind == "call":
                return _Intent("KNOWLEDGE", direct=_CALL_TEXT, kind="knowledge")
            if kind == "cbs":
                return _Intent("KNOWLEDGE", direct=_CBS_TEXT, kind="knowledge")
            if kind == "governance":
                return _Intent("KNOWLEDGE", direct=shared_semantics.AI_GOVERNANCE_TEXT, kind="knowledge")
            if kind == "score_semantics":
                return _Intent("KNOWLEDGE", direct=shared_semantics.SCORE_NOT_PROBABILITY_TEXT, kind="knowledge")
            return _Intent("KNOWLEDGE", kind="knowledge")
        if intent == "EXPLAIN_PRIORITY":
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="priority")
        if intent == "CLARIFICATION_RESPONSE":
            if "khach khong tra no" in _normalize(message):
                return _Intent("CONTEXTUAL_FOLLOWUP", kind="clarify_nonpayment")
            return _Intent("CONTEXTUAL_FOLLOWUP", kind="clarification_response")
        if intent == "TODAY_PRIORITIES":
            return _Intent("TODAY_PRIORITIES", kind="today")
        if intent == "TODAY_CALL_LIST":
            return _Intent("TODAY_PRIORITIES", kind="call_list")
        if intent == "CUSTOMER_SHOULD_CALL":
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="should_call")
        if intent == "CUSTOMER_DECISION" and (nlu.entities or {}).get("compare"):
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="compare")
        if intent in ("CUSTOMER_DECISION", "CUSTOMER_SUMMARY"):
            if intent == "CUSTOMER_DECISION" and _normalize(message) in (
                "quyet dinh", "quyet dinh cua khach", "xem quyet dinh",
            ):
                return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="decision")
            return _Intent("CUSTOMER_EXPLICIT", cif=cif, kind="customer")
        if intent == "RECOVERY_SCORE":
            return _Intent("RECOVERY_SCORE_EXPLANATION", cif=cif, kind="score_ask")
        if intent == "RECOVERY_SCORE_EXPLANATION":
            return _Intent("RECOVERY_SCORE_EXPLANATION", cif=cif, kind="score")
        if intent == "SIMULATION":
            changes = (nlu.entities or {}).get("changes") or _extract_changes(_normalize(message))
            return _Intent("SIMULATION", cif=cif, changes=dict(changes), kind="simulation")
        if intent == "SIMULATION_FOLLOWUP":
            if (nlu.entities or {}).get("baseline"):
                return _Intent(
                    "CONTEXTUAL_FOLLOWUP",
                    direct=("Đã quay lại dữ liệu thực của hồ sơ. Các kết quả mô phỏng trước đó "
                            "không làm thay đổi quyết định gốc."),
                    cif=cif, kind="baseline",
                )
            if "lam sao de thay" in _normalize(message) and "thay doi" in _normalize(message):
                return _Intent(
                    "CONTEXTUAL_FOLLOWUP",
                    direct=("Kết quả chỉ thay đổi khi giả định làm thay đổi điều kiện mà Simulation Core "
                            "đang sử dụng. Với dữ liệu hiện tại, Trợ lý không thể tự đề xuất hay bịa thêm biến; "
                            "Anh/Chị có thể thử một giả định được hỗ trợ như tiền vào 7 ngày hoặc trạng thái cam kết."),
                    cif=cif, kind="simulation_followup",
                )
            return _Intent("CONTEXTUAL_FOLLOWUP", cif=cif, kind="simulation_followup")
        if intent == "CURRENT_CONTEXT":
            return _Intent("CURRENT_CONTEXT", kind="context")
        if intent == "FOLLOWUP_WHY":
            return _Intent("CONTEXTUAL_FOLLOWUP", cif=cif, kind="followup")
        if intent == "FOLLOWUP_WHAT_NEXT":
            return _Intent("CONTEXTUAL_FOLLOWUP", cif=cif, kind="what_next")
        if intent == "UNKNOWN":
            if (nlu.entities or {}).get("reason") == "security":
                direct = _SECURITY_TEXT
            elif nlu.needs_clarification:
                if self._memory.last_cif:
                    direct = (f"Mày đang hỏi về {self._memory.last_cif} đúng không? "
                              f"Muốn xem có nên gọi, cách tính điểm hay tình trạng hiện tại?")
                else:
                    direct = _NLU_CLARIFICATION_TEXT
            else:
                direct = _FALLBACK_TEXT
            return _Intent("FALLBACK", direct=direct, kind="fallback")
        return _Intent("FALLBACK", direct=_FALLBACK_TEXT, kind="fallback")

    def _call_list_answer(self) -> str:
        """Deterministic 'who should I call first today' answer from the NBA tool."""
        rows = self.repository.portfolio()
        actionable: list[tuple[str, dict[str, Any]]] = []
        for row in rows:
            envelope = invoke_tool("get_next_best_action", {"cif": row["cif"]}, repository=self.repository)
            data = envelope.get("data") or {}
            if envelope.get("ok") and isinstance(data, dict) and data.get("channel") == "CALL":
                actionable.append((row["cif"], data))
        if not actionable:
            return "Hôm nay chưa có hồ sơ nào trong danh mục mô phỏng cần gọi điện ngay."
        actionable.sort(key=lambda item: (-(item[1].get("recovery_opportunity_score") or 0), item[0]))
        lines = ["Danh sách hồ sơ có kênh CALL theo quyết định hệ thống (mô phỏng):"]
        for cif, data in actionable[:3]:
            treatment = _TREATMENT_VN.get(data.get("treatment"), "theo quyết định hệ thống")
            lines.append(f"• {cif} · Điểm {data.get('recovery_opportunity_score') or 0} · {treatment}")
        lines.append(f"Tổng cộng {len(actionable)} hồ sơ có kênh xử lý là CALL hôm nay (dữ liệu mô phỏng).")
        return _sanitize_answer("\n".join(lines))

    def _should_call_answer(self, cif: str) -> str:
        envelope = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repository)
        data = envelope.get("data") or {}
        if not envelope.get("ok") or not isinstance(data, dict):
            return f"Không tìm thấy quyết định cho hồ sơ {cif} trong bản demo."
        channel = data.get("channel")
        treatment = _TREATMENT_VN.get(data.get("treatment"), "theo quyết định hệ thống")
        score = data.get("recovery_opportunity_score")
        if channel == "CALL":
            text = (f"Có, hồ sơ {cif} có kênh CALL. "
                    f"Hành động: {treatment.lower()}.")
        else:
            text = (f"Chưa cần gọi {cif} hôm nay. "
                    f"Kênh hiện tại: {_CHANNEL_VN.get(channel, 'chưa xác định')}, "
                    f"hành động: {treatment.lower()}.")
        if score is not None:
            text += f" Điểm {score}/100."
        return _sanitize_answer(text)

    def _compare_customers_answer(self, cif_a: str | None, cif_b: str | None) -> str:
        if not cif_a or not cif_b or cif_a == cif_b:
            return "Để so sánh ưu tiên, cho tôi mã hai hồ sơ (ví dụ SYN002846 và SYN001346)."

        def _fetch(cif: str) -> dict[str, Any]:
            envelope = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repository)
            data = envelope.get("data") or {}
            return data if envelope.get("ok") and isinstance(data, dict) else {}

        first, second = _fetch(cif_a), _fetch(cif_b)
        if not first or not second:
            return "Chưa đủ dữ liệu để so sánh hai hồ sơ trong bản demo."
        score_a, score_b = first.get("recovery_opportunity_score"), second.get("recovery_opportunity_score")
        if score_a == score_b:
            return (f"Cả {cif_a} và {cif_b} cùng điểm cơ hội {score_a}/100; ưu tiên bằng nhau "
                    f"theo quyết định hệ thống trên dữ liệu mô phỏng.")
        higher, higher_score = (cif_a, score_a) if (score_a or 0) > (score_b or 0) else (cif_b, score_b)
        lower, lower_score = (cif_b, score_b) if higher == cif_a else (cif_a, score_a)
        data = _fetch(higher)
        treatment = _TREATMENT_VN.get(data.get("treatment"), "theo quyết định hệ thống")
        return (_sanitize_answer(
            f"Hồ sơ {higher} đáng ưu tiên hơn với điểm {higher_score}/100 so với {lower} ({lower_score}/100). "
            f"Hành động hiện tại của {higher} là {treatment.lower()}."))

    def _what_next_answer(self, cif: str) -> str:
        sim = self._memory.last_simulation_context or {}
        if sim.get("cif") == cif and sim.get("changes"):
            try:
                envelope = invoke_tool(
                    "simulate_decision",
                    {"cif": cif, "changes": dict(sim["changes"])},
                    repository=self.repository,
                )
                data = envelope.get("data") or {}
                if envelope.get("ok") and isinstance(data, dict):
                    after = data.get("decision") or data.get("after") or {}
                    treatment = _TREATMENT_VN.get(after.get("treatment"), "theo quyết định hệ thống")
                    channel = _CHANNEL_VN.get(after.get("channel"), "chưa xác định")
                    return _sanitize_answer(
                        f"Nếu giả định mô phỏng xảy ra, bước tiếp theo là "
                        f"{treatment.lower()} qua kênh {channel.lower()}. "
                        f"Đây là kết quả mô phỏng, chưa phải thay đổi thực tế.")
            except Exception:
                pass
        if cif and self._memory.last_decision_context and self._memory.last_decision_context.get("cif") == cif:
            decision = self._memory.last_decision_context
            treatment = _TREATMENT_VN.get(decision.get("treatment"), "theo quyết định hệ thống")
            channel = _CHANNEL_VN.get(decision.get("channel"), "chưa xác định")
            return _sanitize_answer(
                f"Với {cif}, bước tiếp theo là {treatment.lower()} qua kênh {channel.lower()}.")
        envelope = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repository)
        data = envelope.get("data") or {}
        if not envelope.get("ok") or not isinstance(data, dict):
            return f"Chưa có hành động tiếp theo cho hồ sơ {cif} trong bản demo."
        treatment = _TREATMENT_VN.get(data.get("treatment"), "theo quyết định hệ thống")
        channel = _CHANNEL_VN.get(data.get("channel"), "chưa xác định")
        return _sanitize_answer(
            f"Bước tiếp theo cho {cif}: {treatment.lower()} qua kênh {channel.lower()}.")

    def _decision_enrich(self, cif: str | None) -> dict[str, Any] | None:
        if not cif:
            return None
        try:
            envelope = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repository)
        except Exception:
            return None
        data = envelope.get("data") or {}
        if not envelope.get("ok") or not isinstance(data, dict):
            return None
        decision = {
            "cif": cif,
            "route": data.get("final_route"),
            "treatment": data.get("treatment"),
            "channel": data.get("channel"),
            "score": data.get("recovery_opportunity_score"),
        }
        self._memory.last_decision_context = decision
        return decision

    def _update_memory(
        self, message: str, intent: _Intent, question_intent: str,
        answer_kind: str, cif: str | None, path: str, answer: str,
    ) -> None:
        self._memory.previous_user_question = message[:160]
        self._memory.previous_user_message = message[:160]
        self._memory.last_intent = question_intent
        self._memory.last_answer_kind = answer_kind
        self._memory.last_path = path
        self._memory.last_response_kind = answer_kind
        if question_intent in (
            "DECISION_EXPLANATION", "SIMULATION", "RECOVERY_SCORE_EXPLANATION",
            "CUSTOMER_SUMMARY", "CUSTOMER_SHOULD_CALL", "FOLLOWUP_WHAT_NEXT",
        ):
            self._memory.last_actionable_intent = question_intent
        if cif and intent.label in ("CUSTOMER_EXPLICIT", "SIMULATION", "CONTEXTUAL_FOLLOWUP", "RECOVERY_SCORE_EXPLANATION"):
            if self._memory.active_cif and self._memory.active_cif != cif:
                self._memory.previous_cif = self._memory.active_cif
            self._memory.active_cif = cif
            if self._memory.last_cif and cif != self._memory.last_cif:
                self._memory.previous_cif = self._memory.last_cif
                self._invalidate_stale_context(cif)
            self._memory.last_cif = cif

    def _invalidate_stale_context(self, new_cif: str) -> None:
        """Discard any decision/score/simulation context owned by a previous CIF.

        Context values are NEVER mixed across CIFs. Each stored context carries
        an explicit ``cif`` owner; anything not owned by the incoming CIF is dropped.
        """
        for field in ("last_decision_context", "last_score_context", "last_simulation_context"):
            context = getattr(self._memory, field) or {}
            if context.get("cif") != new_cif:
                setattr(self._memory, field, None)

    def _seed(self, conversation_context: dict[str, Any] | None) -> None:
        if not isinstance(conversation_context, dict):
            return
        for key, field in (("previous_intent", "last_intent"), ("active_cif", "last_cif"), ("previous_path", "last_path")):
            value = conversation_context.get(key)
            if isinstance(value, str) and value.strip() and not getattr(self._memory, field):
                setattr(self._memory, field, value.strip()[:160])
        active = conversation_context.get("active_cif")
        if isinstance(active, str) and active.strip():
            self._memory.active_cif = active.strip()[:160]
        previous = conversation_context.get("previous_user_question")
        if isinstance(previous, str) and previous.strip():
            self._memory.previous_user_question = previous.strip()[:160]
            self._memory.previous_user_message = previous.strip()[:160]
