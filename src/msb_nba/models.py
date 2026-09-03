from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

WhenType = Literal["SOURCE_DATETIME", "SOURCE_DATE", "BEST_WINDOW", "TODAY", "NONE"]
Window = Literal["08-10", "10-12", "13-15", "15-17", "17-19"]


@dataclass(frozen=True)
class When:
    type: WhenType
    datetime: str | None = None
    date: str | None = None
    window: Window | None = None

    def __post_init__(self) -> None:
        valid = {
            "SOURCE_DATETIME": self.datetime is not None and self.date is None and self.window is None,
            "SOURCE_DATE": self.datetime is None and self.date is not None and self.window is None,
            "BEST_WINDOW": self.datetime is None and self.date is not None and self.window is not None,
            "TODAY": self.datetime is None and self.date is not None and self.window is None,
            "NONE": self.datetime is None and self.date is None and self.window is None,
        }
        if self.type not in valid or not valid[self.type]:
            raise ValueError(f"invalid WHEN shape for {self.type}")
        if self.window is not None and self.window not in {"08-10", "10-12", "13-15", "15-17", "17-19"}:
            raise ValueError("invalid WHEN window")


@dataclass(frozen=True)
class Recommendation:
    treatment: str
    channel: str
    when: When
    objective: str


@dataclass(frozen=True)
class SelectedRule:
    rule_id: str
    priority: str
    reason_code: str


@dataclass(frozen=True)
class TraceEntry:
    rule_id: str
    matched: bool
    effect: str | None


@dataclass(frozen=True)
class NBADecision:
    decision_version: str
    cif: str
    reference_date: str
    policy: dict[str, Any]
    recommendation: Recommendation
    selected_rule: SelectedRule
    decision_trace: tuple[TraceEntry, ...]
    evidence_refs: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
