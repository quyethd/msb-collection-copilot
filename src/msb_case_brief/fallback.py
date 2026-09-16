from __future__ import annotations

from typing import Any

from .context_builder import CaseContextBuilder
from .models import (CaseBrief, CaseContext, KeyEvidence, KnowledgeRef, DISCLAIMER,
                     AgentPath)


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
    "CALL": "Gọi điện", "SMS": "Tin nhắn SMS", "ZALO": "Zalo",
    "EMAIL": "Email", "FIELD": "Lực lượng hiện trường", "NONE": "Chưa cần liên hệ",
}


def _format_amount_vn(value: Any) -> str:
    n = int(value or 0)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} tỷ đồng"
    if n >= 1_000_000:
        return f"{n // 1_000_000} triệu đồng"
    return f"{n:,} đồng".replace(",", ".")


class CaseBriefFallback:
    """Level 3: Deterministic safe template.

    Produces a valid CaseBrief without any LLM calls.
    Always works. Never creates business decisions.
    """

    def generate(self, context: CaseContext) -> CaseBrief:
        dec = context.decision
        cust = context.customer
        cash = context.cashflow
        ptp = context.ptp
        contact = context.contact

        cif = context.cif
        treatment = dec.get("treatment", "")
        channel = dec.get("channel", "")
        route = dec.get("final_route", "")
        score = dec.get("recovery_opportunity_score")

        treatment_label = _TREATMENT_VN.get(treatment, treatment or "Chưa có đề xuất")
        channel_label = _CHANNEL_VN.get(channel, channel or "—")

        headline = f"Hồ sơ {cif}: {treatment_label}"

        summary_parts = [f"Đề xuất hiện tại: {treatment_label}."]
        if route:
            summary_parts.append(f"Tuyến xử lý: {route}.")
        if channel:
            summary_parts.append(f"Kênh: {channel_label}.")
        if score is not None:
            summary_parts.append(f"Điểm cơ hội thu hồi: {score}.")
        summary = " ".join(summary_parts)

        evidence: list[KeyEvidence] = []
        dpd = cust.get("max_dpd_cif")
        if dpd is not None:
            evidence.append(KeyEvidence(
                label="Quá hạn", value=f"{dpd} ngày",
                reason="DPD cao nhất trên các khoản vay",
                source="customer360",
            ))
        outstanding = cust.get("total_outstanding_cif")
        if outstanding is not None:
            evidence.append(KeyEvidence(
                label="Dư nợ", value=_format_amount_vn(outstanding),
                reason="Tổng dư nợ hiện tại",
                source="customer360",
            ))
        inflow_7d = cash.get("inflow_7d")
        if inflow_7d is not None:
            evidence.append(KeyEvidence(
                label="Tiền vào 7 ngày", value=_format_amount_vn(inflow_7d),
                reason="Dòng tiền vào gần đây",
                source="cashflow",
            ))
        net_30d = cash.get("net_cashflow_30d")
        if net_30d is not None:
            evidence.append(KeyEvidence(
                label="Dòng tiền ròng 30 ngày", value=_format_amount_vn(net_30d),
                reason="Dòng tiền ròng",
                source="cashflow",
            ))
        ptp_status = ptp.get("status")
        if ptp_status:
            ptp_label = {"OPEN": "Đang cam kết", "BROKEN": "Không thực hiện",
                         "KEPT": "Đã thực hiện", "PARTIAL": "Thanh toán một phần"}.get(ptp_status, ptp_status)
            evidence.append(KeyEvidence(
                label="Cam kết thanh toán", value=ptp_label,
                reason="Trạng thái PTP hiện tại",
                source="ptp",
            ))
        if score is not None:
            evidence.append(KeyEvidence(
                label="Điểm cơ hội thu hồi", value=str(score),
                reason="Recovery Opportunity score",
                source="decision",
            ))

        decision_explanation: list[str] = []
        if treatment == "WAIT_SELF_CURE":
            decision_explanation.append(
                "Hệ thống đề xuất chờ khách hàng tự thanh toán vì có dòng tiền vào gần đây."
            )
        elif treatment in ("CONTACT", "CALLBACK"):
            decision_explanation.append(
                f"Hệ thống đề xuất liên hệ khách hàng qua {channel_label}."
            )
        elif treatment == "REMIND":
            decision_explanation.append("Hệ thống đề xuất nhắc thanh toán.")
        else:
            decision_explanation.append(f"Hệ thống đề xuất: {treatment_label}.")

        officer_focus: list[str] = []
        if context.missing_data:
            officer_focus.append(f"Dữ liệu thiếu: {', '.join(context.missing_data)}.")
        if ptp_status == "OPEN":
            officer_focus.append("Theo dõi ngày cam kết thanh toán.")
        if ptp_status == "BROKEN":
            officer_focus.append("Đánh giá lại cam kết không thực hiện.")
        if inflow_7d is not None and inflow_7d == 0:
            officer_focus.append("Tiền vào 7 ngày bằng 0 — theo dõi dòng tiền.")
        if not officer_focus:
            officer_focus.append("Theo dõi thay đổi dòng tiền và kết quả tương tác.")

        return CaseBrief(
            headline=headline,
            summary=summary,
            key_evidence=evidence,
            decision_explanation=decision_explanation,
            officer_focus=officer_focus,
            knowledge_refs=[],
            missing_data=context.missing_data,
            state=context.state,
            disclaimer=DISCLAIMER,
        )
