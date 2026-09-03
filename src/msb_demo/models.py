from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEMO_VERSION = "TASK-008B-V1"

SUPPORTED_EVENT_TYPES = frozenset({
    "CASH_IN_RECEIVED",
    "PAYMENT_PROMISE_CREATED",
    "PAYMENT_PROMISE_BROKEN",
})

EVENT_LABELS: dict[str, str] = {
    "CASH_IN_RECEIVED": "Có tiền vào mới",
    "PAYMENT_PROMISE_CREATED": "Có cam kết thanh toán mới",
    "PAYMENT_PROMISE_BROKEN": "Không thực hiện cam kết thanh toán",
}

DISPLAY_LABELS: dict[str, str] = {
    "before_event": "Trước sự kiện",
    "after_event": "Sau sự kiện",
    "decision_changed": "Quyết định đã thay đổi",
    "decision_not_changed": "Quyết định không thay đổi",
    "reason_for_change": "Lý do thay đổi",
    "updated_info": "Thông tin vừa cập nhật",
    "demo_only": "API mô phỏng sự kiện nghiệp vụ",
}

DIFF_FIELDS = (
    "final_route", "recovery_opportunity_score", "treatment", "channel",
    "objective", "when", "rule_id", "reason_code",
)


@dataclass(frozen=True)
class DemoEvent:
    event_type: str
    cif: str
    occurred_at: str
    data: dict[str, Any]
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "event_type": self.event_type,
            "cif": self.cif,
            "occurred_at": self.occurred_at,
            "data": dict(self.data),
        }
        if self.event_id is not None:
            result["event_id"] = self.event_id
        return result


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
class TimelineEntry:
    timestamp: str
    event_type: str
    event_label: str
    before_action: str
    after_action: str
    decision_changed: bool
    changed_factors: list[dict[str, Any]]
    rule_before: str
    rule_after: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "event_label": self.event_label,
            "before_action": self.before_action,
            "after_action": self.after_action,
            "decision_changed": self.decision_changed,
            "changed_factors": list(self.changed_factors),
            "rule_before": self.rule_before,
            "rule_after": self.rule_after,
        }
