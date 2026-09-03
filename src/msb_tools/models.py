from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypedDict, TypeVar


class ToolError(TypedDict):
    code: str
    message: str


class ToolMeta(TypedDict):
    synthetic_data: bool
    synthetic_label: str
    reference_date: str


class PortfolioInput(TypedDict, total=False):
    limit: int
    offset: int
    final_route: str
    movement: str
    hard_suppressed: bool


class Customer360Input(TypedDict):
    cif: str


class CollectionHistoryInput(Customer360Input, total=False):
    event_types: list[str]
    limit: int


class CashflowIntelligenceInput(Customer360Input):
    pass


class CollectionPolicyInput(Customer360Input):
    pass


class RecoveryOpportunityInput(Customer360Input):
    pass


PortfolioOutput = dict[str, Any]
Customer360Output = dict[str, Any]
CollectionHistoryOutput = dict[str, Any]
CashflowIntelligenceOutput = dict[str, Any]
CollectionPolicyOutput = dict[str, Any]
RecoveryOpportunityOutput = dict[str, Any]

T = TypeVar("T")


@dataclass(frozen=True)
class ToolEnvelope(Generic[T]):
    ok: bool
    tool: str
    data: T | None
    meta: ToolMeta
    error: ToolError | None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "tool": self.tool, "data": self.data,
                "meta": dict(self.meta), "error": self.error}
