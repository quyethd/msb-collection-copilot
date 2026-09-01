from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from msb_policy.io import evaluate_directory as evaluate_policy_directory
from msb_recovery.io import evaluate_directory as evaluate_recovery_directory
from .engine import COMPONENT_FIELDS, SYNTHETIC_STATISTIC_LABEL, TOP_K_VALUES
from .io import evaluate_directory


def validate(input_directory: Path) -> dict[str, Any]:
    policies = {row.cif: row for row in evaluate_policy_directory(input_directory)}
    recoveries = {row.cif: row for row in evaluate_recovery_directory(input_directory)}
    rows, summary = evaluate_directory(input_directory)
    by_cif = {row.cif: row for row in rows}
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    count = len(rows)
    require(count == 3000, f"record count is {count}, expected 3000")
    require(len(by_cif) == count, "duplicate CIF evaluations")
    require({row.baseline_rank for row in rows} == set(range(1, count + 1)), "baseline ranks are not complete and unique")
    require({row.recovery_rank for row in rows} == set(range(1, count + 1)), "Recovery ranks are not complete and unique")

    baseline_order = sorted(recoveries.values(), key=lambda row: (-row.total_outstanding_cif, -row.max_dpd_cif, row.cif))
    recovery_order = sorted(recoveries.values(), key=lambda row: (-row.recovery_opportunity_score, -row.ability_to_pay_score, -row.willingness_to_pay_score, -row.timing_opportunity_score, row.cif))
    baseline_rank_mismatches = sum(row.baseline_rank != rank for rank, row in enumerate(baseline_order, 1))
    recovery_rank_mismatches = sum(row.recovery_rank != rank for rank, row in enumerate(recovery_order, 1))
    require(baseline_rank_mismatches == 0, f"baseline rank mismatches: {baseline_rank_mismatches}")
    require(recovery_rank_mismatches == 0, f"Recovery rank mismatches: {recovery_rank_mismatches}")

    formula_violations = sum(
        row.rank_delta != row.baseline_rank - row.recovery_rank
        or row.absolute_rank_delta != abs(row.rank_delta)
        or row.normalized_rank_delta != Decimal(row.rank_delta) / Decimal(max(count - 1, 1))
        or row.movement != ("PROMOTED" if row.rank_delta > 0 else "DEMOTED" if row.rank_delta < 0 else "UNCHANGED")
        for row in rows
    )
    require(formula_violations == 0, f"movement formula violations: {formula_violations}")

    top_k_violations = 0
    for k in TOP_K_VALUES:
        baseline = {row.cif for row in rows if row.baseline_rank <= k}
        recovery = {row.cif for row in rows if row.recovery_rank <= k}
        actual = summary["top_k"][str(k)]
        overlap = len(baseline & recovery)
        promoted, demoted = sorted(recovery - baseline), sorted(baseline - recovery)
        top_k_violations += not (
            actual["baseline_count"] == len(baseline) == k
            and actual["recovery_count"] == len(recovery) == k
            and actual["overlap_count"] == overlap
            and Decimal(actual["overlap_ratio"]) == Decimal(overlap) / Decimal(k)
            and actual["promoted_cifs"] == promoted and actual["demoted_cifs"] == demoted
            and actual["promoted_into_recovery_top_k_count"] == len(promoted)
            and actual["demoted_out_of_baseline_top_k_count"] == len(demoted)
            and len(promoted) == len(demoted)
        )
    require(top_k_violations == 0, f"Top-K validation failures: {top_k_violations}")

    squared_rank_differences = sum((row.baseline_rank - row.recovery_rank) ** 2 for row in rows)
    expected_rho = (
        Decimal(1)
        if count <= 1
        else Decimal(1) - Decimal(6 * squared_rank_differences) / Decimal(count * (count * count - 1))
    )
    require(Decimal(summary["spearman_rank_correlation"]) == expected_rho, "Spearman correlation mismatch")

    task2_fields = ("base_route", "challenge_override_route", "final_route", "hard_suppressed", "total_outstanding_cif", "max_dpd_cif")
    task3_fields = ("baseline_rank", "recovery_rank", "recovery_opportunity_score") + tuple(field for _, field, _ in COMPONENT_FIELDS)
    task2_mismatches = sum(getattr(by_cif[cif], field) != getattr(policy, field) for cif, policy in policies.items() for field in task2_fields)
    task3_mismatches = sum(getattr(by_cif[cif], field) != getattr(recovery, field) for cif, recovery in recoveries.items() for field in task3_fields)
    require(task2_mismatches == 0, f"TASK-002 authoritative mismatches: {task2_mismatches}")
    require(task3_mismatches == 0, f"TASK-003 authoritative mismatches: {task3_mismatches}")

    golden_assertions: dict[str, list[bool]] = {f"G{i:02d}": [] for i in range(1, 21)}
    def golden(sid: str, condition: bool, message: str) -> None:
        golden_assertions[sid].append(condition)
        require(condition, message)

    g01, g02 = by_cif["GOLDEN_G01"], by_cif["GOLDEN_G02"]
    golden("G01", g01.baseline_rank < g02.baseline_rank and g01.movement == "DEMOTED", "G01 HERO assertion failed")
    golden("G02", g02.recovery_rank < g01.recovery_rank and g02.movement == "PROMOTED", "G02 HERO assertion failed")
    golden("G07", by_cif["GOLDEN_G07"].final_route == policies["GOLDEN_G07"].final_route == "CALL", "G07 route changed")
    golden("G08", by_cif["GOLDEN_G08"].final_route == policies["GOLDEN_G08"].final_route == "CBS", "G08 route changed")
    g19_policy = policies["GOLDEN_G19"]
    golden("G19", g19_policy.technical_call_status_counts.get("Success", 0) >= 1 and g19_policy.ptp_status is None and recoveries["GOLDEN_G19"].willingness_to_pay_score == 0, "G19 outcome boundary changed")
    g20_policy = policies["GOLDEN_G20"]
    golden("G20", g20_policy.total_outstanding_cif == Decimal(400_000_000) and g20_policy.max_dpd_cif == 12, "G20 aggregation changed")
    golden_statuses = {sid: "NOT_APPLICABLE" if not checks else "PASS" if all(checks) else "FAIL" for sid, checks in golden_assertions.items()}

    forbidden_keys = {"precision", "recall", "auc", "roi", "aev", "expected_recovery", "recovery_probability", "evaluation_score", "quality_score", "business_value_score", "ranking_quality_score", "confidence_score"}
    def keys(value: Any) -> set[str]:
        if isinstance(value, dict):
            return {str(key).lower() for key in value} | set().union(*(keys(item) for item in value.values()), set())
        if isinstance(value, list):
            return set().union(*(keys(item) for item in value), set())
        return set()
    forbidden_output_keys = sorted(keys(summary) & forbidden_keys)
    require(not forbidden_output_keys, f"forbidden output metrics: {forbidden_output_keys}")
    require(summary.get("synthetic_statistic_label") == SYNTHETIC_STATISTIC_LABEL, "synthetic statistic label missing")

    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors, "cif_count": count,
        "baseline_rank_mismatches": baseline_rank_mismatches, "recovery_rank_mismatches": recovery_rank_mismatches,
        "movement_formula_violations": formula_violations, "top_k_violations": top_k_violations,
        "spearman_rank_correlation": str(expected_rho), "task2_authoritative_mismatches": task2_mismatches,
        "task3_authoritative_mismatches": task3_mismatches, "forbidden_output_keys": forbidden_output_keys,
        "synthetic_statistic_label": summary.get("synthetic_statistic_label"), "golden": golden_statuses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate baseline-versus-Recovery evaluation")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/evaluation/golden_evaluation_validation.json"))
    args = parser.parse_args()
    report = validate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
