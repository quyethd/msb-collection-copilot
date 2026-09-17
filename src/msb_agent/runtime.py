from __future__ import annotations

from typing import Any, Callable, Sequence

from .llm import LLMClient
from .models import (AGENT_VERSION, CANONICAL_MODEL, SIMULATE_RESULT, AgentResponse,
                     decision_from_nba)
from .router import detect_question_intent

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]
_OVERRIDE_NOTICE = " The agent cannot override accepted collection policy."

_TREATMENT_VN: dict[str, str] = {
    "WAIT": "Chờ theo dõi",
    "WAIT_SELF_CURE": "Chờ khách hàng tự thanh toán",
    "REMIND": "Nhắc thanh toán",
    "CONTACT": "Liên hệ khách hàng",
    "PTP_FOLLOW_UP": "Theo dõi cam kết thanh toán",
    "PTP_RECOVERY": "Xử lý cam kết thanh toán không thực hiện",
    "PARTIAL_PAYMENT": "Theo dõi khoản thanh toán một phần",
    "CALLBACK": "Gọi lại theo lịch hẹn",
    "VERIFY_CONTACT": "Xác minh thông tin liên hệ",
    "ESCALATE": "Chuyển mức xử lý cao hơn",
}
_CHANNEL_VN: dict[str, str] = {
    "CALL": "Gọi điện",
    "SMS": "Tin nhắn SMS",
    "ZALO": "Zalo",
    "EMAIL": "Email",
    "FIELD": "Lực lượng hiện trường",
    "NONE": "Chưa cần liên hệ",
}
_REASON_VN: dict[str, str] = {
    "CALL_SELF_CURE": "Đáp ứng điều kiện chờ tự thanh toán",
    "CALL_DEFAULT": "Xử lý mặc định (gọi điện)",
    "CBS_DEFAULT": "Xử lý mặc định (CBS)",
    "OTHER_DEFAULT": "Xử lý mặc định (khác)",
    "HARD_SUPPRESSED": "Bị hạn chế xử lý",
    "BROKEN_PTP_RECENT_INFLOW": "Cam kết không thực hiện, có dòng tiền gần đây",
    "BROKEN_PTP": "Cam kết không thực hiện",
    "OPEN_PTP": "Đang cam kết thanh toán",
    "KEPT_PTP": "Đã thực hiện cam kết",
}


def _format_amount_vn(value: Any) -> str:
    n = int(value or 0)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} tỷ đồng"
    if n >= 1_000_000:
        return f"{n // 1_000_000} triệu đồng"
    return f"{n:,} đồng".replace(",", ".")


def _tool_ok(envelope: dict[str, Any]) -> bool:
    return bool(envelope.get("ok"))


def _tool_data(envelope: dict[str, Any]) -> dict[str, Any]:
    return envelope.get("data") or {}


def _call(tool_caller: ToolCaller, name: str, cif: str) -> dict[str, Any]:
    return tool_caller(name, {"cif": cif})


def _evidence_from_nba(nba: dict[str, Any]) -> list[dict[str, Any]]:
    facts = nba.get("evidence_refs", {}).get("selected_rule_facts", {})
    items: list[dict[str, Any]] = []
    label_map = {
        "max_dpd_cif": "DPD", "net_cashflow_30d": "net_cashflow_30d",
        "inflow_7d": "inflow_7d", "inflow_3d": "inflow_3d",
        "ptp_state": "PTP state", "final_route": "final_route",
        "hard_suppressed": "hard_suppressed", "cashflow_available": "cashflow_available",
        "latest_business_outcome": "latest_business_outcome",
        "source_next_action_date": "source_next_action_date", "promise_date": "promise_date",
    }
    for key, label in label_map.items():
        if key in facts:
            items.append({"factor": label, "value": facts[key], "source": "get_next_best_action"})
    best_window = nba.get("evidence_refs", {}).get("best_window")
    if best_window:
        items.append({"factor": "best_window", "value": best_window.get("windows", {}), "source": "get_next_best_action"})
    return items


def _evidence_from_context(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    debt = ctx.get("debt", {})
    items.append({"factor": "DPD", "value": debt.get("max_dpd_cif"), "source": "get_customer_360"})
    items.append({"factor": "total_outstanding", "value": debt.get("total_outstanding_cif"), "source": "get_customer_360"})
    items.append({"factor": "loan_count", "value": debt.get("loan_count"), "source": "get_customer_360"})
    cash = ctx.get("cashflow", {})
    items.append({"factor": "inflow_3d", "value": cash.get("inflow_3d"), "source": "get_customer_360"})
    items.append({"factor": "inflow_7d", "value": cash.get("inflow_7d"), "source": "get_customer_360"})
    items.append({"factor": "net_cashflow_30d", "value": cash.get("net_cashflow_30d"), "source": "get_customer_360"})
    ptp = ctx.get("ptp", {})
    items.append({"factor": "PTP_status", "value": ptp.get("status"), "source": "get_customer_360"})
    items.append({"factor": "PTP_promise_date", "value": ptp.get("promise_date"), "source": "get_customer_360"})
    policy = ctx.get("policy", {})
    items.append({"factor": "final_route", "value": policy.get("final_route"), "source": "get_customer_360"})
    items.append({"factor": "hard_suppressed", "value": policy.get("hard_suppressed"), "source": "get_customer_360"})
    recovery = ctx.get("recovery_opportunity", {})
    items.append({"factor": "recovery_opportunity_score", "value": recovery.get("recovery_opportunity_score"), "source": "get_customer_360"})
    contact = ctx.get("contact", {})
    items.append({"factor": "outbound_attempts_30d", "value": contact.get("outbound_attempts_30d"), "source": "get_customer_360"})
    items.append({"factor": "successful_outbound_calls_30d", "value": contact.get("successful_outbound_calls_30d"), "source": "get_customer_360"})
    return items


def _technical_from_nba(nba: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": nba.get("rule_id", ""),
        "treatment": nba.get("treatment", ""),
        "channel": nba.get("channel", ""),
        "reason_code": nba.get("reason_code", ""),
        "final_route": nba.get("final_route", ""),
        "objective": nba.get("objective", ""),
    }


def _treatment_vn(treatment: str) -> str:
    return _TREATMENT_VN.get(treatment, treatment)


def _channel_vn(channel: str) -> str:
    return _CHANNEL_VN.get(channel, channel)


def _reason_vn(reason: str) -> str:
    return _REASON_VN.get(reason, reason)


def _build_why_no_call_sections(nba: dict[str, Any], facts: dict[str, Any],
                                 ctx: dict[str, Any] | None) -> tuple[str, list[dict[str, Any]]]:
    treatment_label = _treatment_vn(nba["treatment"])
    dpd = facts.get("max_dpd_cif")
    inflow_7d = facts.get("inflow_7d")
    net_30d = facts.get("net_cashflow_30d")
    ptp_state = facts.get("ptp_state")
    promise_date = facts.get("promise_date")

    reasons: list[str] = []
    if dpd is not None:
        reasons.append(f"Khách hàng đang quá hạn {dpd} ngày.")
    if inflow_7d is not None and int(inflow_7d or 0) > 0:
        reasons.append(f"Trong 7 ngày gần nhất có {_format_amount_vn(inflow_7d)} tiền vào.")
    if net_30d is not None:
        reasons.append(f"Dòng tiền ròng 30 ngày gần nhất là {_format_amount_vn(net_30d)}.")
    if ptp_state and ptp_state != "NONE":
        ptp_label = {"OPEN": "đang cam kết thanh toán", "BROKEN": "có cam kết không thực hiện"}.get(ptp_state, ptp_state)
        reasons.append(f"Hiện {ptp_label}.")
    else:
        reasons.append("Hiện chưa có cam kết thanh toán cần xử lý ngay.")
    reasons.append("Với các tín hiệu hiện tại, khách hàng đáp ứng điều kiện để ưu tiên "
                    "chờ tự thanh toán thay vì liên hệ ngay.")

    sections: list[dict[str, Any]] = [
        {"title": "Đề xuất hiện tại", "content": treatment_label},
        {"title": "Vì sao?", "items": reasons},
        {"title": "Cán bộ cần làm gì?",
         "content": "Chưa cần liên hệ tại thời điểm này. Tiếp tục theo dõi thay đổi về "
                     "dòng tiền và cam kết thanh toán."},
    ]
    summary = f"Đề xuất: {treatment_label}. " + " ".join(reasons[:3])
    return summary, sections


def _build_summary_sections(nba: dict[str, Any], facts: dict[str, Any],
                             ctx: dict[str, Any] | None) -> tuple[str, list[dict[str, Any]]]:
    treatment_label = _treatment_vn(nba["treatment"])
    channel_label = _channel_vn(nba.get("channel", "NONE"))
    dpd = facts.get("max_dpd_cif")
    inflow_7d = facts.get("inflow_7d")
    net_30d = facts.get("net_cashflow_30d")
    ptp_state = facts.get("ptp_state")
    outstanding = None
    if ctx:
        outstanding = ctx.get("debt", {}).get("total_outstanding_cif")

    bullets: list[str] = []
    if outstanding is not None:
        bullets.append(f"Dư nợ hiện tại: {_format_amount_vn(outstanding)}.")
    if dpd is not None:
        bullets.append(f"Quá hạn cao nhất: {dpd} ngày.")
    if inflow_7d is not None and int(inflow_7d or 0) > 0:
        bullets.append(f"Tiền vào 7 ngày gần nhất: {_format_amount_vn(inflow_7d)}.")
    if net_30d is not None:
        bullets.append(f"Dòng tiền ròng 30 ngày: {_format_amount_vn(net_30d)}.")
    if ptp_state and ptp_state != "NONE":
        ptp_label = {"OPEN": "Đang cam kết thanh toán", "BROKEN": "Cam kết không thực hiện"}.get(ptp_state, ptp_state)
        bullets.append(f"Trạng thái cam kết: {ptp_label}.")
    else:
        bullets.append("Hiện chưa có cam kết thanh toán.")
    bullets.append(f"Hành động đề xuất hiện tại: {treatment_label}.")
    bullets.append(f"Kênh xử lý: {channel_label}.")

    sections: list[dict[str, Any]] = [
        {"title": "Tóm tắt tình trạng", "items": bullets},
    ]
    summary = f"{treatment_label} · {channel_label}. " + " ".join(bullets[:4])
    return summary, sections


def _build_change_factors_sections(nba: dict[str, Any], facts: dict[str, Any],
                                    ctx: dict[str, Any] | None) -> tuple[str, list[dict[str, Any]]]:
    factors: list[str] = []
    inflow = facts.get("inflow_7d")
    net = facts.get("net_cashflow_30d")
    ptp = facts.get("ptp_state")
    promise = facts.get("promise_date")

    factors.append("Thay đổi dòng tiền gần đây (tiền vào mới hoặc giảm dòng tiền ròng).")
    if ptp == "OPEN" or promise:
        factors.append("Có cam kết thanh toán mới hoặc thay đổi ngày cam kết.")
    else:
        factors.append("Có cam kết thanh toán mới từ khách hàng.")
    factors.append("Cam kết thanh toán không được thực hiện (nếu đã có cam kết trước đó).")
    factors.append("Kết quả tương tác mới (cuộc gọi, SMS, Zalo).")

    sections: list[dict[str, Any]] = [
        {"title": "Yếu tố có thể thay đổi quyết định", "items": factors},
        {"title": "Lưu ý",
         "content": "Hệ thống chỉ thay đổi đề xuất khi có sự thay đổi thực tế về "
                     "tín hiệu hoặc kết quả tương tác."},
    ]
    summary = "Các yếu tố có thể thay đổi quyết định: thay đổi dòng tiền, cam kết thanh toán, và kết quả tương tác."
    return summary, sections


def _plan_summary(nba: dict[str, Any], llm: LLMClient | None) -> tuple[str, str | None]:
    treatment_label = _treatment_vn(nba["treatment"])
    channel_label = _channel_vn(nba.get("channel", "NONE"))
    route_label = _channel_vn(nba.get("final_route", ""))
    facts = nba.get("evidence_refs", {}).get("selected_rule_facts", {})
    dpd = facts.get("max_dpd_cif")
    inflow_7d = facts.get("inflow_7d")
    detail_lines = []
    if dpd is not None:
        detail_lines.append(f"Quá hạn: {dpd} ngày")
    if inflow_7d is not None:
        detail_lines.append(f"Tiền vào 7 ngày: {_format_amount_vn(inflow_7d)}")
    detail_str = "; ".join(detail_lines)

    if detail_str:
        template = (
            f"Hệ thống đề xuất: {treatment_label}.\n"
            f"Tuyến xử lý: {route_label} · Kênh: {channel_label}.\n"
            f"{detail_str}"
        )
    else:
        template = (
            f"Hệ thống đề xuất: {treatment_label}.\n"
            f"Tuyến xử lý: {route_label} · Kênh: {channel_label}."
        )
    if llm is None:
        return template, None
    prompt = (
        "Bạn là trợ lý thu hồi nợ của MSB. Tóm tắt quyết định thu hồi hiện tại "
        "cho nhân viên thu hồi bằng tiếng Việt ngắn gọn (1-2 câu). "
        "KHÔNG thay đổi, KHÔNG đề xuất khác với quyết định đã cho. "
        "Dùng 'Hệ thống đề xuất...' hoặc 'Dựa trên thông tin hiện có...' "
        "KHÔNG dùng từ 'AI quyết định'.\n"
        + template)
    content, model = llm.complete(prompt, max_tokens=150, temperature=0)
    return content or template, model


def _explain_summary(nba: dict[str, Any], llm: LLMClient | None,
                     message: str | None = None) -> tuple[str, str | None, list[dict[str, Any]], str | None]:
    facts = nba.get("evidence_refs", {}).get("selected_rule_facts", {})
    intent = detect_question_intent(message) if message else None

    if intent == "WHY_NO_CALL":
        summary, sections = _build_why_no_call_sections(nba, facts, None)
        if llm is None:
            return summary, None, sections, intent
        prompt = (
            "Giải thích ngắn gọn bằng tiếng Việt vì sao hệ thống giữ nguyên quyết định "
            "hiện tại. Chỉ dùng các dữ kiện và đề xuất dưới đây; không thay đổi route, "
            "treatment, channel hoặc rule_id, không tạo dữ kiện mới.\n"
            + summary + "\nDữ kiện: " + "; ".join(f"{key}={value}" for key, value in facts.items())
        )
        content, model = llm.complete(prompt, max_tokens=200, temperature=0)
        return content or summary, model, sections, intent
    if intent == "SUMMARY":
        summary, sections = _build_summary_sections(nba, facts, None)
        return summary, None, sections, intent
    if intent == "CHANGE_FACTORS":
        summary, sections = _build_change_factors_sections(nba, facts, None)
        return summary, None, sections, intent

    treatment_label = _treatment_vn(nba["treatment"])
    channel_label = _channel_vn(nba.get("channel", "NONE"))
    route_label = _channel_vn(nba.get("final_route", ""))

    template = (
        f"Hệ thống đề xuất: {treatment_label}.\n"
        f"Tuyến xử lý: {route_label} · Kênh: {channel_label}.\n"
        f"Lý do: {_reason_vn(nba.get('reason_code', ''))}."
    )
    if llm is None:
        return template, None, [], None
    prompt = (
        "Bạn là trợ lý thu hồi nợ của MSB. Giải thích cho nhân viên thu hồi "
        "bằng tiếng Việt ngắn gọn tại sao hệ thống đưa ra quyết định hiện tại. "
        "CHỈ dựa trên bằng chứng đã cung cấp, KHÔNG phát miny lý do mới. "
        "KHÔNG thay đổi quyết định. KHÔNG dùng 'DETERMINISTIC DECISION' hay 'AI EXPLANATION'. "
        "Dùng 'Hệ thống đề xuất...' hoặc 'Dựa trên thông tin hiện có...'.\n"
        + template)
    content, model = llm.complete(prompt, max_tokens=200, temperature=0)
    return content or template, model, [], None


def _investigate_summary(cif: str, evidence: list[dict[str, Any]],
                         llm: LLMClient | None) -> tuple[str, str | None]:
    lines = [f"{item['factor']}: {item['value']}" for item in evidence]
    template = f"Thông tin khách hàng {cif}:\n" + "\n".join(lines)
    if llm is None:
        return template, None
    prompt = (
        "Bạn là trợ lý thu hồi nợ của MSB. Tóm tắt bằng tiếng Việt ngắn gọn "
        "những thông tin quan trọng về khách hàng. KHÔNG phát miny dữ liệu. "
        "KHÔNG đề xuất hành động.\n"
        + template)
    content, model = llm.complete(prompt, max_tokens=150, temperature=0)
    return content or template, model


class AgentRuntime:
    def __init__(self, tool_caller: ToolCaller, llm_client: LLMClient | None = None):
        self.tool_caller = tool_caller
        self.llm_client = llm_client

    def invoke(self, mode: str, cif: str | None, message: str | None = None,
               changes: dict[str, Any] | None = None) -> AgentResponse:
        if mode not in ("PLAN", "INVESTIGATE", "EXPLAIN", "SIMULATE"):
            return AgentResponse("error", "PLAN", cif, None, [], "Chế độ không hợp lệ", [], None, True, AGENT_VERSION,
                                 error={"code": "INVALID_ARGUMENT", "message": f"Unknown mode: {mode}"})
        if mode == "SIMULATE":
            return self._simulate(cif, changes or {})
        if not cif:
            return AgentResponse("error", mode, None, None, [], "Chưa cung cấp mã khách hàng", [], None, True, AGENT_VERSION,
                                 error={"code": "INVALID_ARGUMENT", "message": "A synthetic CIF is required"})
        nba_envelope = self.tool_caller("get_next_best_action", {"cif": cif})
        if not _tool_ok(nba_envelope):
            code = nba_envelope.get("error", {}).get("code", "INTERNAL_ERROR")
            return AgentResponse("error", mode, cif, None, [],
                                 f"Không tìm thấy khách hàng {cif}. Vui lòng kiểm tra lại mã khách hàng.",
                                 ["get_next_best_action"],
                                 None, True, AGENT_VERSION,
                                 error={"code": code, "message": f"CIF {cif!r} was not found"})
        if mode == "PLAN":
            return self._plan(cif, nba_envelope)
        if mode == "EXPLAIN":
            return self._explain(cif, nba_envelope, message)
        if mode == "INVESTIGATE":
            return self._investigate(cif, nba_envelope)
        return AgentResponse("error", mode, cif, None, [], "Unreachable", [], None, True, AGENT_VERSION,
                             error={"code": "INTERNAL_ERROR", "message": "Unreachable"})

    def _plan(self, cif: str, nba_envelope: dict[str, Any]) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        ctx_envelope = _call(self.tool_caller, "get_customer_360", cif)
        ctx = _tool_data(ctx_envelope) if _tool_ok(ctx_envelope) else {}
        evidence = _evidence_from_nba(nba)
        summary, model = _plan_summary(nba, self.llm_client)
        return AgentResponse("success", "PLAN", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action", "get_customer_360"], model, True, AGENT_VERSION,
                             technical=_technical_from_nba(nba))

    def _explain(self, cif: str, nba_envelope: dict[str, Any],
                 message: str | None = None) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        evidence = _evidence_from_nba(nba)
        summary, model, sections, intent = _explain_summary(nba, self.llm_client, message)
        return AgentResponse("success", "EXPLAIN", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action"], model, True, AGENT_VERSION,
                             sections=sections, technical=_technical_from_nba(nba),
                             question_intent=intent)

    def _investigate(self, cif: str, nba_envelope: dict[str, Any]) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        ctx_envelope = _call(self.tool_caller, "get_customer_360", cif)
        ctx = _tool_data(ctx_envelope) if _tool_ok(ctx_envelope) else {}
        evidence = _evidence_from_context(ctx) if ctx else _evidence_from_nba(nba)
        evidence.append({"factor": "NBA_rule_id", "value": nba["rule_id"], "source": "get_next_best_action"})
        evidence.append({"factor": "NBA_treatment", "value": nba["treatment"], "source": "get_next_best_action"})
        summary, model = _investigate_summary(cif, evidence, self.llm_client)
        return AgentResponse("success", "INVESTIGATE", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action", "get_customer_360"], model, True, AGENT_VERSION,
                             technical=_technical_from_nba(nba))

    def _simulate(self, cif: str | None, changes: dict[str, Any]) -> AgentResponse:
        if not cif:
            return AgentResponse("error", "SIMULATE", cif, None, [], "Chưa cung cấp mã khách hàng cho mô phỏng.",
                                 [], None, True, AGENT_VERSION,
                                 error={"code": "INVALID_ARGUMENT", "message": "A synthetic CIF is required for simulation"})
        sim_envelope = self.tool_caller("simulate_decision", {"cif": cif, "changes": changes})
        if not _tool_ok(sim_envelope):
            error = sim_envelope.get("error", {})
            return AgentResponse("error", "SIMULATE", cif, None, [],
                                 f"Mô phỏng thất bại: {error.get('message', 'lỗi không xác định')}",
                                 ["simulate_decision"], None, True, AGENT_VERSION,
                                 error={"code": error.get("code", "INTERNAL_ERROR"),
                                        "message": error.get("message", "Simulation failed")})
        sim_data = _tool_data(sim_envelope)
        diff = sim_data.get("diff", [])
        after_decision = sim_data.get("after", {})
        summary, model = self._simulate_summary(sim_data, self.llm_client)
        return AgentResponse("success", "SIMULATE", cif, after_decision, diff, summary,
                             ["simulate_decision"], model, True, AGENT_VERSION,
                             simulation=sim_data,
                             technical={
                                 "before_rule_id": sim_data.get("before", {}).get("rule_id", ""),
                                 "after_rule_id": after_decision.get("rule_id", ""),
                                 "decision_changed": sim_data.get("decision_changed", False),
                             })

    def _simulate_summary(self, sim_data: dict[str, Any], llm: LLMClient | None) -> tuple[str, str | None]:
        before = sim_data.get("before", {})
        after = sim_data.get("after", {})
        changed = sim_data.get("decision_changed", False)
        before_label = _treatment_vn(before.get("treatment", "?"))
        after_label = _treatment_vn(after.get("treatment", "?"))
        before_channel = _channel_vn(before.get("channel", "NONE"))
        after_channel = _channel_vn(after.get("channel", "NONE"))
        template = (
            f"Kết quả mô phỏng:\n"
            f"  Trước: {before_label} · Kênh: {before_channel}\n"
            f"  Sau: {after_label} · Kênh: {after_channel}\n"
            f"  Quyết định thay đổi: {'Có' if changed else 'Không'}\n"
            f"Đây là kết quả mô phỏng. Dữ liệu gốc của khách hàng không bị thay đổi."
        )
        if llm is None:
            return template, None
        prompt = (
            "Bạn là trợ lý thu hồi nợ của MSB. Giải thích kết quả mô phỏng "
            "bằng tiếng Việt thân thiện với nhân viên nghiệp vụ. "
            "KHÔNG thay đổi quyết định. KHÔNG tính quyết định mới. "
            "KHÔNG hiển thị mã quy tắc nội bộ (NBA-xxx). "
            "Chỉ giải thích thay đổi và lý do, dùng tiếng Việt.\n" + template)
        content, model = llm.complete(prompt, max_tokens=250, temperature=0)
        if content and ("NBA-" in content or "nba-" in content.lower()):
            content = None
        return content or template, model
