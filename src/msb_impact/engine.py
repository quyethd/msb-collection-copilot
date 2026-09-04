from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from msb_nba.engine import decide

DEFAULT_ASSUMPTIONS: dict[str, float | int] = {
    "working_days_per_year": 250,
    "daily_customers_reviewed": 100,
    "manual_review_minutes_per_customer": 3,
    "copilot_review_minutes_per_customer": 0.5,
    "average_call_minutes": 3,
    "staff_cost_per_hour_vnd": 100000,
}
ASSUMPTION_KEYS = tuple(DEFAULT_ASSUMPTIONS)
CONTACT_CHANNELS = {"CALL", "SMS", "ZALO", "EMAIL", "FIELD"}


def validate_assumptions(values: Mapping[str, Any] | None) -> dict[str, float | int]:
    if values is None:
        values = {}
    if not isinstance(values, Mapping):
        raise ValueError("assumptions must be an object")
    unknown = set(values) - set(ASSUMPTION_KEYS)
    if unknown:
        raise ValueError(f"unknown assumption(s): {sorted(unknown)}")
    result = dict(DEFAULT_ASSUMPTIONS)
    result.update(values)
    for key, value in result.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a non-negative number")
        if value < 0:
            raise ValueError(f"{key} must be non-negative")
    if result["working_days_per_year"] <= 0 or result["working_days_per_year"] > 366:
        raise ValueError("working_days_per_year must be greater than 0 and at most 366")
    return result


def _ratio(numerator: int, denominator: int) -> float:
    return float(Decimal(numerator) / Decimal(denominator)) if denominator else 0.0


def _provenance(measured: dict[str, Any], assumptions: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in measured:
        result[name] = {"type": "MEASURED_FROM_DEMO_DATA", "source": "accepted deterministic demo outputs"}
    for name in assumptions:
        result[name] = {"type": "CONFIGURABLE_ASSUMPTION", "source": "user input; illustrative default"}
    for name, formula in derived.items():
        result[name] = {"type": "DERIVED_ESTIMATE", "formula": formula}
    return result


def build_impact_report(repository: Any, assumptions: Mapping[str, Any] | None = None) -> dict[str, Any]:
    assumptions = validate_assumptions(assumptions)
    contexts = [repository.context(cif) for cif in sorted(repository.cifs)]
    decisions = [decide(context, repository.calls_for_cif(context["cif"])) for context in contexts]
    total = len(contexts)
    valid = [item for item in decisions if item.recommendation.treatment and item.recommendation.channel]
    call_route = [item for item in decisions if item.policy["final_route"] == "CALL"]
    no_call_now = [item for item in call_route if item.recommendation.channel == "NONE" or item.recommendation.treatment in {"WAIT", "WAIT_SELF_CURE"}]
    active = [item for item in decisions if item.recommendation.channel in CONTACT_CHANNELS]
    ranking_rows = [{"cif": context["cif"], **context["ranking"]} for context in contexts]
    movement = {"PROMOTED": 0, "DEMOTED": 0, "UNCHANGED": 0}
    for row in ranking_rows:
        movement[row["movement"]] += 1
    ranking = {
        "spearman": float(repository.evaluation_summary["spearman_rank_correlation"]) if hasattr(repository, "evaluation_summary") else None,
        "top10_overlap": _top_overlap(ranking_rows, 10),
        "top50_overlap": _top_overlap(ranking_rows, 50),
        "top100_overlap": _top_overlap(ranking_rows, 100),
        "promoted": movement["PROMOTED"], "demoted": movement["DEMOTED"],
    }
    # ToolRepository exposes accepted ranking rows, while the summary is loaded lazily
    # here to keep this engine independent from artifact paths.
    if ranking["spearman"] is None:
        ranking["spearman"] = _spearman(ranking_rows)
    measured = {
        "total_customers": total,
        "decisions_available": len(valid),
        "decision_coverage_rate": _ratio(len(valid), total),
        "auto_triaged_customers": len(valid),
        "call_route_customers": len(call_route),
        "call_route_but_no_call_now": len(no_call_now),
        "potential_call_avoidance_rate": _ratio(len(no_call_now), len(call_route)),
        "active_contact_recommendations": len(active),
        "ranking": ranking,
    }
    a = assumptions
    baseline_hours = a["daily_customers_reviewed"] * a["manual_review_minutes_per_customer"] * a["working_days_per_year"] / 60
    copilot_hours = a["daily_customers_reviewed"] * a["copilot_review_minutes_per_customer"] * a["working_days_per_year"] / 60
    review_saved = baseline_hours - copilot_hours
    calls_per_day = a["daily_customers_reviewed"] * measured["potential_call_avoidance_rate"]
    call_hours = calls_per_day * a["average_call_minutes"] * a["working_days_per_year"] / 60
    total_hours = review_saved + call_hours
    cost_saved = total_hours * a["staff_cost_per_hour_vnd"]
    derived = {
        "manual_hours_baseline": baseline_hours,
        "manual_hours_copilot": copilot_hours,
        "review_hours_saved": review_saved,
        "estimated_calls_avoided_per_day": calls_per_day,
        "call_hours_saved": call_hours,
        "total_hours_saved": total_hours,
        "estimated_operational_cost_saved_vnd": cost_saved,
        "aev_estimate_vnd": cost_saved,
    }
    formulas = {
        "manual_hours_baseline": "daily_customers_reviewed * manual_review_minutes_per_customer * working_days_per_year / 60",
        "manual_hours_copilot": "daily_customers_reviewed * copilot_review_minutes_per_customer * working_days_per_year / 60",
        "review_hours_saved": "manual_hours_baseline - manual_hours_copilot",
        "estimated_calls_avoided_per_day": "daily_customers_reviewed * potential_call_avoidance_rate",
        "call_hours_saved": "estimated_calls_avoided_per_day * average_call_minutes * working_days_per_year / 60",
        "total_hours_saved": "review_hours_saved + call_hours_saved",
        "estimated_operational_cost_saved_vnd": "total_hours_saved * staff_cost_per_hour_vnd",
        "aev_estimate_vnd": "estimated_operational_cost_saved_vnd; no recovery uplift included",
    }
    return {"status": "success", "measured": measured, "assumptions": a, "derived": derived,
            "formulas": formulas, "provenance": _provenance(measured, a, formulas),
            "disclaimer": "Bản demo sử dụng dữ liệu mô phỏng. Các giá trị kinh tế là ước tính theo giả định đầu vào.",
            "recovery_uplift": None}


def _top_overlap(rows: list[Mapping[str, Any]], k: int) -> int:
    baseline = {r["cif"] for r in rows if r.get("baseline_rank", 0) <= k}
    recovery = {r["cif"] for r in rows if r.get("recovery_rank", 0) <= k}
    return len(baseline & recovery)


def _spearman(rows: list[Mapping[str, Any]]) -> float:
    n = len(rows)
    if n <= 1:
        return 1.0
    d2 = sum((int(row["baseline_rank"]) - int(row["recovery_rank"])) ** 2 for row in rows)
    return float(Decimal(1) - Decimal(6 * d2) / Decimal(n * (n * n - 1)))
