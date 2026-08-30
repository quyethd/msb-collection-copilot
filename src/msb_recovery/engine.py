from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

from msb_policy.engine import PolicyResult
from .features import derive_features

COMPONENT_MAX = {"BUSINESS_URGENCY": 20, "ABILITY_TO_PAY": 25, "WILLINGNESS_TO_PAY": 20, "CONTACTABILITY": 15, "TIMING_OPPORTUNITY": 15, "STRATEGIC_ADJUSTMENT": 5}


@dataclass(frozen=True)
class RecoveryConfig:
    reference_date: date = date(2026, 8, 28)
    dpd_bands: tuple[tuple[int | None, int], ...] = ((1, 0), (5, 2), (15, 5), (30, 8), (60, 10), (None, 12))
    outstanding_percentile_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal("0.50"), 0), (Decimal("0.75"), 1), (Decimal("0.90"), 2), (Decimal("0.97"), 3), (None, 4))
    inflow_7d_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal(5_000_000), 1), (Decimal(15_000_000), 3), (Decimal(30_000_000), 6), (None, 8))
    net_cashflow_30d_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal(10_000_000), 2), (Decimal(30_000_000), 4), (None, 5))
    liquidity_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal("0.5"), 1), (Decimal(1), 2), (Decimal(2), 3), (None, 4))
    fulfillment_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal("0.5"), 1), (Decimal(1), 3), (None, 4))
    success_rate_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal("0.20"), 1), (Decimal("0.40"), 2), (Decimal("0.70"), 4), (None, 6))
    inflow_3d_bands: tuple[tuple[Decimal | None, int], ...] = ((Decimal(5_000_000), 1), (Decimal(15_000_000), 2), (Decimal(30_000_000), 4), (None, 5))
    payment_after_contact_days: tuple[int, int] = (3, 7)
    successful_call_recency_days: tuple[int, int] = (7, 30)


@dataclass(frozen=True)
class ScoreTrace:
    rule_id: str
    component: str
    result: str
    points: int
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    score: int
    max_score: int
    evidence: Mapping[str, Any]
    triggered_rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryOpportunityResult:
    cif: str
    baseline_rank: int
    recovery_rank: int | None
    base_route: str
    challenge_override_route: str | None
    final_route: str
    hard_suppressed: bool
    total_outstanding_cif: Decimal
    max_dpd_cif: int
    business_urgency_score: int
    ability_to_pay_score: int
    willingness_to_pay_score: int
    contactability_score: int
    timing_opportunity_score: int
    strategic_adjustment_score: int
    recovery_opportunity_score: int
    component_breakdown: tuple[ScoreComponent, ...]
    derived_features: Mapping[str, Any]
    triggered_rule_ids: tuple[str, ...]
    score_trace: tuple[ScoreTrace, ...]
    data_quality: Mapping[str, str]
    confidence: None = None

    def to_dict(self) -> dict[str, Any]:
        def encode(value: Any) -> Any:
            if isinstance(value, Decimal): return str(value)
            if isinstance(value, (date, datetime)): return value.isoformat()
            if isinstance(value, tuple): return [encode(item) for item in value]
            if isinstance(value, dict): return {key: encode(item) for key, item in value.items()}
            return value
        return encode(asdict(self))


def band(value: Any, bands: Sequence[tuple[Any, int]]) -> int:
    for upper_exclusive, points in bands:
        if upper_exclusive is None or value < upper_exclusive: return points
    raise AssertionError("invalid scoring bands")


def positive_band(value: Decimal, bands: Sequence[tuple[Decimal | None, int]]) -> int:
    if value <= 0: return 0
    return band(value, bands)


def evaluate_one(policy: PolicyResult, features: Mapping[str, Any], outstanding_percentile: Decimal, config: RecoveryConfig) -> RecoveryOpportunityResult:
    traces: list[ScoreTrace] = []
    components: list[ScoreComponent] = []

    def add(component: str, rule: str, points: int, evidence: Mapping[str, Any], available=True) -> None:
        traces.append(ScoreTrace(rule, component, "MATCH" if available else "MISSING", points, dict(evidence)))

    # Business Urgency: 12 + 4 + 4.
    dpd = policy.max_dpd_cif
    dpd_points = band(dpd, config.dpd_bands)
    out_points = band(outstanding_percentile, config.outstanding_percentile_bands)
    if policy.ptp_status == "BROKEN": ptp_urgency = 4
    elif policy.ptp_status == "PARTIAL" and policy.promise_date <= config.reference_date: ptp_urgency = 3
    elif policy.ptp_status == "OPEN" and policy.promise_date <= config.reference_date + timedelta(days=1): ptp_urgency = 2
    elif policy.ptp_status == "OPEN" and policy.promise_date <= config.reference_date + timedelta(days=3): ptp_urgency = 1
    else: ptp_urgency = 0
    add("BUSINESS_URGENCY", "SCORE-URG-DPD-001", dpd_points, {"max_dpd_cif": dpd})
    add("BUSINESS_URGENCY", "SCORE-URG-OUT-001", out_points, {"outstanding_percentile": outstanding_percentile, "total_outstanding_cif": policy.total_outstanding_cif})
    add("BUSINESS_URGENCY", "SCORE-URG-PTP-001", ptp_urgency, {"ptp_status": policy.ptp_status, "promise_date": policy.promise_date}, features["ptp_available"])

    # Ability To Pay: 8 + 5 + 4 + 4 + 4.
    cash = features["cashflow_available"]
    inflow7 = features["inflow_7d"]
    inflow_points = positive_band(inflow7, config.inflow_7d_bands) if cash else 0
    net30 = features["net_cashflow_30d"]
    net_points = positive_band(net30, config.net_cashflow_30d_bands) if cash else 0
    sources = set(features["income_sources_30d"])
    income_points = 4 if sources == {"SALARY", "BUSINESS_INCOME"} else (3 if sources else 0)
    stability_points = {0: 0, 1: 1, 2: 3, 3: 4}[features["positive_cashflow_windows"]] if cash else 0
    liquidity = features["liquidity_to_due_ratio"]
    liquidity_points = 0 if liquidity is None else positive_band(liquidity, config.liquidity_bands)
    add("ABILITY_TO_PAY", "SCORE-ABL-INFLOW7-001", inflow_points, {"inflow_7d": inflow7}, cash)
    add("ABILITY_TO_PAY", "SCORE-ABL-NET30-001", net_points, {"net_cashflow_30d": net30}, cash)
    add("ABILITY_TO_PAY", "SCORE-ABL-INCOME-001", income_points, {"income_sources_30d": sorted(sources)}, cash)
    add("ABILITY_TO_PAY", "SCORE-ABL-STABILITY-001", stability_points, {"net_cashflow_windows_30d": features["net_cashflow_windows_30d"], "positive_windows": features["positive_cashflow_windows"]}, cash)
    add("ABILITY_TO_PAY", "SCORE-ABL-LIQUIDITY-001", liquidity_points, {"liquidity_to_due_ratio": liquidity, "inflow_7d": inflow7, "promise_amount": policy.promise_amount}, liquidity is not None)

    # Willingness: 8 + 4 + 4 + 4.
    state_points = {"KEPT": 8, "PARTIAL": 5, "OPEN": 3, "BROKEN": 0, None: 0}[policy.ptp_status]
    fulfill = (
        policy.actual_paid_amount / policy.promise_amount
        if policy.actual_paid_amount is not None
        and policy.promise_amount is not None
        and policy.promise_amount > 0
        else None
    )
    fulfill_points = 0 if fulfill is None else positive_band(fulfill, config.fulfillment_bands)
    pay_days = features["payment_after_contact_days"]
    pay_points = 4 if pay_days is not None and pay_days <= config.payment_after_contact_days[0] else (2 if pay_days is not None and pay_days <= config.payment_after_contact_days[1] else 0)
    ability_points = {"CERTAIN": 4, "HIGH": 3, "MEDIUM": 1, "LOW": 0, "VERY_LOW": 0, None: 0}[policy.payment_ptp_ability]
    add("WILLINGNESS_TO_PAY", "SCORE-WIL-PTPSTATE-001", state_points, {"ptp_status": policy.ptp_status}, features["ptp_available"])
    add("WILLINGNESS_TO_PAY", "SCORE-WIL-FULFILL-001", fulfill_points, {"ptp_fulfillment_ratio": fulfill}, fulfill is not None)
    add("WILLINGNESS_TO_PAY", "SCORE-WIL-PAYAFTERCONTACT-001", pay_points, {"payment_after_contact_days": pay_days}, features["payment_available"] and features["call_history_available"])
    add("WILLINGNESS_TO_PAY", "SCORE-WIL-HUMANABILITY-001", ability_points, {"payment_ptp_ability": policy.payment_ptp_ability, "human_assessment": True}, policy.payment_ptp_ability is not None)

    # Contactability: 6 + 4 + 3 + 2.
    rate = features["technical_success_rate_30d"]
    rate_points = 0 if rate is None else positive_band(rate, config.success_rate_bands)
    utc_points = 0 if not features["operation_history_available"] else {0: 4, 1: 3, 2: 2, 3: 1}.get(features["utc_count_30d"], 0)
    valid_points = 0 if features["nin_present_30d"] else (3 if features["call_or_operation_evidence_30d"] else 0)
    recency = features["days_since_last_successful_call"]
    recency_points = 2 if recency is not None and recency <= config.successful_call_recency_days[0] else (1 if recency is not None and recency <= config.successful_call_recency_days[1] else 0)
    add("CONTACTABILITY", "SCORE-CON-SUCCESSRATE-001", rate_points, {"outbound_attempts_30d": features["outbound_attempts_30d"], "successful_calls_30d": features["successful_calls_30d"], "success_rate_30d": rate}, rate is not None)
    add("CONTACTABILITY", "SCORE-CON-UTC-001", utc_points, {"utc_count_30d": features["utc_count_30d"]}, features["operation_history_available"])
    add("CONTACTABILITY", "SCORE-CON-VALIDCONTACT-001", valid_points, {"nin_present_30d": features["nin_present_30d"], "call_or_operation_evidence_30d": features["call_or_operation_evidence_30d"]}, features["call_or_operation_evidence_30d"])
    add("CONTACTABILITY", "SCORE-CON-RECENCY-001", recency_points, {"days_since_last_successful_call": recency}, features["call_history_available"])

    # Timing Opportunity: 5 + 5 + 5.
    next_date = policy.source_next_action_date.date() if policy.source_next_action_date else None
    next_delta = (next_date - config.reference_date).days if next_date else None
    next_points = 0 if next_delta is None else (5 if next_delta <= 0 else (4 if next_delta == 1 else (2 if next_delta <= 3 else 0)))
    if policy.ptp_status == "BROKEN": ptp_timing = 5
    elif policy.ptp_status == "PARTIAL" and policy.promise_date <= config.reference_date: ptp_timing = 4
    elif policy.ptp_status == "OPEN" and policy.promise_date <= config.reference_date: ptp_timing = 3
    elif policy.ptp_status == "OPEN" and policy.promise_date == config.reference_date + timedelta(days=1): ptp_timing = 2
    elif policy.ptp_status == "OPEN" and policy.promise_date <= config.reference_date + timedelta(days=3): ptp_timing = 1
    else: ptp_timing = 0
    inflow3 = features["inflow_3d"]
    inflow3_points = positive_band(inflow3, config.inflow_3d_bands) if cash else 0
    add("TIMING_OPPORTUNITY", "SCORE-TIM-NEXTACTION-001", next_points, {"source_next_action_date": policy.source_next_action_date, "days_from_reference": next_delta}, next_date is not None)
    add("TIMING_OPPORTUNITY", "SCORE-TIM-PTP-001", ptp_timing, {"ptp_status": policy.ptp_status, "promise_date": policy.promise_date}, features["ptp_available"])
    add("TIMING_OPPORTUNITY", "SCORE-TIM-INFLOW3-001", inflow3_points, {"inflow_3d": inflow3}, cash)
    add("STRATEGIC_ADJUSTMENT", "SCORE-STR-001", 0, {"configured_nonzero_priority": False})
    add("POLICY_BOUNDARY", "SCORE-POLICY-BOUNDARY-001", 0, {"base_route": policy.base_route, "challenge_override_route": policy.challenge_override_route, "final_route": policy.final_route, "routing_mutated": False})
    add("POLICY_BOUNDARY", "SCORE-OUTCOME-BOUNDARY-001", 0, {"technical_success_used_as_ptp_or_willingness": False})
    add("POLICY_BOUNDARY", "SCORE-SUPPRESSION-001", 0, {"hard_suppressed": policy.hard_suppressed, "analytical_score_calculated": True})

    for component, maximum in COMPONENT_MAX.items():
        component_traces = [trace for trace in traces if trace.component == component]
        score = sum(trace.points for trace in component_traces)
        if not 0 <= score <= maximum: raise ValueError(f"{policy.cif}: {component} score {score} exceeds 0..{maximum}")
        components.append(ScoreComponent(component, score, maximum, {trace.rule_id: trace.evidence for trace in component_traces}, tuple(trace.rule_id for trace in component_traces if trace.result == "MATCH")))
    scores = {component.name: component.score for component in components}
    total = sum(scores.values())
    if not 0 <= total <= 100: raise ValueError(f"{policy.cif}: total score {total} exceeds 0..100")
    umbrellas = ("SCORE-URG-001", "SCORE-ABL-001", "SCORE-WIL-001", "SCORE-CON-001", "SCORE-TIM-001")
    triggered = umbrellas + tuple(trace.rule_id for trace in traces if trace.result == "MATCH")
    quality = {key: "AVAILABLE" if features[key] else "MISSING" for key in ("cashflow_available", "payment_available", "ptp_available", "call_history_available", "operation_history_available")}
    derived_features = dict(features)
    derived_features["ptp_fulfillment_ratio"] = fulfill
    return RecoveryOpportunityResult(policy.cif, policy.baseline_rank or 0, None, policy.base_route, policy.challenge_override_route, policy.final_route, policy.hard_suppressed, policy.total_outstanding_cif, policy.max_dpd_cif, scores["BUSINESS_URGENCY"], scores["ABILITY_TO_PAY"], scores["WILLINGNESS_TO_PAY"], scores["CONTACTABILITY"], scores["TIMING_OPPORTUNITY"], scores["STRATEGIC_ADJUSTMENT"], total, tuple(components), derived_features, triggered, tuple(traces), quality)


def evaluate_recovery(
    policies: Sequence[PolicyResult], cashflows_by_cif: Mapping[str, Sequence[Mapping[str, Any]]],
    payments_by_cif: Mapping[str, Sequence[Mapping[str, Any]]], calls_by_cif: Mapping[str, Sequence[Mapping[str, Any]]],
    operations_by_cif: Mapping[str, Sequence[Mapping[str, Any]]], config: RecoveryConfig,
) -> list[RecoveryOpportunityResult]:
    totals = [policy.total_outstanding_cif for policy in policies]
    count = Decimal(len(totals))
    results = []
    for policy in policies:
        percentile = Decimal(sum(total <= policy.total_outstanding_cif for total in totals)) / count
        features = derive_features(policy, cashflows_by_cif.get(policy.cif, ()), payments_by_cif.get(policy.cif, ()), calls_by_cif.get(policy.cif, ()), operations_by_cif.get(policy.cif, ()), config.reference_date)
        results.append(evaluate_one(policy, features, percentile, config))
    ordered = sorted(results, key=lambda row: (-row.recovery_opportunity_score, -row.ability_to_pay_score, -row.willingness_to_pay_score, -row.timing_opportunity_score, row.cif))
    return [replace(row, recovery_rank=rank, triggered_rule_ids=row.triggered_rule_ids + ("RANK-RECOVERY-001",)) for rank, row in enumerate(ordered, 1)]
