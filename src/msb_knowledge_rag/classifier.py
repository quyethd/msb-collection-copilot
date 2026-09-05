from __future__ import annotations

import re

from .models import QuestionType
from .security import security_scan

_CIF_PATTERN = re.compile(r"\b(?:SYN\d{6}|GOLDEN_G\d{2})\b")

_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "PRODUCT": (
        "sản phẩm", "tổng quan", "là gì", "trợ lý thu hồi", "collection copilot",
        "copilot", "giá trị", "bài toán", "người dùng", "lời hứa", "thông điệp",
    ),
    "ROUTING": (
        "tuyến", "call/cbs", "cbs", "routing", "phân tuyến", "route", "call và cbs",
        "phân loại tuyến",
    ),
    "RECOVERY_SCORE": (
        "điểm cơ hội", "recovery opportunity", "recovery score", "điểm số", "score",
        "cơ hội thu hồi", "thành phần điểm", "điểm 0-100", "priority",
    ),
    "NBA": (
        "hành động", "next best action", "nba", "treatment", "channel", "kênh",
        "objective", "tiếp theo", "ưu tiên hành động", "precedence",
    ),
    "PTP": (
        "ptp", "cam kết", "promise", "cam kết thanh toán", "thanh toán", "kept",
        "broken", "open", "fulfillment", "partial",
    ),
    "CASHFLOW": (
        "dòng tiền", "cashflow", "tiền vào", "dòng tiền ròng", "liquidity",
        "thanh khoản", "inflow", "outflow", "tiền ra",
    ),
    "SELF_CURE": (
        "tự thanh toán", "self-cure", "self cure", "wait self", "chờ khách hàng",
        "chưa cần gọi", "chưa cần liên hệ", "chờ tự thanh toán",
    ),
    "SIMULATION": (
        "mô phỏng", "simulation", "what-if", "what if", "kịch bản", "giả lập",
    ),
    "IMPACT": (
        "tác động", "impact", "giảm", "tiết kiệm", "giờ làm việc", "dự kiến",
        "chi phí vận hành", "cuộc gọi tránh",
    ),
    "DATA": (
        "dữ liệu", "synthetic", "mô phỏng dữ liệu", "demo", "seed", "danh mục",
        "3.000", "3000 khách", "khách hàng mô phỏng",
    ),
    "USER_GUIDE": (
        "hướng dẫn", "cách dùng", "cách sử dụng", "trang tổng quan",
        "danh sách ưu tiên", "màn hình", "cách xem", "làm sao", "làm thế nào",
        "cách mở hồ sơ",
    ),
    "ARCHITECTURE": (
        "kiến trúc", "module", "luồng quyết định", "đường ống", "decision core",
        "layer", "frontend", "api", "cấu trúc code",
    ),
    "GRENNODE": (
        "greennode", "agentbase", "maas", "vdb", "vector database", "qwen",
        "glm", "gemma", "nền tảng", "embedding",
    ),
    "TRUST": (
        "tin cậy", "an toàn", "bảo mật", "guardrail", "bằng chứng", "kiểm chứng",
        "fidelity", "override", "bịa", "unknown cif", "an toàn",
    ),
    "EVALUATION": (
        "đánh giá", "golden", "evaluation", "chỉ số", "recall", "mrr", "độ chính xác",
        "grounding", "kết quả eval",
    ),
    "ROADMAP": (
        "lộ trình", "roadmap", "tiếp theo", "future", "kế hoạch", "kế tiếp",
        "các bước", "hướng phát triển",
    ),
}

_SIMULATE_KEYWORDS = ("mô phỏng", "simulate", "simulation", "what if", "what-if", "kịch bản", "giả lập")

_DECISION_KEYWORDS = (
    "quyết định", "hành động", "nên gọi", "tại sao", "tuyến", "nba",
    "đề xuất", "ưu tiên", "khi nào", "next best action", "xử lý", "treatment",
    "channel", "kênh", "gọi",
)

_FACT_KEYWORDS = (
    "dư nợ", "dpd", "dòng tiền", "ptp", "cam kết", "thông tin", "bao nhiêu",
    "số dư", "lịch sử", "sdt", "liên hệ được", "khoản vay",
)


def extract_cif(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    match = _CIF_PATTERN.search(text)
    return match.group(0) if match else None


def classify_question_type(text: str) -> QuestionType:
    if not isinstance(text, str) or not text.strip():
        return "LOW_CONFIDENCE"
    blocked, _ = security_scan(text)
    if blocked:
        return "SECURITY_SENSITIVE"
    lowered = text.lower()
    cif = extract_cif(text)
    if cif:
        hypothetical = any(kw in lowered for kw in _SIMULATE_KEYWORDS) or (
            "nếu" in lowered and "thì" in lowered
        )
        if hypothetical:
            return "SIMULATION_REQUIRED"
        if any(kw in lowered for kw in _DECISION_KEYWORDS):
            return "CUSTOMER_DECISION_REQUIRED"
        return "CUSTOMER_FACT_REQUIRED"
    return "PROJECT_KNOWLEDGE"


def infer_topics(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    lowered = text.lower()
    hits: list[str] = []
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            hits.append(topic)
    return hits


def infer_audience(text: str) -> str:
    lowered = text.lower() if isinstance(text, str) else ""
    if any(kw in lowered for kw in ("module", "code", "api", "docker", "kiến trúc kỹ thuật", "unit test")):
        return "TECH"
    return "ALL"