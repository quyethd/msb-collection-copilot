from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Iterable, Mapping, Sequence

ROUTING_SEGMENTS = frozenset({"RED", "ORANGE", "YELLOW"})
BUSINESS_OUTCOMES = ("UTC", "PTP", "NPTP", "RTP", "NIN", "THIRT", "NA")
PTP_ABILITIES = frozenset({"CERTAIN", "HIGH", "MEDIUM", "LOW", "VERY_LOW"})
NEXT_ACTION_CHANNELS = frozenset({"CALL", "SMS", "ZALO", "EMAIL", "FIELD", "LETTER"})


@dataclass(frozen=True)
class PolicyConfig:
    """Explicit prototype configuration; one day is not a production MSB policy."""

    ptp_grace_days: int = 1

    def __post_init__(self) -> None:
        if self.ptp_grace_days < 0:
            raise ValueError("ptp_grace_days must be non-negative")


@dataclass(frozen=True)
class RuleTrace:
    rule_id: str
    result: str
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class PolicyResult:
    cif: str
    total_outstanding_cif: Decimal
    max_dpd_cif: int
    baseline_rank: int | None
    heatmap: str
    segment: str
    base_route: str
    challenge_override_route: str | None
    final_route: str
    ptp_status: str | None
    promise_date: date | None
    promise_amount: Decimal | None
    actual_paid_amount: Decimal | None
    fulfillment_ratio: Decimal | None
    payment_ptp_ability: str | None
    latest_business_outcome: str | None
    business_outcome_counts: Mapping[str, int]
    technical_call_status_counts: Mapping[str, int]
    source_next_action_date: datetime | None
    source_next_operation_channel: str | None
    hard_suppressed: bool
    hard_suppression_reason: str | None
    triggered_rule_ids: tuple[str, ...]
    policy_trace: tuple[RuleTrace, ...]

    def to_dict(self) -> dict[str, Any]:
        def encode(value: Any) -> Any:
            if isinstance(value, Decimal):
                return int(value) if value == value.to_integral_value() else str(value)
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if isinstance(value, tuple):
                return [encode(item) for item in value]
            if isinstance(value, dict):
                return {key: encode(item) for key, item in value.items()}
            return value

        return encode(asdict(self))


def _trace(rule_id: str, matched: bool, evidence: Mapping[str, Any]) -> RuleTrace:
    return RuleTrace(rule_id, "MATCH" if matched else "NO_MATCH", dict(evidence))


def _parse_date(value: str | date) -> date:
    return value if isinstance(value, date) and not isinstance(value, datetime) else date.fromisoformat(str(value)[:10])


def _parse_datetime(value: str | datetime) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


def _latest(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    return max(rows, key=lambda row: (str(row.get("created_at", "")), str(row.get("id", "")))) if rows else None


def derive_ptp(
    operations: Sequence[Mapping[str, Any]],
    payments: Sequence[Mapping[str, Any]],
    reference_date: date,
    config: PolicyConfig,
) -> tuple[dict[str, Any], list[RuleTrace]]:
    promises = [row for row in operations if row.get("operation_result") == "PTP"]
    latest = _latest(promises)
    if latest is None:
        return {
            "ptp_status": None, "promise_date": None, "promise_amount": None,
            "actual_paid_amount": None, "fulfillment_ratio": None,
            "payment_ptp_ability": None,
        }, []

    promise_date = _parse_date(latest["payment_ptp_date"])
    promise_amount = Decimal(str(latest["payment_ptp_number"]))
    if promise_amount <= 0:
        raise ValueError(f"{latest['id']}: PTP promise amount must be positive")
    actual_paid = sum(
        (Decimal(str(row["amount"])) for row in payments
         if row.get("linked_ptp_id") == latest["id"]
         and _parse_date(row["payment_date"]) <= reference_date),
        Decimal(0),
    )
    ability = str(latest.get("payment_ptp_ability") or "") or None
    if ability not in PTP_ABILITIES:
        raise ValueError(f"{latest['id']}: invalid payment_ptp_ability {ability!r}")

    kept = actual_paid >= promise_amount
    partial = Decimal(0) < actual_paid < promise_amount
    broken = actual_paid == 0 and reference_date > promise_date + timedelta(days=config.ptp_grace_days)
    open_ptp = not (kept or partial or broken)
    if kept:
        status, status_rule = "KEPT", "PTP-002"
    elif partial:
        status, status_rule = "PARTIAL", "PTP-003"
    elif broken:
        status, status_rule = "BROKEN", "PTP-004"
    else:
        status, status_rule = "OPEN", "PTP-001"
    fulfillment = min(actual_paid / promise_amount, Decimal(1))
    common = {"promise_id": latest["id"], "promise_date": promise_date.isoformat(), "promise_amount": promise_amount, "actual_paid_amount": actual_paid}
    traces = [
        _trace("PTP-001", open_ptp, {**common, "reference_date": reference_date.isoformat()}),
        _trace("PTP-002", kept, common),
        _trace("PTP-003", partial, common),
        _trace("PTP-004", broken, {**common, "reference_date": reference_date.isoformat(), "grace_days": config.ptp_grace_days}),
        _trace("PTP-005", True, {**common, "fulfillment_ratio": fulfillment}),
        _trace("PTP-006", True, {"payment_ptp_ability": ability, "source": "employee_assessment"}),
        _trace("PTP-007", True, {"payment_ptp_ability": ability, "use": "supporting_signal_only"}),
    ]
    return {"ptp_status": status, "promise_date": promise_date, "promise_amount": promise_amount, "actual_paid_amount": actual_paid, "fulfillment_ratio": fulfillment, "payment_ptp_ability": ability, "status_rule": status_rule}, traces


def evaluate_customer(
    customer: Mapping[str, Any],
    loans: Sequence[Mapping[str, Any]],
    assignment: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    payments: Sequence[Mapping[str, Any]],
    calls: Sequence[Mapping[str, Any]],
    reference_date: date,
    config: PolicyConfig = PolicyConfig(),
) -> PolicyResult:
    cif = str(customer["cif"])
    if not loans:
        raise ValueError(f"{cif}: at least one loan is required for AGG-001/AGG-002")
    if any(str(row["cif"]) != cif for row in (*loans, *operations, *payments, *calls)):
        raise ValueError(f"{cif}: related row belongs to another CIF")
    if str(assignment["cif"]) != cif:
        raise ValueError(f"{cif}: assignment belongs to another CIF")

    total = sum((Decimal(str(row["outstanding_amount"])) for row in loans), Decimal(0))
    max_dpd = max(int(row["dpd"]) for row in loans)
    heatmap, segment = str(customer["heatmap"]), str(customer["segment"])
    eligible = heatmap == "RED" and segment in ROUTING_SEGMENTS
    call_match, cbs_match = eligible and max_dpd >= 5, eligible and max_dpd < 5
    base_route = "CALL" if call_match else ("CBS" if cbs_match else "OTHER")
    override = str(assignment.get("challenge_override_route") or "") or None
    if override is not None and (override not in {"CALL", "CBS"} or override == base_route or base_route not in {"CALL", "CBS"}):
        raise ValueError(f"{cif}: challenge override must explicitly switch CALL and CBS")
    final_route = override or base_route

    trace = [
        _trace("AGG-001", True, {"loan_count": len(loans), "total_outstanding_cif": total}),
        _trace("AGG-002", True, {"loan_count": len(loans), "max_dpd_cif": max_dpd}),
        _trace("BASE-001", True, {"total_outstanding_cif": total, "max_dpd_cif": max_dpd}),
        _trace("ROUTE-001", call_match, {"heatmap": heatmap, "segment": segment, "max_dpd_cif": max_dpd}),
        _trace("ROUTE-002", cbs_match, {"heatmap": heatmap, "segment": segment, "max_dpd_cif": max_dpd}),
        _trace("ROUTE-003", override is not None, {"base_route": base_route, "challenge_override_route": override, "final_route": final_route}),
        _trace("ROUTE-004", override is not None, {"override_source": "explicit_synthetic_input" if override else None}),
        _trace("ROUTE-005", base_route == "OTHER", {"heatmap": heatmap, "segment": segment, "max_dpd_cif": max_dpd, "fallback": "OTHER"}),
    ]

    ordered_operations = sorted(operations, key=lambda row: (str(row.get("created_at", "")), str(row.get("id", ""))))
    outcome_counts = {name: sum(row.get("operation_result") == name for row in ordered_operations) for name in BUSINESS_OUTCOMES}
    latest_operation = _latest(ordered_operations)
    latest_outcome = str(latest_operation["operation_result"]) if latest_operation else None
    if latest_outcome is not None and latest_outcome not in BUSINESS_OUTCOMES:
        raise ValueError(f"{cif}: invalid business outcome {latest_outcome!r}")
    technical_counts = {status: sum(row.get("status") == status for row in calls) for status in sorted({str(row.get("status")) for row in calls})}
    trace.append(_trace("OUTCOME-001", bool(ordered_operations), {"latest_business_outcome": latest_outcome, "business_outcome_counts": outcome_counts}))

    latest_next_action = _latest([row for row in ordered_operations if row.get("next_action_date") or row.get("next_operation_channel")])
    source_next_date = _parse_datetime(str(latest_next_action["next_action_date"])) if latest_next_action and latest_next_action.get("next_action_date") else None
    source_next_channel = (str(latest_next_action.get("next_operation_channel") or "") or None) if latest_next_action else None
    if source_next_channel is not None and source_next_channel not in NEXT_ACTION_CHANNELS:
        raise ValueError(f"{cif}: invalid source next-operation channel {source_next_channel!r}")
    trace.append(_trace("OUTCOME-002", source_next_channel is not None, {"source_next_operation_channel": source_next_channel}))
    trace.append(_trace("OUTCOME-003", True, {"technical_call_status_counts": technical_counts, "latest_business_outcome": latest_outcome, "technical_status_used_as_business_outcome": False}))
    next_action_match = bool(latest_next_action and latest_next_action.get("operation_result") == "NA" and source_next_date is not None)
    trace.append(_trace("CONTACT-003", next_action_match, {"source_operation_result": latest_next_action.get("operation_result") if latest_next_action else None, "source_next_action_date": source_next_date.isoformat() if source_next_date else None, "source_next_operation_channel": source_next_channel, "fact_only": True}))

    ptp, ptp_trace = derive_ptp(ordered_operations, payments, reference_date, config)
    trace.extend(ptp_trace)
    triggered = tuple(item.rule_id for item in trace if item.result == "MATCH")
    return PolicyResult(
        cif=cif, total_outstanding_cif=total, max_dpd_cif=max_dpd, baseline_rank=None,
        heatmap=heatmap, segment=segment, base_route=base_route,
        challenge_override_route=override, final_route=final_route,
        ptp_status=ptp["ptp_status"], promise_date=ptp["promise_date"],
        promise_amount=ptp["promise_amount"], actual_paid_amount=ptp["actual_paid_amount"],
        fulfillment_ratio=ptp["fulfillment_ratio"], payment_ptp_ability=ptp["payment_ptp_ability"],
        latest_business_outcome=latest_outcome, business_outcome_counts=outcome_counts,
        technical_call_status_counts=technical_counts,
        source_next_action_date=source_next_date, source_next_operation_channel=source_next_channel,
        hard_suppressed=False, hard_suppression_reason=None,
        triggered_rule_ids=triggered, policy_trace=tuple(trace),
    )


def evaluate_dataset(
    customers: Iterable[Mapping[str, Any]], loans: Iterable[Mapping[str, Any]],
    assignments: Iterable[Mapping[str, Any]], operations: Iterable[Mapping[str, Any]],
    payments: Iterable[Mapping[str, Any]], calls: Iterable[Mapping[str, Any]],
    reference_date: date, config: PolicyConfig = PolicyConfig(),
) -> list[PolicyResult]:
    def group(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for row in rows: grouped.setdefault(str(row["cif"]), []).append(row)
        return grouped

    loan_map, operation_map, payment_map, call_map = map(group, (loans, operations, payments, calls))
    assignment_map = {str(row["cif"]): row for row in assignments}
    results = [evaluate_customer(row, loan_map.get(str(row["cif"]), []), assignment_map[str(row["cif"])], operation_map.get(str(row["cif"]), []), payment_map.get(str(row["cif"]), []), call_map.get(str(row["cif"]), []), reference_date, config) for row in customers]
    ordered = sorted(results, key=lambda item: (-item.total_outstanding_cif, -item.max_dpd_cif, item.cif))
    ranked = []
    for rank, item in enumerate(ordered, 1):
        baseline_trace = _trace("BASE-002", True, {"baseline_rank": rank, "sort": ["total_outstanding_cif DESC", "max_dpd_cif DESC", "cif ASC"]})
        ranked.append(replace(item, baseline_rank=rank, triggered_rule_ids=item.triggered_rule_ids + ("BASE-002",), policy_trace=item.policy_trace + (baseline_trace,)))
    return ranked
