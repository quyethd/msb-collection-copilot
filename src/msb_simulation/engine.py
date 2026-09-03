from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

from msb_nba.config import DEFAULT_CONFIG, NBAConfig
from msb_nba.engine import decide

from .models import (BUSINESS_OUTCOMES, DIFF_FIELDS, PTP_STATES, SUPPORTED_CHANGES,
                     DecisionSnapshot, DiffEntry, SimulationResult, SIMULATION_VERSION)


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value).utcoffset() is not None
    except ValueError:
        return False


def _validate_changes(changes: dict[str, Any]) -> None:
    if not isinstance(changes, dict):
        raise _invalid("changes must be an object")
    unknown = set(changes) - SUPPORTED_CHANGES
    if unknown:
        raise _invalid(f"unsupported change field(s): {sorted(unknown)}")
    if "inflow_7d" in changes:
        v = changes["inflow_7d"]
        if isinstance(v, bool) or not isinstance(v, int):
            raise _invalid("inflow_7d must be an integer")
    if "net_cashflow_30d" in changes:
        v = changes["net_cashflow_30d"]
        if isinstance(v, bool) or not isinstance(v, int):
            raise _invalid("net_cashflow_30d must be an integer")
    if "ptp_state" in changes:
        v = changes["ptp_state"]
        if not isinstance(v, str) or v not in PTP_STATES:
            raise _invalid(f"ptp_state must be one of {sorted(PTP_STATES)}")
    if "promise_date" in changes:
        v = changes["promise_date"]
        if v is not None and not _valid_date(v):
            raise _invalid("promise_date must be a valid date (YYYY-MM-DD) or null")
    if "source_next_action_date" in changes:
        v = changes["source_next_action_date"]
        if v is not None and not _valid_datetime(v):
            raise _invalid("source_next_action_date must be a valid ISO datetime or null")
    if "latest_business_outcome" in changes:
        v = changes["latest_business_outcome"]
        if v is not None and (not isinstance(v, str) or v not in BUSINESS_OUTCOMES):
            raise _invalid(f"latest_business_outcome must be one of {sorted(BUSINESS_OUTCOMES)} or null")


def _invalid(message: str):
    from msb_tools.errors import ToolFailure
    return ToolFailure("INVALID_ARGUMENT", message)


def _not_found(cif: str):
    from msb_tools.errors import ToolFailure
    return ToolFailure("NOT_FOUND", f"CIF {cif!r} was not found")


def _apply_changes(context: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    modified = copy.deepcopy(context)
    if "inflow_7d" in changes:
        modified["cashflow"]["inflow_7d"] = changes["inflow_7d"]
    if "net_cashflow_30d" in changes:
        modified["cashflow"]["net_cashflow_30d"] = changes["net_cashflow_30d"]
    if "ptp_state" in changes:
        modified["ptp"]["status"] = changes["ptp_state"]
    if "promise_date" in changes:
        modified["ptp"]["promise_date"] = changes["promise_date"]
    if "source_next_action_date" in changes:
        modified["policy"]["source_next_action_date"] = changes["source_next_action_date"]
    if "latest_business_outcome" in changes:
        modified["policy"]["latest_business_outcome"] = changes["latest_business_outcome"]
    return modified


def _snapshot(decision, context: dict[str, Any]) -> DecisionSnapshot:
    return DecisionSnapshot(
        final_route=decision.policy["final_route"],
        recovery_opportunity_score=context["recovery_opportunity"]["recovery_opportunity_score"],
        treatment=decision.recommendation.treatment,
        channel=decision.recommendation.channel,
        objective=decision.recommendation.objective,
        when={
            "type": decision.recommendation.when.type,
            "datetime": decision.recommendation.when.datetime,
            "date": decision.recommendation.when.date,
            "window": decision.recommendation.when.window,
        },
        rule_id=decision.selected_rule.rule_id,
        reason_code=decision.selected_rule.reason_code,
    )


def _get_original_input_value(context: dict[str, Any], field: str) -> Any:
    if field == "inflow_7d":
        return context["cashflow"].get("inflow_7d")
    if field == "net_cashflow_30d":
        return context["cashflow"].get("net_cashflow_30d")
    if field == "ptp_state":
        return context["ptp"].get("status") or "NONE"
    if field == "promise_date":
        return context["ptp"].get("promise_date")
    if field == "source_next_action_date":
        return context["policy"].get("source_next_action_date")
    if field == "latest_business_outcome":
        return context["policy"].get("latest_business_outcome")
    return None


def _diff(before: DecisionSnapshot, after: DecisionSnapshot,
          original_context: dict[str, Any], changes: dict[str, Any]) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    before_d = before.to_dict()
    after_d = after.to_dict()
    for field in DIFF_FIELDS:
        if before_d[field] != after_d[field]:
            entries.append(DiffEntry(field, before_d[field], after_d[field]))
    for field, new_value in changes.items():
        original = _get_original_input_value(original_context, field)
        if original != new_value:
            entries.append(DiffEntry(field, original, new_value))
    return entries


class SimulationEngine:
    def __init__(self, repository, config: NBAConfig = DEFAULT_CONFIG):
        self.repository = repository
        self.config = config

    def simulate(self, cif: str, changes: dict[str, Any]) -> SimulationResult:
        if not isinstance(cif, str) or not cif.strip():
            raise _invalid("cif must be a non-blank string")
        if cif not in self.repository.cifs:
            raise _not_found(cif)
        _validate_changes(changes)
        original_context = self.repository.context(cif)
        calls = self.repository.calls_for_cif(cif)
        before_decision = decide(original_context, calls, self.config)
        before_snapshot = _snapshot(before_decision, original_context)
        modified_context = _apply_changes(original_context, changes)
        after_decision = decide(modified_context, calls, self.config)
        after_snapshot = _snapshot(after_decision, modified_context)
        diff = _diff(before_snapshot, after_snapshot, original_context, changes)
        return SimulationResult(
            status="success",
            cif=cif,
            before=before_snapshot,
            after=after_snapshot,
            changes_applied=copy.deepcopy(changes),
            decision_changed=len(diff) > 0,
            diff=diff,
            simulation_version=SIMULATION_VERSION,
            synthetic_data=True,
        )
