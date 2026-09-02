from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

CONTEXT_VERSION = "1.0"
SYNTHETIC_LABEL = "SYNTHETIC PROTOTYPE DATA"
DEFAULT_PREVIEW_LIMIT = 10


def encode(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return encode(asdict(value))
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (tuple, list)):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class DecisionContext:
    context_version: str
    cif: str
    as_of_date: str
    customer: dict[str, Any]
    debt: dict[str, Any]
    policy: dict[str, Any]
    cashflow: dict[str, Any]
    payment: dict[str, Any]
    ptp: dict[str, Any]
    contact: dict[str, Any]
    recovery_opportunity: dict[str, Any]
    ranking: dict[str, Any]
    evidence: dict[str, Any]
    availability: dict[str, bool]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return encode(asdict(self))
