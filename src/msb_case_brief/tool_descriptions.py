from __future__ import annotations

from .models import ToolSpec

TOOL_SPECS: dict[str, ToolSpec] = {
    "get_customer_360": ToolSpec(
        name="get_customer_360",
        purpose=(
            "Lấy thông tin tổng quan hiện tại của một CIF: dư nợ, DPD, phân khúc, "
            "trạng thái hồ sơ, và các facts tổng quan khác từ Decision Context đã chấp nhận."
        ),
        when_to_use=[
            "hỏi DPD hoặc quá hạn",
            "tổng dư nợ",
            "phân khúc khách hàng",
            "trạng thái hồ sơ",
            "facts tổng quan về khách hàng",
        ],
        when_not_to_use=[
            "chỉ hỏi policy/định nghĩa chung — dùng find_knowledge",
            "chỉ hỏi PTP — dùng get_ptp_context",
            "chỉ hỏi Decision Core result — dùng get_current_decision",
            "chỉ hỏi score breakdown — dùng get_score_breakdown",
        ],
        authority="Facts only. Does not decide route, score, treatment or channel.",
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "customer": "object", "debt": "object", "cashflow": "object",
                       "ptp": "object", "contact": "object", "policy": "object",
                       "recovery_opportunity": "object", "availability": "object"},
        timeout_ms=2000,
        fallback="Return empty customer dict; CaseContextBuilder marks missing_data.",
        permission="READ",
    ),
    "get_current_decision": ToolSpec(
        name="get_current_decision",
        purpose=(
            "Lấy kết quả chính thức hiện tại từ Decision Core (NBA engine): "
            "route, treatment, channel, score, rule_id, reason_code. "
            "Đây là nguồn authoritative cho mọi quyết định nghiệp vụ."
        ),
        when_to_use=[
            "giờ nên làm gì",
            "vì sao gọi/chờ/nhắc",
            "điểm hiện tại",
            "route hiện tại",
            "treatment hiện tại",
            "channel hiện tại",
            "quyết định hiện tại",
        ],
        when_not_to_use=[
            "chỉ hỏi policy/định nghĩa — dùng find_knowledge",
            "chỉ hỏi dòng tiền — dùng get_cashflow_summary",
            "chỉ hỏi PTP — dùng get_ptp_context",
            "giả định/kịch bản — dùng simulate_decision",
        ],
        authority=(
            "Authoritative source for route, score, treatment and channel. "
            "Never infer or replace these values using another tool or model."
        ),
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "final_route": "string", "treatment": "string",
                       "channel": "string", "rule_id": "string", "reason_code": "string",
                       "recovery_opportunity_score": "integer", "when": "object"},
        timeout_ms=2000,
        fallback="Return empty decision dict; validator rejects any brief citing decision facts.",
        permission="READ",
    ),
    "get_cashflow_summary": ToolSpec(
        name="get_cashflow_summary",
        purpose=(
            "Lấy các tín hiệu dòng tiền gần đây của một CIF: inflow_3d, inflow_7d, "
            "net_cashflow_30d, income_sources, liquidity ratio."
        ),
        when_to_use=[
            "hỏi tiền vào / dòng tiền",
            "tín hiệu tự thanh toán",
            "thay đổi tài chính gần đây",
            "lý do WAIT_SELF_CURE",
            "giả định liên quan inflow",
        ],
        when_not_to_use=[
            "chỉ hỏi CALL/CBS — dùng get_current_decision",
            "chỉ hỏi PTP — dùng get_ptp_context",
            "hỏi policy chung không gắn CIF — dùng find_knowledge",
        ],
        authority="Facts only. Does not determine treatment, channel or score.",
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "inflow_3d": "integer|null", "inflow_7d": "integer|null",
                       "net_cashflow_30d": "integer|null", "income_sources_30d": "array|null",
                       "liquidity_to_due_ratio": "decimal|null"},
        timeout_ms=2000,
        fallback="Return empty cashflow dict; CaseContextBuilder marks missing_data.",
        permission="READ",
    ),
    "get_ptp_context": ToolSpec(
        name="get_ptp_context",
        purpose=(
            "Lấy cam kết thanh toán gần nhất và trạng thái PTP: status, promise_date, "
            "promise_amount, actual_paid_amount, fulfillment ratio."
        ),
        when_to_use=[
            "PTP",
            "cam kết",
            "hứa trả",
            "thất hứa",
            "thanh toán một phần",
            "đã hẹn trả chưa",
            "cam kết gần nhất",
            "treatment liên quan PTP",
        ],
        when_not_to_use=[
            "chỉ hỏi dòng tiền — dùng get_cashflow_summary",
            "chỉ hỏi quyết định hiện tại — dùng get_current_decision",
        ],
        authority=(
            "Return observed PTP facts only. "
            "Do not infer willingness or intent beyond available data."
        ),
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "status": "string|null", "promise_date": "string|null",
                       "promise_amount": "integer|null", "actual_paid_amount": "integer|null",
                       "policy_fulfillment_ratio": "decimal|null"},
        timeout_ms=2000,
        fallback="Return empty PTP dict; CaseContextBuilder marks missing_data.",
        permission="READ",
    ),
    "get_contact_history": ToolSpec(
        name="get_contact_history",
        purpose=(
            "Lấy summary lịch sử liên hệ gần đây: outbound_attempts_30d, "
            "successful_outbound_calls_30d, latest_successful_outbound_date, "
            "technical_call_status_counts."
        ),
        when_to_use=[
            "hỏi lần gọi gần nhất",
            "đã liên hệ chưa",
            "khách có bắt máy không",
            "kết quả cuộc gọi",
            "callback",
            "VERIFY_CONTACT",
            "thay đổi từ lần liên hệ trước",
        ],
        when_not_to_use=[
            "chỉ hỏi quyết định hiện tại — dùng get_current_decision",
            "chỉ hỏi dòng tiền — dùng get_cashflow_summary",
        ],
        authority=(
            "Prefer summarized contact facts. "
            "Do not return large raw call-history payloads unless necessary."
        ),
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "outbound_attempts_30d": "integer",
                       "successful_outbound_calls_30d": "integer",
                       "latest_successful_outbound_date": "string|null",
                       "technical_call_status_counts": "object"},
        timeout_ms=2000,
        fallback="Return empty contact dict; CaseContextBuilder marks missing_data.",
        permission="READ",
    ),
    "get_score_breakdown": ToolSpec(
        name="get_score_breakdown",
        purpose=(
            "Lấy breakdown canonical của Recovery Opportunity score: "
            "business_urgency, ability_to_pay, willingness_to_pay, "
            "contactability, timing_opportunity, strategic_adjustment."
        ),
        when_to_use=[
            "hỏi vì sao điểm là X",
            "thành phần kéo điểm lên/xuống",
            "ability/willingness/contactability/timing",
            "giải thích score",
        ],
        when_not_to_use=[
            "chỉ hỏi quyết định hiện tại — dùng get_current_decision",
            "chỉ hỏi dòng tiền — dùng get_cashflow_summary",
        ],
        authority=(
            "Recovery Opportunity is a prioritization score, not payment probability. "
            "Never recalculate or modify it using the language model."
        ),
        input_schema={"cif": {"type": "string", "required": True}},
        output_schema={"cif": "string", "recovery_opportunity_score": "integer",
                       "component_breakdown": "array", "score_trace": "array"},
        timeout_ms=2000,
        fallback="Return empty breakdown dict; CaseContextBuilder marks missing_data.",
        permission="READ",
    ),
    "simulate_decision": ToolSpec(
        name="simulate_decision",
        purpose=(
            "Tính lại Decision Core trong một kịch bản giả định. "
            "Áp dụng thay đổi tạm thời lên context và replay NBA engine."
        ),
        when_to_use=[
            "nếu...",
            "giả sử...",
            "điều gì xảy ra nếu...",
            "nếu tiền vào bằng 0...",
            "nếu PTP thay đổi...",
        ],
        when_not_to_use=[
            "hỏi factual questions về current state — dùng get_current_decision",
            "chỉ hỏi policy — dùng find_knowledge",
        ],
        authority=(
            "Simulation Core remains authoritative. "
            "The language model only explains the result. "
            "Never mutate original customer data. "
            "Every output must be marked SIMULATION."
        ),
        input_schema={"cif": {"type": "string", "required": True},
                       "changes": {"type": "object", "required": False}},
        output_schema={"cif": "string", "before": "object", "after": "object",
                       "changes_applied": "object", "decision_changed": "boolean",
                       "diff": "array", "simulation_version": "string"},
        timeout_ms=3000,
        fallback="Return empty simulation result; brief marks simulation unavailable.",
        permission="COMPUTE",
    ),
    "find_knowledge": ToolSpec(
        name="find_knowledge",
        purpose=(
            "Tra cứu quy trình, định nghĩa, chính sách và tài liệu nghiệp vụ có nguồn. "
            "Sử dụng Project Knowledge RAG service."
        ),
        when_to_use=[
            "CALL/CBS nghĩa là gì",
            "PTP nghĩa là gì",
            "policy/rule hoạt động ra sao",
            "thuật ngữ nghiệp vụ",
            "hướng dẫn nghiệp vụ chung",
        ],
        when_not_to_use=[
            "current treatment — dùng get_current_decision",
            "current score — dùng get_score_breakdown",
            "current channel — dùng get_current_decision",
            "current route — dùng get_current_decision",
        ],
        authority=(
            "For customer-specific decisions use get_current_decision. "
            "Knowledge must not override Decision Core."
        ),
        input_schema={"question": {"type": "string", "required": True}},
        output_schema={"answer": "string", "sources": "array", "knowledge_type": "string",
                       "status": "string"},
        timeout_ms=5000,
        fallback="Return low-confidence refusal; brief omits knowledge_refs.",
        permission="READ",
    ),
}


def get_tool_spec(name: str) -> ToolSpec | None:
    return TOOL_SPECS.get(name)


def tool_description_for_planner(name: str) -> str:
    spec = TOOL_SPECS.get(name)
    if spec is None:
        return ""
    lines = [f"Tool: {spec.name}", f"Purpose: {spec.purpose}"]
    lines.append("Use when: " + "; ".join(spec.when_to_use))
    lines.append("Do NOT use when: " + "; ".join(spec.when_not_to_use))
    lines.append(f"Authority: {spec.authority}")
    lines.append(f"Permission: {spec.permission}")
    lines.append(f"Timeout: {spec.timeout_ms}ms")
    lines.append(f"Fallback: {spec.fallback}")
    return "\n".join(lines)


def registry_description() -> str:
    return "\n\n".join(tool_description_for_planner(name) for name in TOOL_SPECS)
