"""Shared semantic contract for the Web Copilot and Zalo Bot.

Both channels resolve the same canonical intent for the same message + same
conversation state. This module is pure and deterministic: it never calls
tools, the LLM, or the network. Channel adapters remain responsible for
AgentBase fallback (step 7 of the precedence), tool execution, and
channel-specific formatting.

Intent precedence (TASK-017 section 7):

    1. GREETING / HELP
    2. TODAY_WORKLIST / GLOBAL_OPERATIONAL
    3. EXPLICIT_CIF_IN_MESSAGE
    4. EXPLICIT_CASE_INTENT
    5. PENDING_CLARIFICATION
    6. LAST_TOPIC_FOLLOWUP
    7. BOUNDED_AGENTBASE_SEMANTIC_RESOLUTION   (channel adapter)
    8. EXPLICIT_GENERIC_CASE_SUMMARY
    9. CLARIFICATION
    10. SAFE_FALLBACK

``active_cif`` is context only. It must never become the default intent.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------- #
# Canonical intent set
# --------------------------------------------------------------------------- #

GREETING = "GREETING"
HELP = "HELP"
TODAY_WORKLIST = "TODAY_WORKLIST"
KNOWLEDGE = "KNOWLEDGE"
SCORE_VALUE = "SCORE_VALUE"
SCORE_BREAKDOWN = "SCORE_BREAKDOWN"
EXPLAIN_PRIORITY = "EXPLAIN_PRIORITY"
CURRENT_CASE_SUMMARY = "CURRENT_CASE_SUMMARY"
CURRENT_CASE_ACTION = "CURRENT_CASE_ACTION"
SIMULATION = "SIMULATION"
SIMULATION_FOLLOWUP = "SIMULATION_FOLLOWUP"
RETURN_TO_BASELINE = "RETURN_TO_BASELINE"
CLARIFICATION = "CLARIFICATION"
CLARIFICATION_RESPONSE = "CLARIFICATION_RESPONSE"
ACTIVE_CIF_QUERY = "ACTIVE_CIF_QUERY"
KNOWLEDGE_EVALUATION = "KNOWLEDGE_EVALUATION"
KNOWLEDGE_GOVERNANCE = "KNOWLEDGE_GOVERNANCE"
KNOWLEDGE_SCORE_SEMANTICS = "KNOWLEDGE_SCORE_SEMANTICS"
UNKNOWN = "UNKNOWN"

CANONICAL_INTENTS = frozenset({
    GREETING, HELP, TODAY_WORKLIST, KNOWLEDGE, SCORE_VALUE, SCORE_BREAKDOWN,
    EXPLAIN_PRIORITY, CURRENT_CASE_SUMMARY, CURRENT_CASE_ACTION, SIMULATION,
    SIMULATION_FOLLOWUP, RETURN_TO_BASELINE, CLARIFICATION, CLARIFICATION_RESPONSE,
    ACTIVE_CIF_QUERY, KNOWLEDGE_EVALUATION, KNOWLEDGE_GOVERNANCE,
    KNOWLEDGE_SCORE_SEMANTICS, UNKNOWN,
})


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #

_CIF_RE = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b", re.IGNORECASE)


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize(value: str) -> str:
    """Shared no-diacritic, slang-tolerant normalization used by both channels."""
    text = _strip_diacritics(value or "")
    text = re.sub(r"\bdc\b", "duoc", text)
    text = re.sub(r"\bntn\b", "nhu the nao", text)
    text = text.replace("vi sai", "vi sao")
    text = re.sub(r"\bcac tinh\b", "cach tinh", text)
    text = re.sub(r"\btao ngay\b", "tao nay", text)
    text = re.sub(r"\bhnay\b", "hom nay", text)
    text = re.sub(r"^nay\b", "hom nay", text)
    text = re.sub(r"\b(?:lam|lm) j\b", "lam gi", text)
    text = re.sub(r"\b(?:lam|lm)\s+j\b", "lam gi", text)
    text = text.replace("/", " ")
    text = re.sub(r"[?!.,;:]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_cif(message: str) -> str | None:
    """Extract a CIF, correcting only the unambiguous ``SNY`` -> ``SYN`` typo."""
    matched = _CIF_RE.search(message)
    if matched:
        return matched.group(0).upper()
    typo = re.search(r"\bSNY(\d{6})\b", message, re.IGNORECASE)
    return f"SYN{typo.group(1)}" if typo else None


# --------------------------------------------------------------------------- #
# Conversation state
# --------------------------------------------------------------------------- #

@dataclass
class ConversationState:
    active_cif: str = ""
    last_intent: str = ""
    last_topic: str = ""
    last_cif: str = ""
    pending_clarification: str = ""
    last_simulation_context: dict[str, Any] | None = None
    previous_intent: str = ""
    previous_user_question: str = ""

    @classmethod
    def from_context(cls, context: dict[str, Any] | None) -> "ConversationState":
        context = context or {}
        return cls(
            active_cif=str(context.get("active_cif") or ""),
            last_intent=str(context.get("last_intent") or context.get("previous_intent") or ""),
            last_topic=str(context.get("last_topic") or context.get("previous_topic") or ""),
            last_cif=str(context.get("last_cif") or context.get("active_cif") or ""),
            pending_clarification=str(context.get("pending_clarification") or ""),
            last_simulation_context=context.get("last_simulation_context") if isinstance(context.get("last_simulation_context"), dict) else None,
            previous_intent=str(context.get("previous_intent") or ""),
            previous_user_question=str(context.get("previous_user_question") or ""),
        )


# --------------------------------------------------------------------------- #
# Resolved intent
# --------------------------------------------------------------------------- #

@dataclass
class ResolvedIntent:
    intent: str
    cif: str | None = None
    kind: str = ""
    changes: dict[str, Any] | None = None
    confidence: float = 0.0
    needs_clarification: bool = False

    @property
    def is_global(self) -> bool:
        return self.intent in (GREETING, HELP, TODAY_WORKLIST, KNOWLEDGE, KNOWLEDGE_EVALUATION, KNOWLEDGE_GOVERNANCE, KNOWLEDGE_SCORE_SEMANTICS)


# --------------------------------------------------------------------------- #
# Marker tables
# --------------------------------------------------------------------------- #

_GREETING_EXACT = frozenset({"alo", "chao", "hello", "hi", "xin chao", "chao ban", "chao em", "chao anh", "chao chi", "yo", "hey", "e", "alo alo", "alo alo alo", "chao nhe"})
_GREETING_PREFIX = ("xin chao", "chao ban", "chao em", "chao chi", "chao anh", "hello", "hi ", "alo ", "yo ", "hey ", "chao nhe")

_HELP_MARKERS = ("tro giup", "giup gi", "giup duoc gi", "ban lam gi", "ban giup", "can giup", "huong dan", "ban lam duoc gi", "ban co the giup")

_TODAY_WORKLIST_MARKERS = ("lam gi", "can lam", "phai lam", "can thao tac", "uu tien", "viec gi", "can xu ly", "xem khach", "noi bat", "diem dang chu y")
_TODAY_WORKLIST_EXACT = frozenset({"toi can lam gi", "viec hom nay", "hom nay lam gi", "nay lam gi", "hom nay uu tien gi", "viec gi hom nay"})

_KNOWLEDGE_CONCEPT = ("la gi", "la gi vay", "la gi the", "nghia la", "de lam gi", "khac nhau", "khac nhau giua", "khac nhau the nao", "khac gi", "duoc tinh nhu the nao", "duoc tinh the nao", "nam o dau", "chay o dau", "dong vai tro")

_EVALUATION_MARKERS = ("evaluation", "bo test", "he thong ai duoc cham", "he thong danh gia ai", "ai duoc cham nhu the nao", "test danh gia he thong")

_AI_GOVERNANCE_MARKERS = ("ai quyet dinh", "ai co tu quyet dinh", "tu quyet dinh", "ai quyet dinh hanh dong", "ai co the quyet dinh", "may quyet dinh", "ai dat ra quyet dinh", "ai ra quyet dinh")

_SCORE_PROBABILITY_MARKERS = ("xac suat", "khac nang", "kha nang khach", "kha nang tra no", "phan tram khach", "xac suat tra")

_SCORE_BREAKDOWN_MARKERS = ("duoc tinh", "tinh dua tren", "dua tren", "cach tinh diem", "tinh diem", "diem tinh", "diem duoc tinh", "diem cua", "co hoi thu hoi", "sao cao", "sao thap", "diem cao", "diem thap", "vi sao diem", "tai sao diem", "sao diem", "kha nang thanh toan", "vi sao lai", "tai sao lai", "cham", "tieu chi", "diem cham")
_SCORE_VALUE_MARKERS = ("diem bao nhieu", "diem khach", "score khach", "diem cua khach", "diem hien tai", "bao nhieu diem")

_EXPLAIN_PRIORITY_MARKERS = ("vi sao lai xem", "phai uu tien", "nam top", "vi sao can xem", "tai sao can xem", "vi sao phai xem", "uu tien ho so nay", "nam top hom nay")

_CASE_SUMMARY_MARKERS = ("tom tat", "tinh trang", "thong tin khach", "khach nay the nao", "khach nay sao", "xem tinh trang", "cho toi xem", "cho tao xem")
_CASE_ACTION_MARKERS = ("nen lam gi", "hanh dong", "xu ly sao", "buoc tiep theo", "the gio lam gi", "gio lam gi", "lam gi tiep")

_SIMULATION_MARKERS = ("neu ", "neu nhu", "gia su", "mo phong", "tinh huong", "what if")
_SIMULATION_FOLLOWUP_MARKERS = ("lam sao de thay doi", "vi sao lai doi", "vi sao doi", "thi sao", "gio lam gi", "lam gi tiep", "the gio lam gi")
_RETURN_BASELINE_MARKERS = ("quay lai du lieu that", "quay lai du lieu goc", "tro ve du lieu that", "tro ve baseline")

_CLARIFICATION_NONPAYMENT = ("khach khong tra no", "khach hang khong tra no", "khach khong thuc hien cam ket")

_INFLOW_ZERO_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\b(?:tien vao|dong tien) 7 ngay (?:bang|la) 0\b",
    r"\bkhong co (?:tien vao|dong tien) 7 ngay\b",
    r"\b(?:tien vao|dong tien) tuan nay (?:bang|la) 0\b",
    r"\bkhong co (?:tien vao|dong tien) tuan nay\b",
    r"\btuan nay khong co (?:tien vao|dong tien)\b",
    r"\b7 ngay khong co (?:tien vao|dong tien)\b",
))


def _has_any(text: str, markers: tuple[str, ...] | frozenset[str]) -> bool:
    return any(marker in text for marker in markers)


def _extract_simulation_changes(text: str) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    if any(pattern.search(text) for pattern in _INFLOW_ZERO_PATTERNS):
        changes["inflow_7d"] = 0
    if "cam ket" in text and any(token in text for token in ("pha vo", "bi pha", "khong thuc hien")):
        changes["ptp_state"] = "BROKEN"
    return changes


def _call_cbs_kind(text: str) -> str | None:
    has_call = "call" in text
    has_cbs = "cbs" in text
    concept = _has_any(text, _KNOWLEDGE_CONCEPT) or "thi sao" in text or text.endswith("sao")
    if has_call and has_cbs and (concept or _has_any(text, ("khac nhau", "so sanh"))):
        return "comparison"
    if has_call and concept:
        return "call"
    if has_cbs and (concept or _has_any(text, ("khac nhau", "so sanh"))):
        return "cbs"
    return None


# --------------------------------------------------------------------------- #
# Resolver
# --------------------------------------------------------------------------- #

def resolve(message: str, state: ConversationState | None = None) -> ResolvedIntent:
    """Deterministic high-confidence semantic resolver (precedence 1-6, 8-10).

    Returns UNKNOWN when no deterministic intent is identified; the channel
    adapter then applies bounded AgentBase resolution (step 7) or a safe
    fallback. ``active_cif`` is never used as a default intent.
    """
    state = state or ConversationState()
    norm = normalize(message)
    if not norm:
        return ResolvedIntent(UNKNOWN, confidence=1.0, needs_clarification=True)

    cif = extract_cif(message)
    effective_cif = cif or state.last_cif

    # 1. GREETING / HELP
    if norm in _GREETING_EXACT or any(norm.startswith(prefix) for prefix in _GREETING_PREFIX):
        return ResolvedIntent(GREETING, confidence=1.0)
    if _has_any(norm, _HELP_MARKERS):
        return ResolvedIntent(HELP, confidence=1.0)

    # 2. TODAY_WORKLIST / GLOBAL_OPERATIONAL
    if norm in _TODAY_WORKLIST_EXACT:
        return ResolvedIntent(TODAY_WORKLIST, confidence=0.95)
    if "hom nay" in norm and _has_any(norm, _TODAY_WORKLIST_MARKERS):
        return ResolvedIntent(TODAY_WORKLIST, confidence=0.95)
    if "nay" in norm and _has_any(norm, ("lam gi", "can lam", "phai lam", "can thao tac", "can xu ly", "xu ly gi", "viec gi")):
        return ResolvedIntent(TODAY_WORKLIST, confidence=0.93)

    # Evaluation knowledge (explicit only) — checked before case score so
    # "điểm được tính thế nào" stays a case score, not an evaluation question.
    if _has_any(norm, _EVALUATION_MARKERS):
        return ResolvedIntent(KNOWLEDGE_EVALUATION, confidence=0.95)

    # AI governance question — must be checked before decision words so
    # "AI có tự quyết định hành động không?" is KNOWLEDGE, not DECISION.
    if _has_any(norm, _AI_GOVERNANCE_MARKERS):
        return ResolvedIntent(KNOWLEDGE_GOVERNANCE, confidence=1.0)

    # Score-is-not-probability question — checked before score breakdown so
    # "Điểm 47 có phải là 47% khả năng trả nợ?" is KNOWLEDGE, not SCORE.
    if _has_any(norm, _SCORE_PROBABILITY_MARKERS) and "diem" in norm:
        return ResolvedIntent(KNOWLEDGE_SCORE_SEMANTICS, confidence=1.0)

    # Knowledge CALL/CBS (global, never hijacked by active CIF)
    cbs_kind = _call_cbs_kind(norm)
    if cbs_kind:
        return ResolvedIntent(KNOWLEDGE, kind=cbs_kind, confidence=1.0)

    # 3. EXPLICIT_CIF_IN_MESSAGE + 4. EXPLICIT_CASE_INTENT
    if cif:
        if _has_any(norm, _EXPLAIN_PRIORITY_MARKERS) or ("xem" in norm and _has_any(norm, ("vi sao", "tai sao"))) or (("vi sao" in norm or "tai sao" in norm) and "xem" in norm):
            return ResolvedIntent(EXPLAIN_PRIORITY, cif=cif, confidence=1.0)
        if _has_any(norm, _SCORE_BREAKDOWN_MARKERS) or _has_any(norm, ("cach tinh diem", "tinh diem")) or ("diem" in norm and _has_any(norm, ("giai thich", "tinh", "cham", "tieu chi", "dua tren", "chi tiet"))):
            return ResolvedIntent(SCORE_BREAKDOWN, cif=cif, confidence=0.95)
        if _has_any(norm, _SCORE_VALUE_MARKERS) or "diem bao nhieu" in norm:
            return ResolvedIntent(SCORE_VALUE, cif=cif, confidence=0.95)
        if _has_any(norm, _CASE_SUMMARY_MARKERS) or _has_any(norm, ("giai thich", "xem")):
            return ResolvedIntent(CURRENT_CASE_SUMMARY, cif=cif, confidence=0.92)
        if _has_any(norm, _CASE_ACTION_MARKERS):
            return ResolvedIntent(CURRENT_CASE_ACTION, cif=cif, confidence=0.9)

    # Score without explicit CIF -> use active/last CIF as context (not intent)
    if _has_any(norm, _SCORE_BREAKDOWN_MARKERS) or _has_any(norm, ("cach tinh diem", "tinh diem")) or ("diem" in norm and _has_any(norm, ("giai thich", "tinh", "cham", "tieu chi", "dua tren", "chi tiet"))):
        return ResolvedIntent(SCORE_BREAKDOWN, cif=effective_cif, confidence=0.9, needs_clarification=not effective_cif)
    if _has_any(norm, _SCORE_VALUE_MARKERS) or "diem bao nhieu" in norm:
        return ResolvedIntent(SCORE_VALUE, cif=effective_cif, confidence=0.9, needs_clarification=not effective_cif)

    # Priority without explicit CIF -> use last CIF
    if _has_any(norm, _EXPLAIN_PRIORITY_MARKERS) and effective_cif:
        return ResolvedIntent(EXPLAIN_PRIORITY, cif=effective_cif, confidence=0.9)

    # Non-payment hypothetical -> clarification (before simulation, since
    # "cam ket khong thuc hien" would otherwise look like a simulation change)
    if _has_any(norm, _CLARIFICATION_NONPAYMENT):
        return ResolvedIntent(CLARIFICATION, confidence=1.0)

    # Simulation
    changes = _extract_simulation_changes(norm)
    if _has_any(norm, _SIMULATION_MARKERS) or changes:
        return ResolvedIntent(SIMULATION, cif=effective_cif, changes=changes or None, confidence=0.92, needs_clarification=not effective_cif)

    # Return to baseline
    if _has_any(norm, _RETURN_BASELINE_MARKERS):
        return ResolvedIntent(RETURN_TO_BASELINE, cif=effective_cif, confidence=1.0)

    # Simulation follow-up (only meaningful with prior simulation context)
    if state.last_simulation_context and _has_any(norm, _SIMULATION_FOLLOWUP_MARKERS):
        return ResolvedIntent(SIMULATION_FOLLOWUP, cif=state.last_cif, confidence=0.9)

    # 5. PENDING_CLARIFICATION
    if state.pending_clarification == "NONPAYMENT" and norm in ("mo phong", "quyet dinh", "quy trinh", "mô phỏng", "quyết định", "quy trình"):
        return ResolvedIntent(CLARIFICATION_RESPONSE, confidence=1.0)

    # 6. LAST_TOPIC_FOLLOWUP (knowledge topic continuity)
    if state.last_topic == "ROUTING_CALL_CBS":
        if norm in ("cbs thi sao", "cbs sao", "con cbs", "cbs"):
            return ResolvedIntent(KNOWLEDGE, kind="cbs", confidence=1.0)
        if norm in ("khac nhau o dau", "khac nhau gi", "so sanh di", "khac nhau the nao"):
            return ResolvedIntent(KNOWLEDGE, kind="comparison", confidence=1.0)
        if norm in ("call thi sao", "call sao", "con call", "call"):
            return ResolvedIntent(KNOWLEDGE, kind="call", confidence=1.0)

    # Active CIF query ("tao đang thao tác với cif nào")
    if _has_any(norm, ("cif nao", "cif hien tai", "khach nao", "dang noi den", "dang xu ly ho so")):
        return ResolvedIntent(ACTIVE_CIF_QUERY, confidence=0.95)

    # 8. EXPLICIT_GENERIC_CASE_SUMMARY (only when user clearly asks for this case)
    if _has_any(norm, _CASE_SUMMARY_MARKERS) and effective_cif:
        return ResolvedIntent(CURRENT_CASE_SUMMARY, cif=effective_cif, confidence=0.85)

    # 10. SAFE_FALLBACK — never auto-summary from active_cif alone
    return ResolvedIntent(UNKNOWN, cif=effective_cif or None, confidence=0.3, needs_clarification=True)


# --------------------------------------------------------------------------- #
# Public enum mapping (section 17 / 20)
# --------------------------------------------------------------------------- #

PTP_STATUS_VN: dict[str, str] = {
    "OPEN": "Đang mở",
    "KEPT": "Đã thực hiện",
    "PARTIAL": "Thanh toán một phần",
    "BROKEN": "Không thực hiện cam kết",
    "EXPIRED": "Hết hạn",
    "CANCELLED": "Đã hủy",
    "NONE": "Chưa có cam kết",
}

TREATMENT_VN: dict[str, str] = {
    "WAIT": "Chờ theo dõi",
    "WAIT_SELF_CURE": "Chờ khách hàng tự thanh toán",
    "REMIND": "Nhắc thanh toán",
    "CONTACT": "Liên hệ khách hàng",
    "PTP_FOLLOW_UP": "Theo dõi cam kết thanh toán",
    "PTP_RECOVERY": "Xử lý cam kết không thực hiện",
    "PARTIAL_PAYMENT": "Thu hồi một phần",
    "CALLBACK": "Gọi lại sau",
    "VERIFY_CONTACT": "Xác minh thông tin liên hệ",
    "ESCALATE": "Chuyển bậc xử lý",
}

CHANNEL_VN: dict[str, str] = {
    "CALL": "Gọi điện",
    "SMS": "Tin nhắn SMS",
    "ZALO": "Zalo",
    "EMAIL": "Email",
    "FIELD": "Lực lượng hiện trường",
    "NONE": "Chưa cần liên hệ",
}

ROUTE_VN: dict[str, str] = {
    "CALL": "Tuyến CALL (gọi điện)",
    "CBS": "Tuyến CBS (nhắc thanh toán và theo dõi cam kết)",
    "OTHER": "Tuyến OTHER (xử lý khác)",
}


def map_ptp_status(status: Any) -> str:
    if status is None:
        return PTP_STATUS_VN["NONE"]
    return PTP_STATUS_VN.get(str(status), str(status))


def map_treatment(treatment: Any) -> str:
    if not treatment:
        return "Theo quyết định hệ thống"
    return TREATMENT_VN.get(str(treatment), str(treatment))


def map_channel(channel: Any) -> str:
    if not channel:
        return CHANNEL_VN["NONE"]
    return CHANNEL_VN.get(str(channel), str(channel))


def map_route(route: Any) -> str:
    if not route:
        return "Tuyến chưa xác định"
    return ROUTE_VN.get(str(route), str(route))


# Canonical knowledge answers for CALL/CBS (shared by both channels)
CALL_TEXT = (
    "CALL là tuyến xử lý qua gọi điện, hướng tới khách hàng cần tương tác trực tiếp "
    "để thu hồi. Routing là tuyến xử lý, không đồng nghĩa action phải thực hiện ngay. "
    "Thuộc tuyến CALL không có nghĩa hôm nay cán bộ nhất thiết phải gọi."
)

CBS_TEXT = (
    "CBS là tuyến nhắc thanh toán và theo dõi cam kết. Routing là tuyến xử lý, "
    "không đồng nghĩa action phải thực hiện ngay."
)

CALL_CBS_COMPARISON = (
    "CALL và CBS là hai tuyến xử lý (route) trong tác nghiệp thu hồi.\n"
    "• CALL — tuyến xử lý qua gọi điện, hướng tới khách hàng cần tương tác trực tiếp để thu hồi.\n"
    "• CBS — tuyến nhắc thanh toán và theo dõi cam kết.\n"
    "Khác nhau ở hướng tiếp cận: CALL dùng gọi điện để tương tác trực tiếp; CBS nhắc thanh toán "
    "và theo dõi cam kết.\n"
    "Routing là tuyến xử lý, không đồng nghĩa action phải thực hiện ngay.\n"
    "Thuộc tuyến CALL không có nghĩa hôm nay cán bộ nhất thiết phải gọi."
)

# --------------------------------------------------------------------------- #
# Score component Vietnamese labels (no raw enum leak)
# --------------------------------------------------------------------------- #

SCORE_COMPONENT_VN: dict[str, str] = {
    "BUSINESS_URGENCY": "Mức khẩn cấp nghiệp vụ",
    "ABILITY_TO_PAY": "Khả năng thanh toán",
    "WILLINGNESS_TO_PAY": "Mức sẵn sàng thanh toán",
    "CONTACTABILITY": "Khả năng tiếp cận",
    "TIMING_OPPORTUNITY": "Thời điểm thuận lợi",
    "STRATEGIC_ADJUSTMENT": "Điều chỉnh chiến lược",
}


def map_score_component(name: Any) -> str:
    if not name:
        return str(name or "")
    return SCORE_COMPONENT_VN.get(str(name), str(name))


# --------------------------------------------------------------------------- #
# Canonical knowledge answers for AI governance and score semantics
# --------------------------------------------------------------------------- #

AI_GOVERNANCE_TEXT = (
    "Không. AgentBase là bộ lập kế hoạch hội thoại, không phải bộ não nghiệp vụ.\n"
    "AgentBase có thể: hiểu câu hỏi tự nhiên, giữ ngữ cảnh, chọn công cụ được phê duyệt, "
    "truy xuất dữ liệu và kiến thức, tổ chức và giải thích câu trả lời.\n"
    "Nhưng các thành phần deterministic giữ quyền quyết định:\n"
    "• Decision Core quyết định route, điểm, treatment, channel.\n"
    "• Simulation Core tính kết quả mô phỏng.\n"
    "AI không tự ý quyết định hay thay đổi quyết định nghiệp vụ."
)

SCORE_NOT_PROBABILITY_TEXT = (
    "Không. 47/100 là Điểm Cơ hội Thu hồi dùng để hỗ trợ sắp thứ tự ưu tiên xử lý, "
    "không phải 47% xác suất khách hàng sẽ thanh toán.\n"
    "Điểm này tổng hợp từ 6 nhóm tiêu chí nghiệp vụ (mức khẩn cấp, khả năng thanh toán, "
    "sẵn sàng thanh toán, khả năng tiếp cận, thời điểm thuận lợi, điều chỉnh chiến lược). "
    "Điểm cao hơn nghĩa là hồ sơ đáng ưu tiên xử lý hơn, không nghĩa là xác suất trả nợ cao hơn."
)
