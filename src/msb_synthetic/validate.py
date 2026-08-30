from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

TABLES = ("customer", "loan_account", "collection_assignment", "cashflow_transaction", "payment_event", "operation_result", "call_history", "golden_scenario_expected")


def load(directory: Path) -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = {}
    for name in TABLES:
        with (directory / f"{name}.csv").open(encoding="utf-8") as handle:
            rows[name] = list(csv.DictReader(handle))
    return rows


def validate(directory: Path, expected_population: int = 3000) -> dict[str, Any]:
    rows = load(directory)
    manifest = json.loads((directory / "generation_manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    checks: list[str] = []

    def check(condition: bool, message: str) -> None:
        (checks if condition else errors).append(message)

    customers = {r["cif"] for r in rows["customer"]}
    check(len(customers) == expected_population, f"customer count = {expected_population}")
    golden = {r["scenario_id"]: r for r in rows["golden_scenario_expected"]}
    check(set(golden) == {f"G{i:02d}" for i in range(1, 21)}, "golden scenarios G01-G20 present exactly")
    check(all(golden[f"G0{i}"]["hero"] == "true" for i in range(1, 6)) and sum(r["hero"] == "true" for r in golden.values()) == 5, "G01-G05 are the only HERO scenarios")
    check(all(r["cif"] in customers for r in rows["loan_account"]), "loan_account CIF foreign keys")
    check(all(r["cif"] in customers for r in rows["cashflow_transaction"]), "cashflow_transaction CIF foreign keys")
    check(all(r["cif"] in customers for r in rows["payment_event"]), "payment_event CIF foreign keys")
    check(all(r["cif"] in customers for r in rows["call_history"]), "call_history CIF foreign keys")
    check(all(r["cif"] in customers for r in rows["operation_result"]), "operation_result CIF foreign keys")

    accounts = {r["account_id"]: r for r in rows["loan_account"]}
    operations = {r["id"]: r for r in rows["operation_result"]}
    check(all(r["account_id"] in accounts and accounts[r["account_id"]]["cif"] == r["cif"] for r in rows["payment_event"]), "payment account foreign keys and ownership")
    check(all(not r["linked_ptp_id"] or r["linked_ptp_id"] in operations for r in rows["payment_event"]), "payment linked PTP foreign keys")
    check(len(rows["collection_assignment"]) == len(customers) and all(r["cif"] in customers for r in rows["collection_assignment"]), "one valid assignment per CIF")

    loans_by_cif: dict[str, list[dict[str, str]]] = defaultdict(list)
    ops_by_cif: dict[str, list[dict[str, str]]] = defaultdict(list)
    calls_by_cif: dict[str, list[dict[str, str]]] = defaultdict(list)
    pays_by_op: dict[str, Decimal] = defaultdict(Decimal)
    cash_by_cif: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows["loan_account"]: loans_by_cif[r["cif"]].append(r)
    for r in rows["operation_result"]: ops_by_cif[r["cif"]].append(r)
    for r in rows["call_history"]: calls_by_cif[r["cif"]].append(r)
    for r in rows["cashflow_transaction"]: cash_by_cif[r["cif"]].append(r)
    for r in rows["payment_event"]:
        if r["linked_ptp_id"]: pays_by_op[r["linked_ptp_id"]] += Decimal(r["amount"])

    g20 = loans_by_cif["GOLDEN_G20"]
    check(sum(Decimal(r["outstanding_amount"]) for r in g20) == Decimal(400_000_000) and max(int(r["dpd"]) for r in g20) == 12, "G20 aggregation is 400,000,000 VND and MAX DPD 12")

    def ptp_status(cif: str, grace_days=1) -> tuple[str, Decimal, Decimal]:
        pts = [r for r in ops_by_cif[cif] if r["operation_result"] == "PTP"]
        op = max(pts, key=lambda r: r["created_at"])
        promised, paid = Decimal(op["payment_ptp_number"]), pays_by_op[op["id"]]
        promise_date = date.fromisoformat(op["payment_ptp_date"])
        ref = date.fromisoformat(manifest["reference_date"])
        if paid >= promised: status = "KEPT"
        elif paid > 0: status = "PARTIAL"
        elif ref > promise_date + timedelta(days=grace_days): status = "BROKEN"
        else: status = "OPEN"
        return status, promised, paid

    check(ptp_status("GOLDEN_G09")[0] == "KEPT", "G09 supports PTP KEPT")
    s, promised, paid = ptp_status("GOLDEN_G10")
    check(s == "PARTIAL" and promised == Decimal(20_000_000) and paid == Decimal(10_000_000), "G10 is 20M promise / 10M paid / PARTIAL")
    check(ptp_status("GOLDEN_G11")[0] == "BROKEN", "G11 supports BROKEN PTP with configured one-day grace")
    check(ptp_status("GOLDEN_G12")[0] == "OPEN", "G12 supports OPEN PTP")
    check(any(r["operation_result"] == "NIN" for r in ops_by_cif["GOLDEN_G13"]), "G13 contains NIN evidence")
    check(any(r["operation_result"] == "NA" and r["next_action_date"] for r in ops_by_cif["GOLDEN_G14"]), "G14 contains NA and next_action_date")
    check(sum(r["operation_result"] == "UTC" for r in ops_by_cif["GOLDEN_G15"]) >= 5, "G15 contains repeated UTC evidence")
    g19_ops = ops_by_cif["GOLDEN_G19"]
    check(any(r["status"] == "Success" for r in calls_by_cif["GOLDEN_G19"]) and not any(r["operation_result"] == "PTP" for r in g19_ops), "G19 technical Success does not contain PTP business outcome")

    money_ok = all(Decimal(r["outstanding_amount"]) >= 0 and Decimal(r["overdue_amount"]) >= 0 and Decimal(r["overdue_amount"]) <= Decimal(r["outstanding_amount"]) and Decimal(r["due_amount"]) >= 0 for r in rows["loan_account"])
    money_ok &= all(Decimal(r["amount"]) > 0 for table in ("cashflow_transaction", "payment_event") for r in rows[table])
    check(money_ok, "all monetary values are valid")
    check(manifest["is_synthetic"] is True and manifest["golden_scenario_count"] == 20 and manifest["hero_scenario_count"] == 5, "manifest synthetic and scenario metadata")

    # Input evidence for every locked golden scenario, without executing future policy rules.
    scenario_checks = {
        "G01": len([r for r in ops_by_cif["GOLDEN_G01"] if r["operation_result"] == "PTP"]) == 3 and len(calls_by_cif["GOLDEN_G01"]) >= 5,
        "G02": sum(Decimal(r["amount"]) for r in cash_by_cif["GOLDEN_G02"] if r["direction"] == "IN") >= 40_000_000,
        "G03": len([r for r in rows["payment_event"] if r["cif"] == "GOLDEN_G03" and r["payment_type"] == "SELF_CURE"]) >= 3,
        "G04": ptp_status("GOLDEN_G04")[0] == "BROKEN",
        "G05": json.loads(golden["G05"]["input_fixture"])["simulation_override"]["source_must_remain_unchanged"] is True,
        "G06": golden["G06"]["expected_route"] == "CBS",
        "G07": json.loads(golden["G07"]["input_fixture"])["challenge_override_route"] == "CALL",
        "G08": json.loads(golden["G08"]["input_fixture"])["challenge_override_route"] == "CBS",
        "G09": ptp_status("GOLDEN_G09")[0] == "KEPT", "G10": ptp_status("GOLDEN_G10")[0] == "PARTIAL",
        "G11": ptp_status("GOLDEN_G11")[0] == "BROKEN", "G12": ptp_status("GOLDEN_G12")[0] == "OPEN",
        "G13": any(r["operation_result"] == "NIN" for r in ops_by_cif["GOLDEN_G13"]),
        "G14": any(r["operation_result"] == "NA" and r["next_action_date"] for r in ops_by_cif["GOLDEN_G14"]),
        "G15": sum(r["operation_result"] == "UTC" for r in ops_by_cif["GOLDEN_G15"]) == 5,
        "G16": any(r["operation_result"] == "RTP" for r in ops_by_cif["GOLDEN_G16"]) and bool(cash_by_cif["GOLDEN_G16"]),
        "G17": max(int(r["dpd"]) for r in loans_by_cif["GOLDEN_G17"]) == 35 and bool(cash_by_cif["GOLDEN_G17"]),
        "G18": len([r for r in rows["payment_event"] if r["cif"] == "GOLDEN_G18" and r["payment_type"] == "SELF_CURE"]) == 3,
        "G19": any(r["status"] == "Success" for r in calls_by_cif["GOLDEN_G19"]) and not g19_ops,
        "G20": sum(Decimal(r["outstanding_amount"]) for r in g20) == 400_000_000,
    }
    for sid in sorted(scenario_checks): check(scenario_checks[sid], f"{sid} input fixture validation")
    return {"status": "PASS" if not errors else "FAIL", "checks_passed": len(checks), "errors": errors, "golden": {sid: "PASS" if ok else "FAIL" for sid, ok in scenario_checks.items()}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TASK-001 generated data")
    parser.add_argument("directory", type=Path, nargs="?", default=Path("build/synthetic-data"))
    parser.add_argument("--expected-population", type=int, default=3000)
    args = parser.parse_args()
    report = validate(args.directory, args.expected_population)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
