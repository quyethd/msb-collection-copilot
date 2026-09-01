from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from msb_recovery.engine import RecoveryOpportunityResult

SYNTHETIC_STATISTIC_LABEL = "SYNTHETIC PROTOTYPE STATISTIC"
TOP_K_VALUES = (10, 50, 100)
COMPONENT_FIELDS = (
    ("BUSINESS_URGENCY", "business_urgency_score", 20),
    ("ABILITY_TO_PAY", "ability_to_pay_score", 25),
    ("WILLINGNESS_TO_PAY", "willingness_to_pay_score", 20),
    ("CONTACTABILITY", "contactability_score", 15),
    ("TIMING_OPPORTUNITY", "timing_opportunity_score", 15),
    ("STRATEGIC_ADJUSTMENT", "strategic_adjustment_score", 5),
)


def encode(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return encode(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [encode(item) for item in value]
    if isinstance(value, list):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class MovementFactor:
    factor: str
    score: int
    max_score: int
    supporting_rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class CifEvaluation:
    cif: str
    baseline_rank: int
    recovery_rank: int
    rank_delta: int
    absolute_rank_delta: int
    normalized_rank_delta: Decimal
    movement: str
    total_outstanding_cif: Decimal
    max_dpd_cif: int
    base_route: str
    challenge_override_route: str | None
    final_route: str
    hard_suppressed: bool
    recovery_opportunity_score: int
    business_urgency_score: int
    ability_to_pay_score: int
    willingness_to_pay_score: int
    contactability_score: int
    timing_opportunity_score: int
    strategic_adjustment_score: int
    movement_factors: tuple[MovementFactor, ...]
    primary_movement_factors: tuple[MovementFactor, ...]

    def to_dict(self) -> dict[str, Any]:
        return encode(asdict(self))


def classify_movement(rank_delta: int) -> str:
    if rank_delta > 0:
        return "PROMOTED"
    if rank_delta < 0:
        return "DEMOTED"
    return "UNCHANGED"


def normalized_rank_delta(rank_delta: int, portfolio_size: int) -> Decimal:
    return Decimal(rank_delta) / Decimal(max(portfolio_size - 1, 1))


def spearman_rank_correlation(rows: Sequence[CifEvaluation]) -> Decimal:
    count = len(rows)
    if count <= 1:
        return Decimal(1)
    squared_difference = sum(row.rank_delta * row.rank_delta for row in rows)
    return Decimal(1) - Decimal(6 * squared_difference) / Decimal(count * (count * count - 1))


def movement_factors(source: RecoveryOpportunityResult) -> tuple[MovementFactor, ...]:
    components = {item.name: item for item in source.component_breakdown}
    factors = tuple(
        MovementFactor(name, getattr(source, field), maximum, tuple(components[name].triggered_rule_ids))
        for name, field, maximum in COMPONENT_FIELDS
        if getattr(source, field) > 0
    )
    return tuple(sorted(factors, key=lambda item: (-item.score, item.factor)))


def evaluate_cifs(results: Sequence[RecoveryOpportunityResult]) -> list[CifEvaluation]:
    count = len(results)
    evaluations = []
    for source in results:
        if source.recovery_rank is None:
            raise ValueError(f"{source.cif}: recovery rank is missing")
        delta = source.baseline_rank - source.recovery_rank
        factors = movement_factors(source)
        evaluations.append(CifEvaluation(
            source.cif, source.baseline_rank, source.recovery_rank, delta, abs(delta),
            normalized_rank_delta(delta, count), classify_movement(delta),
            source.total_outstanding_cif, source.max_dpd_cif, source.base_route,
            source.challenge_override_route, source.final_route, source.hard_suppressed,
            source.recovery_opportunity_score, source.business_urgency_score,
            source.ability_to_pay_score, source.willingness_to_pay_score,
            source.contactability_score, source.timing_opportunity_score,
            source.strategic_adjustment_score, factors, factors[:3],
        ))
    return evaluations


def route_counts(rows: Sequence[CifEvaluation]) -> dict[str, int]:
    routes = sorted({row.final_route for row in rows})
    return {route: sum(row.final_route == route for row in rows) for route in routes}


def arithmetic_mean(values: Sequence[int]) -> Decimal:
    return Decimal(sum(values)) / Decimal(len(values)) if values else Decimal(0)


def component_means(rows: Sequence[CifEvaluation]) -> dict[str, Decimal]:
    return {field: arithmetic_mean([getattr(row, field) for row in rows]) for _, field, _ in COMPONENT_FIELDS}


def component_statistics(rows: Sequence[CifEvaluation]) -> dict[str, dict[str, int | Decimal]]:
    fields = [field for _, field, _ in COMPONENT_FIELDS] + ["recovery_opportunity_score"]
    return {
        field: {
            "minimum": min(getattr(row, field) for row in rows),
            "maximum": max(getattr(row, field) for row in rows),
            "mean": arithmetic_mean([getattr(row, field) for row in rows]),
            "statistic_label": SYNTHETIC_STATISTIC_LABEL,
        }
        for field in fields
    }


def top_k_summary(rows: Sequence[CifEvaluation], k: int) -> dict[str, Any]:
    baseline = {row.cif for row in rows if row.baseline_rank <= k}
    recovery = {row.cif for row in rows if row.recovery_rank <= k}
    promoted = sorted(recovery - baseline)
    demoted = sorted(baseline - recovery)
    overlap = len(baseline & recovery)
    return {
        "baseline_count": len(baseline), "recovery_count": len(recovery),
        "overlap_count": overlap, "overlap_ratio": Decimal(overlap) / Decimal(k),
        "promoted_into_recovery_top_k_count": len(promoted),
        "demoted_out_of_baseline_top_k_count": len(demoted),
        "promoted_cifs": promoted, "demoted_cifs": demoted,
    }


def hero_record(row: CifEvaluation) -> dict[str, Any]:
    return {
        "cif": row.cif, "baseline_rank": row.baseline_rank, "recovery_rank": row.recovery_rank,
        "rank_delta": row.rank_delta, "movement": row.movement,
        "baseline_evidence": {"total_outstanding_cif": row.total_outstanding_cif, "max_dpd_cif": row.max_dpd_cif},
        "recovery_opportunity_score": row.recovery_opportunity_score,
        "component_scores": {field: getattr(row, field) for _, field, _ in COMPONENT_FIELDS},
        "primary_movement_factors": row.primary_movement_factors, "final_route": row.final_route,
    }


def summarize(rows: Sequence[CifEvaluation]) -> dict[str, Any]:
    by_cif = {row.cif: row for row in rows}
    top_k = {str(k): top_k_summary(rows, k) for k in TOP_K_VALUES}
    route_composition: dict[str, Any] = {"full_portfolio": route_counts(rows)}
    profiles: dict[str, Any] = {}
    for k in TOP_K_VALUES:
        baseline = [row for row in rows if row.baseline_rank <= k]
        recovery = [row for row in rows if row.recovery_rank <= k]
        route_composition[f"baseline_top_{k}"] = route_counts(baseline)
        route_composition[f"recovery_top_{k}"] = route_counts(recovery)
        profiles[str(k)] = {
            "baseline_top_k": component_means(baseline),
            "recovery_top_k": component_means(recovery),
            "statistic_label": SYNTHETIC_STATISTIC_LABEL,
        }
    g01, g02 = by_cif["GOLDEN_G01"], by_cif["GOLDEN_G02"]
    return encode({
        "portfolio_size": len(rows), "spearman_rank_correlation": spearman_rank_correlation(rows),
        "movement_counts": {name.lower(): sum(row.movement == name for row in rows) for name in ("PROMOTED", "DEMOTED", "UNCHANGED")},
        "rank_delta": {
            "minimum": min(row.rank_delta for row in rows), "maximum": max(row.rank_delta for row in rows),
            "mean_absolute": arithmetic_mean([row.absolute_rank_delta for row in rows]),
            "statistic_label": SYNTHETIC_STATISTIC_LABEL,
        },
        "top_k": top_k, "route_composition": route_composition,
        "component_statistics": component_statistics(rows), "top_k_component_profiles": profiles,
        "hero_comparison": {
            "G01": hero_record(g01), "G02": hero_record(g02),
            "baseline": {"G01_rank": g01.baseline_rank, "G02_rank": g02.baseline_rank, "winner": g01.cif if g01.baseline_rank < g02.baseline_rank else g02.cif},
            "recovery_opportunity": {"G01_rank": g01.recovery_rank, "G02_rank": g02.recovery_rank, "winner": g01.cif if g01.recovery_rank < g02.recovery_rank else g02.cif},
            "statement": "Recovery Opportunity changes prioritization.",
        },
        "synthetic_statistic_label": SYNTHETIC_STATISTIC_LABEL,
    })
