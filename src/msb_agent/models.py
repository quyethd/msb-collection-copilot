from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Mode = Literal["PLAN", "INVESTIGATE", "EXPLAIN", "SIMULATE"]
MODES: tuple[Mode, ...] = ("PLAN", "INVESTIGATE", "EXPLAIN", "SIMULATE")

CANONICAL_MODEL = "glm-5.2"
SIMULATE_RESULT = "TASK_008_REQUIRED"
AGENT_VERSION = "TASK-007B-V1"

FORBIDDEN_LLM_FIELDS = frozenset({
    "treatment", "channel", "objective", "when", "final_route", "rule_id",
    "reason_code", "priority", "hard_suppressed", "routing", "score",
})


@dataclass(frozen=True)
class AgentResponse:
    status: str
    mode: Mode
    cif: str | None
    decision: dict[str, Any] | None
    evidence: list[dict[str, Any]]
    summary: str
    tools_used: list[str]
    canonical_model: str | None
    synthetic_data: bool
    agent_version: str
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "cif": self.cif,
            "decision": self.decision,
            "evidence": self.evidence,
            "summary": self.summary,
            "tools_used": self.tools_used,
            "canonical_model": self.canonical_model,
            "synthetic_data": self.synthetic_data,
            "agent_version": self.agent_version,
            **({"error": self.error} if self.error else {}),
        }


def decision_from_nba(nba_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "final_route": nba_data["final_route"],
        "treatment": nba_data["treatment"],
        "channel": nba_data["channel"],
        "objective": nba_data["objective"],
        "when": nba_data["when"],
        "rule_id": nba_data["rule_id"],
        "reason_code": nba_data["reason_code"],
    }
