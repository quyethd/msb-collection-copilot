from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

from msb_policy.engine import PolicyResult


def as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime): return value.date()
    if isinstance(value, date): return value
    return date.fromisoformat(value[:10])


def as_datetime(value: str | datetime) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


def in_window(value: str | date | datetime, reference_date: date, days: int, offset: int = 0) -> bool:
    event_date = as_date(value)
    end = reference_date - timedelta(days=offset)
    start = reference_date - timedelta(days=offset + days - 1)
    return start <= event_date <= end


def derive_features(
    policy: PolicyResult,
    cashflows: Sequence[Mapping[str, Any]], payments: Sequence[Mapping[str, Any]],
    calls: Sequence[Mapping[str, Any]], operations: Sequence[Mapping[str, Any]],
    reference_date: date,
) -> dict[str, Any]:
    cash_available, payment_available = bool(cashflows), bool(payments)
    call_available, operation_available = bool(calls), bool(operations)
    ptp_available = policy.ptp_status is not None

    def cash_sum(direction: str, days: int, offset: int = 0) -> Decimal:
        return sum((Decimal(str(row["amount"])) for row in cashflows if row["direction"] == direction and in_window(row["transaction_date"], reference_date, days, offset)), Decimal(0))

    inflow_3d, inflow_7d, inflow_30d = cash_sum("IN", 3), cash_sum("IN", 7), cash_sum("IN", 30)
    outflow_30d = cash_sum("OUT", 30)
    window_nets = tuple(cash_sum("IN", 30, offset) - cash_sum("OUT", 30, offset) for offset in (0, 30, 60))
    income_sources = sorted({row["source_type"] for row in cashflows if row["direction"] == "IN" and in_window(row["transaction_date"], reference_date, 30) and row["source_type"] in {"SALARY", "BUSINESS_INCOME"}})

    recent_calls = [row for row in calls if in_window(row["call_time"], reference_date, 30)]
    outbound = [row for row in recent_calls if row.get("call_type") in {"OUTBOUND", "OUT"}]
    successful = [row for row in outbound if row.get("status") == "Success"]
    success_rate = Decimal(len(successful)) / Decimal(len(outbound)) if outbound else None
    latest_success_date = max((as_date(row["call_time"]) for row in successful), default=None)
    days_since_success = (reference_date - latest_success_date).days if latest_success_date else None
    recent_operations = [row for row in operations if in_window(row["created_at"], reference_date, 30)]
    utc_count = sum(row.get("operation_result") == "UTC" for row in recent_operations)
    nin_present = any(row.get("operation_result") == "NIN" for row in recent_operations)

    payment_after_contact_days: int | None = None
    for call in successful:
        call_time = as_datetime(str(call["call_time"]))
        for payment in payments:
            payment_time = as_datetime(str(payment["payment_date"]))
            if Decimal(str(payment["amount"])) > 0 and call_time < payment_time and as_date(payment_time) <= reference_date:
                delta = (payment_time.date() - call_time.date()).days
                if 0 <= delta <= 7 and (payment_after_contact_days is None or delta < payment_after_contact_days): payment_after_contact_days = delta

    liquidity = inflow_7d / policy.promise_amount if cash_available and policy.promise_amount is not None and policy.promise_amount > 0 else None
    return {
        "inflow_3d": inflow_3d, "inflow_7d": inflow_7d, "inflow_30d": inflow_30d,
        "outflow_30d": outflow_30d, "net_cashflow_30d": inflow_30d - outflow_30d,
        "net_cashflow_windows_30d": window_nets, "positive_cashflow_windows": sum(value > 0 for value in window_nets),
        "income_sources_30d": income_sources, "liquidity_to_due_ratio": liquidity,
        "outbound_attempts_30d": len(outbound), "successful_calls_30d": len(successful),
        "technical_success_rate_30d": success_rate, "days_since_last_successful_call": days_since_success,
        "utc_count_30d": utc_count, "nin_present_30d": nin_present,
        "call_or_operation_evidence_30d": bool(recent_calls or recent_operations),
        "payment_after_contact_days": payment_after_contact_days,
        "cashflow_available": cash_available, "payment_available": payment_available,
        "ptp_available": ptp_available, "call_history_available": call_available,
        "operation_history_available": operation_available,
    }
