from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SIMULATION_VERSION = "TASK-008-V1"

SUPPORTED_CHANGES = frozenset({
    "inflow_7d", "net_cashflow_30d", "ptp_state", "promise_date",
    "source_next_action_date", "latest_business_outcome",
})

PTP_STATES = frozenset({"NONE", "OPEN", "KEPT", "PARTIAL", "BROKEN"})
BUSINESS_OUTCOMES = frozenset({"UTC", "PTP", "NPTP", "RTP", "THIRT", "NIN", "NA"})

DIFF_FIELDS = (
    "final_route", "recovery_opportunity_score", "treatment", "channel",
    "objective", "when", "rule_id", "reason_code",
)


@dataclass(frozen=True)
class DecisionSnapshot:
    final_route: str
    recovery_opportunity_score: int
    treatment: str
    channel: str
    objective: str
    when: dict[str, Any]
    rule_id: str
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_route": self.final_route,
            "recovery_opportunity_score": self.recovery_opportunity_score,
            "treatment": self.treatment,
            "channel": self.channel,
            "objective": self.objective,
            "when": self.when,
            "rule_id": self.rule_id,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class DiffEntry:
    field: str
    before: Any
    after: Any

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "before": self.before, "after": self.after}


@dataclass(frozen=True)
class SimulationResult:
    status: str
    cif: str
    before: DecisionSnapshot
    after: DecisionSnapshot
    changes_applied: dict[str, Any]
    decision_changed: bool
    diff: list[DiffEntry]
    simulation_version: str
    synthetic_data: bool
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "cif": self.cif,
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "changes_applied": self.changes_applied,
            "decision_changed": self.decision_changed,
            "diff": [entry.to_dict() for entry in self.diff],
            "simulation_version": self.simulation_version,
            "synthetic_data": self.synthetic_data,
            **({"error": self.error} if self.error else {}),
        }
