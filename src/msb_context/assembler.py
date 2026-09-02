from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from msb_evaluation.engine import CifEvaluation
from msb_evaluation.io import evaluate_directory as evaluate_evaluation_directory
from msb_policy.engine import PolicyResult
from msb_policy.io import evaluate_directory as evaluate_policy_directory, read_csv
from msb_recovery.engine import RecoveryOpportunityResult
from msb_recovery.io import evaluate_directory as evaluate_recovery_directory

from .models import CONTEXT_VERSION, DEFAULT_PREVIEW_LIMIT, SYNTHETIC_LABEL, DecisionContext, encode


class ContextAssemblyError(ValueError):
    """Raised when authoritative stages cannot be joined exactly by CIF."""


class ContextNotFoundError(LookupError):
    def __init__(self, cif: str):
        super().__init__(f"Decision Context not found for CIF {cif!r}")
        self.cif = cif


def _unique_map(rows: Iterable[Any], stage: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        cif = str(row.cif if hasattr(row, "cif") else row["cif"])
        if cif in result:
            raise ContextAssemblyError(f"{stage}: duplicate CIF {cif}")
        result[cif] = row
    return result


def _require_same_cifs(authoritative: Mapping[str, Mapping[str, Any]]) -> set[str]:
    source = set(authoritative["TASK-001"])
    for stage, rows in authoritative.items():
        actual = set(rows)
        missing, unexpected = sorted(source - actual), sorted(actual - source)
        if missing or unexpected:
            raise ContextAssemblyError(f"{stage}: CIF mismatch; missing={missing[:5]}, unexpected={unexpected[:5]}")
    return source


def _group(rows: Sequence[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["cif"]].append(row)
    return grouped


def _recent(rows: Sequence[dict[str, str]], timestamp: str, stable_id: str, limit: int) -> list[dict[str, str]]:
    # CTX-ORDER-001: timestamp/date DESC, then stable source ID ASC.
    ordered_ids = sorted(rows, key=lambda row: str(row[stable_id]))
    ordered = sorted(ordered_ids, key=lambda row: str(row[timestamp]), reverse=True)
    return [dict(row) for row in ordered[:limit]]


def assemble(
    customers: Sequence[dict[str, str]], loans: Sequence[dict[str, str]],
    cashflows: Sequence[dict[str, str]], payments: Sequence[dict[str, str]],
    calls: Sequence[dict[str, str]], operations: Sequence[dict[str, str]],
    policies: Sequence[PolicyResult], recoveries: Sequence[RecoveryOpportunityResult],
    evaluations: Sequence[CifEvaluation], reference_date: str, preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> list[DecisionContext]:
    if preview_limit < 0:
        raise ValueError("preview_limit must be non-negative")
    customer_map = _unique_map(customers, "TASK-001")
    policy_map = _unique_map(policies, "TASK-002")
    recovery_map = _unique_map(recoveries, "TASK-003")
    evaluation_map = _unique_map(evaluations, "TASK-004")
    cifs = _require_same_cifs({"TASK-001": customer_map, "TASK-002": policy_map, "TASK-003": recovery_map, "TASK-004": evaluation_map})
    loan_map, cash_map, payment_map, call_map, operation_map = map(_group, (loans, cashflows, payments, calls, operations))
    for family, rows in (("loan", loan_map), ("cashflow", cash_map), ("payment", payment_map), ("call", call_map), ("operation", operation_map)):
        unexpected = sorted(set(rows) - cifs)
        if unexpected:
            raise ContextAssemblyError(f"TASK-001 {family}: unexpected CIF {unexpected[:5]}")

    contexts: list[DecisionContext] = []
    for cif in sorted(cifs):
        customer, policy, recovery, evaluation = customer_map[cif], policy_map[cif], recovery_map[cif], evaluation_map[cif]
        cif_loans = loan_map.get(cif, [])
        calculated_total = sum(int(row["outstanding_amount"]) for row in cif_loans)
        calculated_max_dpd = max((int(row["dpd"]) for row in cif_loans), default=None)
        if calculated_total != policy.total_outstanding_cif or calculated_max_dpd != policy.max_dpd_cif:
            raise ContextAssemblyError(f"{cif}: debt aggregation differs from TASK-002")
        features = recovery.derived_features
        availability = {name: bool(features[name]) for name in (
            "cashflow_available", "payment_available", "ptp_available",
            "call_history_available", "operation_history_available",
        )}
        policy_section = {
            "base_route": policy.base_route, "challenge_override_route": policy.challenge_override_route,
            "final_route": policy.final_route, "hard_suppressed": policy.hard_suppressed,
            "hard_suppression_reason": policy.hard_suppression_reason,
            "source_next_action_date": policy.source_next_action_date,
            "source_next_operation_channel": policy.source_next_operation_channel,
            "latest_business_outcome": policy.latest_business_outcome,
            "business_outcome_counts": dict(policy.business_outcome_counts),
            "triggered_rule_ids": policy.triggered_rule_ids, "policy_trace": policy.policy_trace,
        }
        cash_section = {
            key: features[key] for key in (
                "inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d", "net_cashflow_30d",
                "income_sources_30d", "net_cashflow_windows_30d", "positive_cashflow_windows",
                "liquidity_to_due_ratio",
            )
        }
        if not availability["cashflow_available"]:
            # These are analytical facts derived from cashflow evidence.  TASK-003
            # may use zero contributions when evidence is absent, but TASK-005
            # must expose the underlying evidence itself as unavailable.
            for key in (
                "inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d",
                "net_cashflow_30d", "income_sources_30d",
                "net_cashflow_windows_30d", "positive_cashflow_windows",
                "liquidity_to_due_ratio",
            ):
                cash_section[key] = None
        cash_section["recent_transactions"] = _recent(cash_map.get(cif, []), "transaction_date", "transaction_id", preview_limit)
        payment_section = {
            "payment_available": availability["payment_available"],
            "recent_payment_count": len(payment_map.get(cif, [])),
            "recent_payments": _recent(payment_map.get(cif, []), "payment_date", "payment_id", preview_limit),
        }
        ptp_section = {
            "promise_date": policy.promise_date, "promise_amount": policy.promise_amount,
            "actual_paid_amount": policy.actual_paid_amount, "status": policy.ptp_status,
            "employee_assessed_ability": policy.payment_ptp_ability,
            "policy_fulfillment_ratio": policy.fulfillment_ratio,
            "scoring_fulfillment_ratio_raw": features["ptp_fulfillment_ratio"],
            "source_next_action_date": policy.source_next_action_date,
            "source_next_operation_channel": policy.source_next_operation_channel,
        }
        contact_section = {
            "call_history_available": availability["call_history_available"],
            "operation_history_available": availability["operation_history_available"],
            "outbound_attempts_30d": features["outbound_attempts_30d"],
            "successful_outbound_calls_30d": features["successful_calls_30d"],
            "technical_success_rate_30d": features["technical_success_rate_30d"],
            "utc_count_30d": features["utc_count_30d"],
            "latest_successful_outbound_date": None if features["days_since_last_successful_call"] is None else features["days_since_last_successful_call"],
            "latest_successful_outbound_days_ago": features["days_since_last_successful_call"],
            "technical_call_status_counts": dict(policy.technical_call_status_counts),
            "recent_calls": _recent(call_map.get(cif, []), "call_time", "id", preview_limit),
            "recent_operation_results": _recent(operation_map.get(cif, []), "created_at", "id", preview_limit),
        }
        # Date is deterministically recoverable from accepted days-since evidence.
        if features["days_since_last_successful_call"] is not None:
            from datetime import date, timedelta
            contact_section["latest_successful_outbound_date"] = (date.fromisoformat(reference_date) - timedelta(days=features["days_since_last_successful_call"])).isoformat()
        recovery_section = {
            "recovery_opportunity_score": recovery.recovery_opportunity_score,
            "business_urgency_score": recovery.business_urgency_score,
            "ability_to_pay_score": recovery.ability_to_pay_score,
            "willingness_to_pay_score": recovery.willingness_to_pay_score,
            "contactability_score": recovery.contactability_score,
            "timing_opportunity_score": recovery.timing_opportunity_score,
            "strategic_adjustment_score": recovery.strategic_adjustment_score,
            "component_breakdown": recovery.component_breakdown,
            "score_trace": recovery.score_trace,
            "triggered_rule_ids": recovery.triggered_rule_ids,
        }
        ranking = {key: getattr(evaluation, key) for key in (
            "baseline_rank", "recovery_rank", "rank_delta", "absolute_rank_delta",
            "normalized_rank_delta", "movement", "primary_movement_factors",
        )}
        evidence = {
            "baseline": [{"rule_id": "AGG-001", "total_outstanding_cif": policy.total_outstanding_cif}, {"rule_id": "AGG-002", "max_dpd_cif": policy.max_dpd_cif}],
            "recovery": recovery.score_trace,
            "ptp": [trace for trace in policy.policy_trace if trace.rule_id.startswith("PTP-")],
            "contact": [trace for trace in recovery.score_trace if trace.component == "CONTACTABILITY"],
            "cashflow": [trace for trace in recovery.score_trace if trace.component in {"ABILITY_TO_PAY", "TIMING_OPPORTUNITY"}],
        }
        contexts.append(DecisionContext(
            CONTEXT_VERSION, cif, reference_date, dict(customer),
            {"total_outstanding_cif": policy.total_outstanding_cif, "max_dpd_cif": policy.max_dpd_cif, "loan_count": len(cif_loans), "loans": [dict(row) for row in sorted(cif_loans, key=lambda row: row["account_id"])]},
            policy_section, cash_section, payment_section, ptp_section, contact_section,
            recovery_section, ranking, evidence, availability,
            {"synthetic_data": True, "synthetic_label": SYNTHETIC_LABEL, "reference_date": reference_date,
             "source_stage": "TASK-001", "policy_stage": "TASK-002", "recovery_stage": "TASK-003",
             "evaluation_stage": "TASK-004", "context_stage": "TASK-005"},
        ))
    return contexts


def assemble_directory(input_directory: Path, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> list[DecisionContext]:
    manifest = json.loads((input_directory / "generation_manifest.json").read_text(encoding="utf-8"))
    customers = read_csv(input_directory, "customer")
    policies = evaluate_policy_directory(input_directory)
    recoveries = evaluate_recovery_directory(input_directory)
    evaluations, _ = evaluate_evaluation_directory(input_directory)
    return assemble(customers, read_csv(input_directory, "loan_account"), read_csv(input_directory, "cashflow_transaction"),
                    read_csv(input_directory, "payment_event"), read_csv(input_directory, "call_history"),
                    read_csv(input_directory, "operation_result"), policies, recoveries, evaluations,
                    str(manifest["reference_date"]), preview_limit)


class DecisionContextStore:
    def __init__(self, contexts: Sequence[DecisionContext]):
        self._contexts = _unique_map(contexts, "TASK-005")

    def get_customer_context(self, cif: str) -> DecisionContext:
        try:
            return self._contexts[cif]
        except KeyError as error:
            raise ContextNotFoundError(cif) from error
