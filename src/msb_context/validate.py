from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from msb_evaluation.io import evaluate_directory as evaluate_evaluation_directory
from msb_policy.io import evaluate_directory as evaluate_policy_directory, read_csv
from msb_recovery.io import evaluate_directory as evaluate_recovery_directory

from .assembler import assemble_directory
from .io import load_contexts
from .models import DEFAULT_PREVIEW_LIMIT, SYNTHETIC_LABEL, DecisionContext

FORBIDDEN_OUTPUT_KEYS = {
    "treatment", "recommended_treatment", "next_best_action", "recommended_channel",
    "recommended_when", "best_contact_time", "action_priority", "recovery_probability",
    "payment_probability", "cure_probability", "expected_recovery", "expected_payment",
    "confidence_score", "ai_explanation", "agent_reasoning", "aev", "roi",
}

REQUIRED_SECTIONS: dict[str, set[str]] = {
    "customer": {"cif"},
    "debt": {"total_outstanding_cif", "max_dpd_cif", "loan_count", "loans"},
    "policy": {"base_route", "challenge_override_route", "final_route", "hard_suppressed"},
    "cashflow": {"inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d", "net_cashflow_30d", "income_sources_30d", "net_cashflow_windows_30d", "positive_cashflow_windows", "liquidity_to_due_ratio", "recent_transactions"},
    "payment": {"payment_available", "recent_payment_count", "recent_payments"},
    "ptp": {"promise_date", "promise_amount", "actual_paid_amount", "status", "employee_assessed_ability", "policy_fulfillment_ratio", "scoring_fulfillment_ratio_raw"},
    "contact": {"call_history_available", "operation_history_available", "outbound_attempts_30d", "successful_outbound_calls_30d", "technical_success_rate_30d", "utc_count_30d", "recent_calls", "recent_operation_results"},
    "recovery_opportunity": {"recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score", "willingness_to_pay_score", "contactability_score", "timing_opportunity_score", "strategic_adjustment_score", "score_trace"},
    "ranking": {"baseline_rank", "recovery_rank", "rank_delta", "absolute_rank_delta", "normalized_rank_delta", "movement", "primary_movement_factors"},
    "evidence": {"baseline", "recovery", "ptp", "contact", "cashflow"},
    "availability": {"cashflow_available", "payment_available", "ptp_available", "call_history_available", "operation_history_available"},
    "provenance": {"synthetic_data", "synthetic_label", "reference_date", "source_stage", "policy_stage", "recovery_stage", "evaluation_stage", "context_stage"},
}
REQUIRED_TOP_LEVEL = {"context_version", "cif", "as_of_date", *REQUIRED_SECTIONS}
MISSING_CASHFLOW_DERIVED_FIELDS = (
    "inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d",
    "net_cashflow_30d", "income_sources_30d", "net_cashflow_windows_30d",
    "positive_cashflow_windows", "liquidity_to_due_ratio",
)


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(*(_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value), set())
    return set()


def validate(input_directory: Path, contexts: Iterable[DecisionContext] | None = None, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> dict[str, Any]:
    context_rows = list(contexts) if contexts is not None else assemble_directory(input_directory, preview_limit)
    by_cif = {row.cif: row for row in context_rows}
    customers = read_csv(input_directory, "customer")
    customer_cifs = {row["cif"] for row in customers}
    policies = {row.cif: row for row in evaluate_policy_directory(input_directory)}
    recoveries = {row.cif: row for row in evaluate_recovery_directory(input_directory)}
    evaluations, _ = evaluate_evaluation_directory(input_directory)
    evaluation_map = {row.cif: row for row in evaluations}
    loans: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(input_directory, "loan_account"):
        loans.setdefault(row["cif"], []).append(row)
    errors: list[str] = []
    def require(condition: bool, message: str) -> None:
        if not condition: errors.append(message)

    duplicate = len(context_rows) - len(by_cif)
    missing, unexpected = customer_cifs - set(by_cif), set(by_cif) - customer_cifs
    require(len(context_rows) == 3000, f"context count {len(context_rows)} != 3000")
    require(not duplicate, f"duplicate context CIF: {duplicate}")
    require(not missing, f"missing context CIF: {len(missing)}")
    require(not unexpected, f"unexpected context CIF: {len(unexpected)}")
    task2_fields = ("base_route", "challenge_override_route", "final_route", "hard_suppressed")
    task3_fields = ("recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score", "willingness_to_pay_score", "contactability_score", "timing_opportunity_score", "strategic_adjustment_score")
    task4_fields = ("baseline_rank", "recovery_rank", "rank_delta", "absolute_rank_delta", "normalized_rank_delta", "movement")
    task2_mismatches = task3_mismatches = task4_mismatches = debt_mismatches = ordering_violations = preview_violations = 0
    forbidden: set[str] = set()
    for cif, context in by_cif.items():
        policy, recovery, evaluation = policies[cif], recoveries[cif], evaluation_map[cif]
        task2_mismatches += sum(context.policy[field] != getattr(policy, field) for field in task2_fields)
        task2_mismatches += context.debt["total_outstanding_cif"] != policy.total_outstanding_cif
        task2_mismatches += context.debt["max_dpd_cif"] != policy.max_dpd_cif
        task3_mismatches += sum(context.recovery_opportunity[field] != getattr(recovery, field) for field in task3_fields)
        task3_mismatches += context.ranking["baseline_rank"] != recovery.baseline_rank
        task3_mismatches += context.ranking["recovery_rank"] != recovery.recovery_rank
        task4_mismatches += sum(context.ranking[field] != getattr(evaluation, field) for field in task4_fields)
        source_loans = loans[cif]
        debt_mismatches += context.debt["total_outstanding_cif"] != sum(int(row["outstanding_amount"]) for row in source_loans)
        debt_mismatches += context.debt["max_dpd_cif"] != max(int(row["dpd"]) for row in source_loans)
        previews = ((context.cashflow["recent_transactions"], "transaction_date", "transaction_id"),
                    (context.payment["recent_payments"], "payment_date", "payment_id"),
                    (context.contact["recent_calls"], "call_time", "id"),
                    (context.contact["recent_operation_results"], "created_at", "id"))
        for rows, timestamp, stable_id in previews:
            preview_violations += len(rows) > preview_limit
            expected = sorted(sorted(rows, key=lambda row: row[stable_id]), key=lambda row: row[timestamp], reverse=True)
            ordering_violations += rows != expected
        forbidden |= _keys(context.to_dict()) & FORBIDDEN_OUTPUT_KEYS
        require(context.provenance["synthetic_data"] is True and context.provenance["synthetic_label"] == SYNTHETIC_LABEL, f"{cif}: synthetic provenance missing")
    for value, label in ((task2_mismatches, "TASK-002"), (task3_mismatches, "TASK-003"), (task4_mismatches, "TASK-004"), (debt_mismatches, "debt"), (preview_violations, "preview limit"), (ordering_violations, "preview ordering")):
        require(value == 0, f"{label} mismatch/violation count: {value}")
    require(not forbidden, f"forbidden output keys: {sorted(forbidden)}")

    assertions: dict[str, list[bool]] = {f"G{i:02d}": [] for i in range(1, 21)}
    def golden(sid: str, condition: bool, message: str) -> None:
        assertions[sid].append(condition); require(condition, message)
    g01, g02, g04 = (by_cif[f"GOLDEN_{sid}"] for sid in ("G01", "G02", "G04"))
    golden("G01", g01.ranking["movement"] == "DEMOTED" and g01.ranking["baseline_rank"] == evaluation_map[g01.cif].baseline_rank and g01.ranking["recovery_rank"] == evaluation_map[g01.cif].recovery_rank, "G01 context failed")
    golden("G02", g02.ranking["movement"] == "PROMOTED" and g02.cashflow["inflow_7d"] > 0 and g02.ptp["status"] is not None and g02.contact["successful_outbound_calls_30d"] > 0, "G02 context failed")
    golden("G04", g04.ptp["status"] == "BROKEN" and g04.cashflow["inflow_7d"] > 0 and g04.contact["successful_outbound_calls_30d"] > 0, "G04 context failed")
    golden("G07", by_cif["GOLDEN_G07"].policy["base_route"] == "CBS" and by_cif["GOLDEN_G07"].policy["final_route"] == "CALL", "G07 route failed")
    golden("G08", by_cif["GOLDEN_G08"].policy["base_route"] == "CALL" and by_cif["GOLDEN_G08"].policy["final_route"] == "CBS", "G08 route failed")
    g19 = by_cif["GOLDEN_G19"]
    golden("G19", g19.contact["technical_call_status_counts"].get("Success", 0) > 0 and g19.ptp["status"] is None and g19.recovery_opportunity["willingness_to_pay_score"] == 0, "G19 boundary failed")
    g20 = by_cif["GOLDEN_G20"]
    golden("G20", g20.debt["loan_count"] == 3 and [int(row["outstanding_amount"]) for row in g20.debt["loans"]] == [100_000_000, 250_000_000, 50_000_000] and g20.debt["total_outstanding_cif"] == 400_000_000 and g20.debt["max_dpd_cif"] == 12, "G20 aggregation failed")
    statuses = {sid: "NOT_APPLICABLE" if not checks else "PASS" if all(checks) else "FAIL" for sid, checks in assertions.items()}
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "context_count": len(context_rows),
            "duplicate_context_cif": duplicate, "missing_context_cif": len(missing), "unexpected_context_cif": len(unexpected),
            "task2_authoritative_mismatches": task2_mismatches, "task3_authoritative_mismatches": task3_mismatches,
            "task4_authoritative_mismatches": task4_mismatches, "debt_aggregation_mismatches": debt_mismatches,
            "preview_limit_violations": preview_violations, "preview_ordering_violations": ordering_violations,
            "forbidden_output_keys": sorted(forbidden), "synthetic_label": SYNTHETIC_LABEL, "golden": statuses}


def validate_persisted(input_directory: Path, artifact_directory: Path, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> dict[str, Any]:
    """Validate serialized TASK-005 artifacts against TASK-001 source presence."""
    required_artifacts = {
        "customer_context.jsonl", "portfolio_context_index.json",
        "golden_context_validation.json", "context_manifest.json",
    }
    missing_artifacts = sorted(name for name in required_artifacts if not (artifact_directory / name).is_file())
    if missing_artifacts:
        return {"status": "FAIL", "errors": [f"missing persisted artifact: {name}" for name in missing_artifacts],
                "persisted_artifacts_parsed": 0, "persisted_contexts_checked": 0,
                "persisted_schema_errors": 0, "missing_semantic_violations": 0}

    errors: list[str] = []
    schema_errors = missing_semantic_violations = preview_violations = 0
    try:
        contexts = load_contexts(artifact_directory / "customer_context.jsonl")
        index = json.loads((artifact_directory / "portfolio_context_index.json").read_text(encoding="utf-8"))
        manifest = json.loads((artifact_directory / "context_manifest.json").read_text(encoding="utf-8"))
        golden = json.loads((artifact_directory / "golden_context_validation.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        return {"status": "FAIL", "errors": [f"malformed persisted artifact: {error}"],
                "persisted_artifacts_parsed": 0, "persisted_contexts_checked": 0,
                "persisted_schema_errors": 1, "missing_semantic_violations": 0}

    cashflow_source_cifs = {row["cif"] for row in read_csv(input_directory, "cashflow_transaction")}
    payment_source_cifs = {row["cif"] for row in read_csv(input_directory, "payment_event")}
    call_source_cifs = {row["cif"] for row in read_csv(input_directory, "call_history")}
    operation_source_cifs = {row["cif"] for row in read_csv(input_directory, "operation_result")}
    ptp_available_by_cif = {row.cif: row.ptp_status is not None for row in evaluate_policy_directory(input_directory)}
    customer_cifs = {row["cif"] for row in read_csv(input_directory, "customer")}
    seen: set[str] = set()
    forbidden: set[str] = set()
    for position, context in enumerate(contexts):
        if not isinstance(context, dict) or not REQUIRED_TOP_LEVEL <= set(context):
            schema_errors += 1
            continue
        cif = context["cif"]
        if cif in seen:
            errors.append(f"duplicate persisted context CIF: {cif}")
        seen.add(cif)
        for section, fields in REQUIRED_SECTIONS.items():
            value = context.get(section)
            if not isinstance(value, dict) or not fields <= set(value):
                schema_errors += 1
        availability = context.get("availability", {})
        cashflow = context.get("cashflow", {})
        source_available = cif in cashflow_source_cifs
        if availability.get("cashflow_available") is not source_available:
            errors.append(f"{cif}: cashflow availability differs from source presence")
        expected_availability = {
            "payment_available": cif in payment_source_cifs,
            "call_history_available": cif in call_source_cifs,
            "operation_history_available": cif in operation_source_cifs,
            "ptp_available": ptp_available_by_cif.get(cif, False),
        }
        for field, expected in expected_availability.items():
            if availability.get(field) is not expected:
                errors.append(f"{cif}: {field} differs from source/accepted presence")
        if not source_available:
            missing_semantic_violations += sum(
                cashflow.get(field) is not None for field in MISSING_CASHFLOW_DERIVED_FIELDS
            )
            missing_semantic_violations += cashflow.get("recent_transactions") != []
        transactions = cashflow.get("recent_transactions")
        if not isinstance(transactions, list):
            schema_errors += 1
        elif len(transactions) > preview_limit:
            preview_violations += 1
        forbidden |= _keys(context) & FORBIDDEN_OUTPUT_KEYS
        provenance = context.get("provenance", {})
        if provenance.get("synthetic_data") is not True or provenance.get("synthetic_label") != SYNTHETIC_LABEL:
            errors.append(f"{cif}: persisted synthetic provenance missing")

    if len(contexts) != 3000:
        errors.append(f"persisted context count {len(contexts)} != 3000")
    if seen != customer_cifs:
        errors.append(f"persisted CIF set mismatch: missing={len(customer_cifs - seen)}, unexpected={len(seen - customer_cifs)}")
    if not isinstance(index, list) or len(index) != 3000 or len({row.get("cif") for row in index if isinstance(row, dict)}) != 3000:
        schema_errors += 1
    if not isinstance(manifest, dict) or manifest.get("customer_count") != 3000:
        schema_errors += 1
    if not isinstance(golden, dict) or "golden" not in golden or "status" not in golden:
        schema_errors += 1
    if schema_errors:
        errors.append(f"persisted schema errors: {schema_errors}")
    if missing_semantic_violations:
        errors.append(f"missing cashflow scalar violations: {missing_semantic_violations}")
    if preview_violations:
        errors.append(f"persisted preview limit violations: {preview_violations}")
    if forbidden:
        errors.append(f"persisted forbidden output keys: {sorted(forbidden)}")

    base = validate(input_directory, preview_limit=preview_limit)
    errors = list(base["errors"]) + errors
    base.update({
        "status": "PASS" if not errors else "FAIL", "errors": errors,
        "persisted_artifacts_parsed": 4, "persisted_contexts_checked": len(contexts),
        "persisted_schema_errors": schema_errors,
        "missing_semantic_violations": missing_semantic_violations,
        "persisted_preview_limit_violations": preview_violations,
    })
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate deterministic TASK-005 Decision Context assembly")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/decision-context/golden_context_validation.json"))
    parser.add_argument("--artifacts", type=Path, help="TASK-005 artifact directory; defaults to --output parent")
    parser.add_argument("--preview-limit", type=int, default=DEFAULT_PREVIEW_LIMIT)
    args = parser.parse_args()
    report = validate_persisted(args.input, args.artifacts or args.output.parent, args.preview_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
