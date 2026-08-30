from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .engine import COMPONENT_MAX
from .io import evaluate_directory


def validate(input_directory: Path) -> dict[str, Any]:
    results = evaluate_directory(input_directory)
    by_cif = {row.cif: row for row in results}
    errors: list[str] = []
    component_violations = total_violations = routing_mutations = 0
    for row in results:
        components = {item.name: item.score for item in row.component_breakdown}
        component_violations += sum(not 0 <= score <= COMPONENT_MAX[name] for name, score in components.items())
        total_violations += not (0 <= row.recovery_opportunity_score <= 100 and row.recovery_opportunity_score == sum(components.values()))
        boundary = next(trace for trace in row.score_trace if trace.rule_id == "SCORE-POLICY-BOUNDARY-001")
        routing_mutations += bool(boundary.evidence["routing_mutated"])
    if len(results) != 3000: errors.append(f"record count is {len(results)}, expected 3000")
    if len(by_cif) != len(results): errors.append("duplicate CIF results")
    if component_violations: errors.append(f"component bound violations: {component_violations}")
    if total_violations: errors.append(f"total bound/sum violations: {total_violations}")
    if routing_mutations: errors.append(f"routing mutations: {routing_mutations}")
    golden_assertions: dict[str, list[bool]] = {f"G{i:02d}": [] for i in range(1, 21)}

    def check_golden(scenario_id: str, passed: bool, message: str) -> None:
        golden_assertions[scenario_id].append(passed)
        if not passed:
            errors.append(message)

    g01, g02 = by_cif["GOLDEN_G01"], by_cif["GOLDEN_G02"]
    baseline_order = g01.baseline_rank < g02.baseline_rank
    recovery_order = g02.recovery_rank < g01.recovery_rank
    check_golden("G01", baseline_order, "G01 must rank above G02 in baseline")
    check_golden("G02", baseline_order, "G01 must rank above G02 in baseline")
    check_golden("G01", recovery_order, "G02 must rank above G01 in Recovery Opportunity")
    check_golden("G02", recovery_order, "G02 must rank above G01 in Recovery Opportunity")
    check_golden("G07", by_cif["GOLDEN_G07"].final_route == "CALL", "G07 final route changed")
    check_golden("G08", by_cif["GOLDEN_G08"].final_route == "CBS", "G08 final route changed")
    g19 = by_cif["GOLDEN_G19"]
    check_golden("G19", g19.derived_features["successful_calls_30d"] >= 1 and g19.willingness_to_pay_score == 0, "G19 technical Success affected PTP/willingness")
    g20 = by_cif["GOLDEN_G20"]
    check_golden("G20", g20.total_outstanding_cif == Decimal(400_000_000) and g20.max_dpd_cif == 12, "G20 aggregation changed")
    golden = {
        scenario_id: "NOT_APPLICABLE" if not assertions else ("PASS" if all(assertions) else "FAIL")
        for scenario_id, assertions in golden_assertions.items()
    }
    hero = {sid: by_cif[f"GOLDEN_{sid}"].to_dict() for sid in ("G01", "G02", "G03", "G04", "G05")}
    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors, "cif_count": len(results),
        "minimum_score": min(row.recovery_opportunity_score for row in results),
        "maximum_score": max(row.recovery_opportunity_score for row in results),
        "average_score": str(sum(Decimal(row.recovery_opportunity_score) for row in results) / Decimal(len(results))),
        "component_bound_violations": component_violations, "total_bound_violations": total_violations,
        "routing_mutations": routing_mutations, "duplicate_cifs": len(results) - len(by_cif),
        "golden": golden, "hero_results": hero,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TASK-003 against source data and policy results")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/recovery-opportunity/golden_recovery_validation.json"))
    args = parser.parse_args()
    report = validate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
