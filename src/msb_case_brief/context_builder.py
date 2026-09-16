from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import CaseContext, CaseState


def _safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    result = data
    for key in keys:
        if not isinstance(result, dict):
            return default
        result = result.get(key, default)
    return result


def _format_amount_vn(value: Any) -> str:
    n = int(value or 0)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} tỷ đồng"
    if n >= 1_000_000:
        return f"{n // 1_000_000} triệu đồng"
    return f"{n:,} đồng".replace(",", ".")


class CaseContextBuilder:
    """Normalize raw tool results into a canonical CaseContext.

    Does not pass large raw DB/tool payloads directly to GLM.
    Extracts only the fields needed for the brief.
    """

    def build(
        self,
        cif: str,
        customer_360: dict[str, Any] | None = None,
        decision: dict[str, Any] | None = None,
        cashflow: dict[str, Any] | None = None,
        ptp: dict[str, Any] | None = None,
        contact: dict[str, Any] | None = None,
        score_breakdown: dict[str, Any] | None = None,
        simulation: dict[str, Any] | None = None,
        knowledge: list[dict[str, Any]] | None = None,
        state: CaseState = "BASELINE",
    ) -> CaseContext:
        ctx = customer_360 or {}
        dec = decision or {}
        cash = cashflow or ctx.get("cashflow", {})
        ptp_data = ptp or ctx.get("ptp", {})
        contact_data = contact or ctx.get("contact", {})
        score = score_breakdown or ctx.get("recovery_opportunity", {})

        missing: list[str] = []
        if not ctx:
            missing.append("customer_360")
        if not dec:
            missing.append("decision")
        if not cash:
            missing.append("cashflow")
        if not ptp_data:
            missing.append("ptp")
        if not contact_data:
            missing.append("contact")
        if not score:
            missing.append("score_breakdown")

        availability = ctx.get("availability", {})
        data_quality: dict[str, Any] = {}
        for key in ("cashflow_available", "payment_available", "ptp_available",
                     "call_history_available", "operation_history_available"):
            data_quality[key] = "AVAILABLE" if availability.get(key) else "MISSING"

        customer_summary = {
            "cif": cif,
            "customer_name": ctx.get("customer", {}).get("customer_name", ""),
            "segment": ctx.get("customer", {}).get("segment", ""),
            "max_dpd_cif": ctx.get("debt", {}).get("max_dpd_cif"),
            "total_outstanding_cif": ctx.get("debt", {}).get("total_outstanding_cif"),
            "loan_count": ctx.get("debt", {}).get("loan_count"),
        }

        decision_summary = {
            "final_route": dec.get("final_route", ""),
            "treatment": dec.get("treatment", ""),
            "channel": dec.get("channel", ""),
            "rule_id": dec.get("rule_id", ""),
            "reason_code": dec.get("reason_code", ""),
            "recovery_opportunity_score": dec.get("recovery_opportunity_score"),
            "when": dec.get("when", {}),
        }

        cashflow_summary = {
            "inflow_3d": cash.get("inflow_3d"),
            "inflow_7d": cash.get("inflow_7d"),
            "net_cashflow_30d": cash.get("net_cashflow_30d"),
            "income_sources_30d": cash.get("income_sources_30d"),
            "liquidity_to_due_ratio": cash.get("liquidity_to_due_ratio"),
        }

        ptp_summary = {
            "status": ptp_data.get("status"),
            "promise_date": ptp_data.get("promise_date"),
            "promise_amount": ptp_data.get("promise_amount"),
            "actual_paid_amount": ptp_data.get("actual_paid_amount"),
            "policy_fulfillment_ratio": ptp_data.get("policy_fulfillment_ratio"),
        }

        contact_summary = {
            "outbound_attempts_30d": contact_data.get("outbound_attempts_30d", 0),
            "successful_outbound_calls_30d": contact_data.get("successful_outbound_calls_30d", 0),
            "latest_successful_outbound_date": contact_data.get("latest_successful_outbound_date"),
            "technical_call_status_counts": contact_data.get("technical_call_status_counts", {}),
        }

        score_summary = {
            "recovery_opportunity_score": score.get("recovery_opportunity_score"),
            "business_urgency_score": score.get("business_urgency_score"),
            "ability_to_pay_score": score.get("ability_to_pay_score"),
            "willingness_to_pay_score": score.get("willingness_to_pay_score"),
            "contactability_score": score.get("contactability_score"),
            "timing_opportunity_score": score.get("timing_opportunity_score"),
            "strategic_adjustment_score": score.get("strategic_adjustment_score"),
            "component_breakdown": score.get("component_breakdown", []),
        }

        sim_summary: dict[str, Any] | None = None
        if simulation:
            sim_summary = {
                "before": simulation.get("before", {}),
                "after": simulation.get("after", {}),
                "decision_changed": simulation.get("decision_changed", False),
                "diff": simulation.get("diff", []),
                "changes_applied": simulation.get("changes_applied", {}),
            }

        return CaseContext(
            cif=cif,
            as_of=datetime.now(timezone.utc).isoformat(),
            state=state,
            customer=customer_summary,
            decision=decision_summary,
            score_breakdown=score_summary,
            cashflow=cashflow_summary,
            ptp=ptp_summary,
            contact=contact_summary,
            simulation=sim_summary,
            knowledge=knowledge or [],
            missing_data=missing,
            data_quality=data_quality,
        )
