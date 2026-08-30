from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .engine import PolicyConfig
from .io import evaluate_directory

PTP_EXPECTED = {"G01": "BROKEN", "G02": "OPEN", "G04": "BROKEN", "G09": "KEPT", "G10": "PARTIAL", "G11": "BROKEN", "G12": "OPEN"}


def validate(input_directory: Path, config: PolicyConfig = PolicyConfig()) -> dict[str, Any]:
    results = evaluate_directory(input_directory, config)
    by_cif = {result.cif: result for result in results}
    with (input_directory / "golden_scenario_expected.csv").open(encoding="utf-8") as handle:
        fixtures = list(csv.DictReader(handle))
    errors: list[str] = []
    golden: dict[str, dict[str, Any]] = {}

    def require(condition: bool, message: str) -> None:
        if not condition: errors.append(message)

    require(len(results) == 3000, "expected 3,000 policy results")
    require(len(by_cif) == len(results), "policy results must have unique CIFs")
    for fixture in sorted(fixtures, key=lambda row: row["scenario_id"]):
        sid, cif = fixture["scenario_id"], fixture["cif"]
        result = by_cif.get(cif)
        if result is None:
            errors.append(f"{sid}: missing policy result")
            continue
        passed = result.final_route == fixture["expected_route"]
        if sid in PTP_EXPECTED: passed &= result.ptp_status == PTP_EXPECTED[sid]
        if sid == "G13": passed &= result.latest_business_outcome == "NIN"
        if sid == "G14": passed &= result.latest_business_outcome == "NA" and result.source_next_action_date is not None and result.source_next_operation_channel == "CALL"
        if sid == "G15": passed &= result.business_outcome_counts["UTC"] >= 5
        if sid == "G19": passed &= result.technical_call_status_counts.get("Success", 0) >= 1 and result.ptp_status is None and result.latest_business_outcome != "PTP"
        if sid == "G20": passed &= result.total_outstanding_cif == 400_000_000 and result.max_dpd_cif == 12
        if not passed: errors.append(f"{sid}: applicable policy expectations failed")
        golden[sid] = {"status": "PASS" if passed else "FAIL", "base_route": result.base_route, "challenge_override_route": result.challenge_override_route, "final_route": result.final_route, "ptp_status": result.ptp_status, "hard_suppressed": result.hard_suppressed, "triggered_rule_ids": list(result.triggered_rule_ids)}

    require(golden.get("G07", {}).get("base_route") == "CBS" and golden.get("G07", {}).get("final_route") == "CALL", "G07 must preserve CBS to CALL")
    require(golden.get("G08", {}).get("base_route") == "CALL" and golden.get("G08", {}).get("final_route") == "CBS", "G08 must preserve CALL to CBS")
    require(all(not result.hard_suppressed for result in results), "no hard suppression exists in locked rules")
    route_violations = sum(not any(t.rule_id == {"CALL": "ROUTE-001", "CBS": "ROUTE-002", "OTHER": "ROUTE-005"}[result.base_route] and t.result == "MATCH" for t in result.policy_trace) for result in results)
    require(route_violations == 0, f"hard routing violations: {route_violations}")
    return {"status": "PASS" if not errors else "FAIL", "record_count": len(results), "hard_policy_violations": route_violations, "errors": errors, "golden": golden}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TASK-002 policy results against actual synthetic inputs")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/policy-results/golden_policy_validation.json"))
    parser.add_argument("--ptp-grace-days", type=int, default=1)
    args = parser.parse_args()
    report = validate(args.input, PolicyConfig(args.ptp_grace_days))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
