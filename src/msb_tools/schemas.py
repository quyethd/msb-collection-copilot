from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DESCRIPTIONS = {
    "get_portfolio": "Return accepted portfolio ranks, movements, scores, routes, availability and debt aggregates with validated pagination and exact filters.",
    "get_customer_360": "Return the complete accepted TASK-005 Decision Context for one synthetic CIF without summarization or reinterpretation.",
    "get_collection_history": "Return accepted source call, operation, payment and PTP-operation events for one synthetic CIF in deterministic order.",
    "get_cashflow_intelligence": "Return accepted cashflow facts, source transactions and deterministic scoring evidence for one synthetic CIF while preserving missing values.",
    "get_collection_policy": "Return accepted read-only collection routes, suppression facts, source next-action fields and deterministic policy trace for one synthetic CIF.",
    "get_recovery_opportunity": "Return accepted Recovery Opportunity score, component scores, ranks, movement and supporting deterministic evidence for one synthetic CIF; the score is not a probability or expected value.",
}


def _object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": False}
    if required: value["required"] = required
    return value


def _nullable(*types: str) -> dict[str, Any]:
    return {"type": [*types, "null"]}


def _array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def schema_document() -> dict[str, Any]:
    cif = {"type": "string", "minLength": 1}
    single = _object({"cif": cif}, ["cif"])
    tools = [
        {"name": "get_portfolio", "description": DESCRIPTIONS["get_portfolio"], "input_schema": _object({
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            "offset": {"type": "integer", "minimum": 0, "default": 0},
            "final_route": {"type": "string", "enum": ["CALL", "CBS", "OTHER"]},
            "movement": {"type": "string", "enum": ["DEMOTED", "PROMOTED", "UNCHANGED"]},
            "hard_suppressed": {"type": "boolean"}}), "output_schema": {"$ref": "#/$defs/PortfolioOutput"}},
        {"name": "get_customer_360", "description": DESCRIPTIONS["get_customer_360"], "input_schema": single, "output_schema": {"$ref": "#/$defs/Customer360Output"}},
        {"name": "get_collection_history", "description": DESCRIPTIONS["get_collection_history"], "input_schema": _object({
            "cif": cif, "event_types": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": ["CALL", "OPERATION", "PAYMENT", "PTP"]}},
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}}, ["cif"]), "output_schema": {"$ref": "#/$defs/CollectionHistoryOutput"}},
        {"name": "get_cashflow_intelligence", "description": DESCRIPTIONS["get_cashflow_intelligence"], "input_schema": single, "output_schema": {"$ref": "#/$defs/CashflowIntelligenceOutput"}},
        {"name": "get_collection_policy", "description": DESCRIPTIONS["get_collection_policy"], "input_schema": single, "output_schema": {"$ref": "#/$defs/CollectionPolicyOutput"}},
        {"name": "get_recovery_opportunity", "description": DESCRIPTIONS["get_recovery_opportunity"], "input_schema": single, "output_schema": {"$ref": "#/$defs/RecoveryOpportunityOutput"}},
    ]
    route = {"type": "string", "enum": ["CALL", "CBS", "OTHER"]}
    movement = {"type": "string", "enum": ["DEMOTED", "PROMOTED", "UNCHANGED"]}
    integer_or_null = _nullable("integer")
    decimal_or_null = {"type": ["integer", "string", "null"]}
    string_or_null = _nullable("string")
    string_array = _array({"type": "string"})
    defs: dict[str, Any] = {
        "ToolError": _object({"code": {"enum": ["INVALID_ARGUMENT", "NOT_FOUND", "DATA_INTEGRITY_ERROR", "INTERNAL_ERROR"]}, "message": {"type": "string"}}, ["code", "message"]),
        "ToolMeta": _object({"synthetic_data": {"const": True}, "synthetic_label": {"const": "SYNTHETIC PROTOTYPE DATA"}, "reference_date": {"type": "string", "format": "date"}}, ["synthetic_data", "synthetic_label", "reference_date"]),
        "Availability": _object({
            "cashflow_available": {"type": "boolean"}, "payment_available": {"type": "boolean"},
            "ptp_available": {"type": "boolean"}, "call_history_available": {"type": "boolean"},
            "operation_history_available": {"type": "boolean"}},
            ["cashflow_available", "payment_available", "ptp_available", "call_history_available", "operation_history_available"]),
        "Transaction": _object({k: {"type": "string"} for k in
            ("transaction_id", "cif", "transaction_date", "direction", "amount", "source_type", "balance_after")},
            ["transaction_id", "cif", "transaction_date", "direction", "amount", "source_type", "balance_after"]),
        "CashflowFacts": _object({
            "inflow_3d": integer_or_null, "inflow_7d": integer_or_null, "inflow_30d": integer_or_null,
            "outflow_30d": integer_or_null, "net_cashflow_30d": integer_or_null,
            "net_cashflow_windows_30d": {"anyOf": [_array({"type": "integer"}), {"type": "null"}]},
            "positive_cashflow_windows": integer_or_null,
            "income_sources_30d": {"anyOf": [string_array, {"type": "null"}]},
            "liquidity_to_due_ratio": decimal_or_null,
            "recent_transactions": _array({"$ref": "#/$defs/Transaction"})},
            ["inflow_3d", "inflow_7d", "inflow_30d", "outflow_30d", "net_cashflow_30d",
             "net_cashflow_windows_30d", "positive_cashflow_windows", "income_sources_30d",
             "liquidity_to_due_ratio", "recent_transactions"]),
        "RuleEvidence": _object({
            "rule_id": {"type": "string"}, "result": {"type": "string"},
            "component": {"type": "string"}, "points": {"type": "integer"},
            "evidence": {"type": "object", "additionalProperties": {"$ref": "#/$defs/JsonValue"}}},
            ["rule_id", "result", "component", "points", "evidence"]),
        "PolicyTrace": _object({
            "rule_id": {"type": "string"}, "result": {"type": "string"},
            "evidence": {"type": "object", "additionalProperties": {"$ref": "#/$defs/JsonValue"}}},
            ["rule_id", "result", "evidence"]),
        "BusinessOutcomeCounts": _object({k: {"type": "integer"} for k in
            ("UTC", "PTP", "NPTP", "RTP", "THIRT", "NIN", "NA")},
            ["UTC", "PTP", "NPTP", "RTP", "THIRT", "NIN", "NA"]),
        "PolicyFacts": _object({
            "base_route": route, "challenge_override_route": {"anyOf": [route, {"type": "null"}]},
            "final_route": route, "hard_suppressed": {"type": "boolean"},
            "hard_suppression_reason": string_or_null, "latest_business_outcome": string_or_null,
            "business_outcome_counts": {"$ref": "#/$defs/BusinessOutcomeCounts"},
            "source_next_action_date": string_or_null, "source_next_operation_channel": string_or_null,
            "triggered_rule_ids": string_array, "policy_trace": _array({"$ref": "#/$defs/PolicyTrace"})},
            ["base_route", "challenge_override_route", "final_route", "hard_suppressed",
             "hard_suppression_reason", "latest_business_outcome", "business_outcome_counts",
             "source_next_action_date", "source_next_operation_channel", "triggered_rule_ids", "policy_trace"]),
        "MovementFactor": _object({
            "factor": {"type": "string"}, "score": {"type": "integer"}, "max_score": {"type": "integer"},
            "supporting_rule_ids": string_array}, ["factor", "score", "max_score", "supporting_rule_ids"]),
        "Ranking": _object({
            "baseline_rank": {"type": "integer"}, "recovery_rank": {"type": "integer"},
            "rank_delta": {"type": "integer"}, "absolute_rank_delta": {"type": "integer"},
            "normalized_rank_delta": {"type": "string"}, "movement": movement,
            "primary_movement_factors": _array({"$ref": "#/$defs/MovementFactor"})},
            ["baseline_rank", "recovery_rank", "rank_delta", "absolute_rank_delta",
             "normalized_rank_delta", "movement", "primary_movement_factors"]),
        "ScoreTrace": {"$ref": "#/$defs/RuleEvidence"},
        "ComponentBreakdown": _object({
            "name": {"type": "string"}, "score": {"type": "integer"}, "max_score": {"type": "integer"},
            "triggered_rule_ids": string_array,
            "evidence": {"type": "object", "additionalProperties": {"$ref": "#/$defs/JsonValue"}}},
            ["name", "score", "max_score", "triggered_rule_ids", "evidence"]),
        "RecoveryFacts": _object({
            "recovery_opportunity_score": {"type": "integer"}, "business_urgency_score": {"type": "integer"},
            "ability_to_pay_score": {"type": "integer"}, "willingness_to_pay_score": {"type": "integer"},
            "contactability_score": {"type": "integer"}, "timing_opportunity_score": {"type": "integer"},
            "strategic_adjustment_score": {"type": "integer"},
            "component_breakdown": _array({"$ref": "#/$defs/ComponentBreakdown"}),
            "score_trace": _array({"$ref": "#/$defs/ScoreTrace"}), "triggered_rule_ids": string_array},
            ["recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score",
             "willingness_to_pay_score", "contactability_score", "timing_opportunity_score",
             "strategic_adjustment_score", "component_breakdown", "score_trace", "triggered_rule_ids"]),
    }
    defs.update(_source_and_context_definitions(route, movement, integer_or_null, decimal_or_null,
                                                string_or_null, string_array))
    defs["ToolEnvelope"] = _object({"ok": {"type": "boolean"}, "tool": {"type": "string"}, "data": {"type": ["object", "null"]}, "meta": {"$ref": "#/$defs/ToolMeta"}, "error": {"anyOf": [{"$ref": "#/$defs/ToolError"}, {"type": "null"}]}}, ["ok", "tool", "data", "meta", "error"])
    return {"schema_version": SCHEMA_VERSION, "tools": tools, "$defs": defs}


def _source_and_context_definitions(route: dict[str, Any], movement: dict[str, Any],
                                    integer_or_null: dict[str, Any], decimal_or_null: dict[str, Any],
                                    string_or_null: dict[str, Any], string_array: dict[str, Any]) -> dict[str, Any]:
    strings = lambda names: _object({name: {"type": "string"} for name in names}, list(names))
    customer = strings(("cif", "customer_name", "segment", "heatmap", "created_at"))
    loan = strings(("account_id", "cif", "product_type", "outstanding_amount", "overdue_amount",
                    "dpd", "due_amount", "due_date", "status"))
    debt = _object({"loan_count": {"type": "integer"}, "total_outstanding_cif": {"type": "integer"},
                    "max_dpd_cif": {"type": "integer"}, "loans": _array(loan)},
                   ["loan_count", "total_outstanding_cif", "max_dpd_cif", "loans"])
    payment_event = strings(("payment_id", "cif", "account_id", "payment_date", "amount",
                             "payment_type", "linked_ptp_id"))
    payment = _object({"payment_available": {"type": "boolean"}, "recent_payment_count": {"type": "integer"},
                       "recent_payments": _array(payment_event)},
                      ["payment_available", "recent_payment_count", "recent_payments"])
    ptp = _object({
        "status": string_or_null, "promise_amount": integer_or_null, "promise_date": string_or_null,
        "actual_paid_amount": integer_or_null, "policy_fulfillment_ratio": decimal_or_null,
        "scoring_fulfillment_ratio_raw": decimal_or_null, "employee_assessed_ability": string_or_null,
        "source_next_action_date": string_or_null, "source_next_operation_channel": string_or_null},
        ["status", "promise_amount", "promise_date", "actual_paid_amount", "policy_fulfillment_ratio",
         "scoring_fulfillment_ratio_raw", "employee_assessed_ability", "source_next_action_date",
         "source_next_operation_channel"])
    call_fields = ("id", "call_id", "request_code", "cif", "customer_name", "call_phone", "relationship",
                   "destination_name", "call_type", "start_at", "end_at", "call_time", "end_time",
                   "ring_duration", "talk_duration", "status", "pbx", "extension", "employee_name",
                   "record_file", "operation_status", "operation_source", "created_at", "created_by",
                   "updated_at", "updated_by")
    call_event = strings(call_fields)
    operation_fields = ("id", "cif", "operation_result", "operation_object", "operation_address", "relation",
                        "detail_relation", "overdue_reason", "detail_overdue_reason", "income_status", "work_status",
                        "overall_customer_assessment", "payment_ptp_ability", "payment_ptp_number", "payment_ptp_date",
                        "proposed_solution", "debt_solution", "affected_repayment_source", "next_action_date",
                        "next_operation_channel", "is_current_phone_number", "is_current_address",
                        "is_change_contact_info", "new_phone_number", "need_investigation",
                        "detail_operation_content", "created_at", "created_by", "updated_at", "updated_by")
    operation_event = strings(operation_fields)
    status_counts = {"type": "object", "additionalProperties": {"type": "integer"}}
    contact = _object({
        "call_history_available": {"type": "boolean"}, "operation_history_available": {"type": "boolean"},
        "outbound_attempts_30d": {"type": "integer"}, "successful_outbound_calls_30d": {"type": "integer"},
        "technical_success_rate_30d": decimal_or_null, "utc_count_30d": {"type": "integer"},
        "latest_successful_outbound_date": string_or_null,
        "latest_successful_outbound_days_ago": integer_or_null,
        "technical_call_status_counts": status_counts, "recent_calls": _array(call_event),
        "recent_operation_results": _array(operation_event)},
        ["call_history_available", "operation_history_available", "outbound_attempts_30d",
         "successful_outbound_calls_30d", "technical_success_rate_30d", "utc_count_30d",
         "latest_successful_outbound_date", "latest_successful_outbound_days_ago",
         "technical_call_status_counts", "recent_calls", "recent_operation_results"])
    baseline_evidence = {"oneOf": [
        _object({"rule_id": {"const": "AGG-001"}, "total_outstanding_cif": {"type": "integer"}},
                ["rule_id", "total_outstanding_cif"]),
        _object({"rule_id": {"const": "AGG-002"}, "max_dpd_cif": {"type": "integer"}},
                ["rule_id", "max_dpd_cif"]),
    ]}
    evidence = _object({
        "baseline": _array(baseline_evidence), "cashflow": _array({"$ref": "#/$defs/RuleEvidence"}),
        "ptp": _array({"$ref": "#/$defs/PolicyTrace"}),
        "contact": _array({"$ref": "#/$defs/RuleEvidence"}),
        "recovery": _array({"$ref": "#/$defs/RuleEvidence"})},
        ["baseline", "cashflow", "ptp", "contact", "recovery"])
    provenance = _object({
        "synthetic_data": {"const": True}, "synthetic_label": {"const": "SYNTHETIC PROTOTYPE DATA"},
        "reference_date": {"type": "string"}, "source_stage": {"type": "string"},
        "policy_stage": {"type": "string"}, "recovery_stage": {"type": "string"},
        "evaluation_stage": {"type": "string"}, "context_stage": {"type": "string"}},
        ["synthetic_data", "synthetic_label", "reference_date", "source_stage", "policy_stage",
         "recovery_stage", "evaluation_stage", "context_stage"])
    context = _object({
        "context_version": {"type": "string"}, "cif": {"type": "string"}, "as_of_date": {"type": "string"},
        "customer": customer, "debt": debt, "policy": {"$ref": "#/$defs/PolicyFacts"},
        "cashflow": {"$ref": "#/$defs/CashflowFacts"}, "payment": payment, "ptp": ptp,
        "contact": contact, "recovery_opportunity": {"$ref": "#/$defs/RecoveryFacts"},
        "ranking": {"$ref": "#/$defs/Ranking"}, "evidence": evidence,
        "availability": {"$ref": "#/$defs/Availability"}, "provenance": provenance},
        ["context_version", "cif", "as_of_date", "customer", "debt", "policy", "cashflow", "payment",
         "ptp", "contact", "recovery_opportunity", "ranking", "evidence", "availability", "provenance"])
    portfolio_fields = {
        "cif": {"type": "string"}, "final_route": route, "hard_suppressed": {"type": "boolean"},
        "total_outstanding_cif": {"type": "integer"}, "max_dpd_cif": {"type": "integer"},
        "baseline_rank": {"type": "integer"}, "recovery_rank": {"type": "integer"},
        "rank_delta": {"type": "integer"}, "movement": movement,
        "recovery_opportunity_score": {"type": "integer"}, "business_urgency_score": {"type": "integer"},
        "ability_to_pay_score": {"type": "integer"}, "willingness_to_pay_score": {"type": "integer"},
        "contactability_score": {"type": "integer"}, "timing_opportunity_score": {"type": "integer"},
        "strategic_adjustment_score": {"type": "integer"}, "availability": {"$ref": "#/$defs/Availability"},
        "synthetic_label": {"const": "SYNTHETIC PROTOTYPE DATA"}}
    portfolio_row = _object(portfolio_fields, list(portfolio_fields))
    portfolio_output_fields = {
        "items": _array(portfolio_row), "total_matching": {"type": "integer"},
        "limit": {"type": "integer"}, "offset": {"type": "integer"}, "synthetic_data": {"const": True},
        "synthetic_label": {"const": "SYNTHETIC PROTOTYPE DATA"}, "reference_date": {"type": "string"}}
    history_event = _object({
        "event_type": {"enum": ["CALL", "OPERATION", "PAYMENT", "PTP"]}, "source_id": {"type": "string"},
        "event_timestamp": {"type": "string"},
        "payload": {"oneOf": [call_event, operation_event, payment_event]}},
        ["event_type", "source_id", "event_timestamp", "payload"])
    history_fields = {"cif": {"type": "string"}, "events": _array(history_event),
                      "total_matching": {"type": "integer"}, "limit": {"type": "integer"},
                      "ptp_mapping": {"type": "string"}}
    cashflow_fields = {"cif": {"type": "string"}, "cashflow_available": {"type": "boolean"},
                       **{k: v for k, v in _dereference_properties("CashflowFacts").items()},
                       "scoring_evidence": _array({"$ref": "#/$defs/RuleEvidence"}),
                       "accepted_rule_ids": string_array}
    policy_fields = {"cif": {"type": "string"}, **_dereference_properties("PolicyFacts")}
    recovery_fields = {"cif": {"type": "string"}, **_dereference_properties("RecoveryFacts"),
                       **_dereference_properties("Ranking"), "score_semantics": {"type": "string"}}
    return {
        "CallEventPayload": call_event, "OperationEventPayload": operation_event,
        "PaymentEventPayload": payment_event,
        "Customer360Output": context,
        "PortfolioOutput": _object(portfolio_output_fields, list(portfolio_output_fields)),
        "CollectionHistoryOutput": _object(history_fields, list(history_fields)),
        "CashflowIntelligenceOutput": _object(cashflow_fields, list(cashflow_fields)),
        "CollectionPolicyOutput": _object(policy_fields, list(policy_fields)),
        "RecoveryOpportunityOutput": _object(recovery_fields, list(recovery_fields)),
        "JsonValue": {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "boolean"},
                                  {"type": "null"}, _array({"$ref": "#/$defs/JsonValue"}),
                                  {"type": "object", "additionalProperties": {"$ref": "#/$defs/JsonValue"}}]},
    }


def _dereference_properties(name: str) -> dict[str, Any]:
    """Stable field templates for flat tool projections of shared context sections."""
    if name == "CashflowFacts":
        return {
            "inflow_3d": _nullable("integer"), "inflow_7d": _nullable("integer"),
            "inflow_30d": _nullable("integer"), "outflow_30d": _nullable("integer"),
            "net_cashflow_30d": _nullable("integer"),
            "net_cashflow_windows_30d": {"anyOf": [_array({"type": "integer"}), {"type": "null"}]},
            "positive_cashflow_windows": _nullable("integer"),
            "income_sources_30d": {"anyOf": [_array({"type": "string"}), {"type": "null"}]},
            "liquidity_to_due_ratio": {"type": ["integer", "string", "null"]},
            "recent_transactions": _array({"$ref": "#/$defs/Transaction"})}
    if name == "PolicyFacts":
        return {key: {"$ref": f"#/$defs/PolicyFacts/properties/{key}"} for key in
                ("base_route", "challenge_override_route", "final_route", "hard_suppressed",
                 "hard_suppression_reason", "latest_business_outcome", "business_outcome_counts",
                 "source_next_action_date", "source_next_operation_channel", "triggered_rule_ids", "policy_trace")}
    recovery = ("recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score",
                "willingness_to_pay_score", "contactability_score", "timing_opportunity_score",
                "strategic_adjustment_score", "component_breakdown", "score_trace", "triggered_rule_ids")
    ranking = ("baseline_rank", "recovery_rank", "rank_delta", "absolute_rank_delta",
               "normalized_rank_delta", "movement", "primary_movement_factors")
    section = "RecoveryFacts" if name == "RecoveryFacts" else "Ranking"
    return {key: {"$ref": f"#/$defs/{section}/properties/{key}"} for key in (recovery if name == "RecoveryFacts" else ranking)}


def registry_manifest(reference_date: str) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "tool_count": 6,
            "tool_names": list(DESCRIPTIONS), "synthetic_data": True,
            "synthetic_label": "SYNTHETIC PROTOTYPE DATA", "reference_date": reference_date}


def write_schema_artifacts(output: Path, reference_date: str, validation: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, value in (("tool_schemas.json", schema_document()),
                        ("tool_registry_manifest.json", registry_manifest(reference_date)),
                        ("golden_tool_validation.json", validation)):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
