from __future__ import annotations

from typing import Any

from .labels import label_for_field, label_for_value, label_for_when
from .models import SimulationResult


def display_projection(result: SimulationResult) -> dict[str, Any]:
    before = result.before
    after = result.after
    changed_factors = []
    for entry in result.diff:
        if entry.field == "when":
            before_label = label_for_when(entry.before) if isinstance(entry.before, dict) else str(entry.before)
            after_label = label_for_when(entry.after) if isinstance(entry.after, dict) else str(entry.after)
        else:
            before_label = label_for_value(entry.field, entry.before)
            after_label = label_for_value(entry.field, entry.after)
        changed_factors.append({
            "label": label_for_field(entry.field),
            "before": before_label,
            "after": after_label,
        })
    return {
        "title": "Quyết định thay đổi như thế nào?",
        "before_display": {
            "action": label_for_value("treatment", before.treatment),
            "channel": label_for_value("channel", before.channel),
            "time": label_for_when(before.when),
            "reason": label_for_value("reason_code", before.reason_code),
            "rule_id": before.rule_id,
        },
        "after_display": {
            "action": label_for_value("treatment", after.treatment),
            "channel": label_for_value("channel", after.channel),
            "time": label_for_when(after.when),
            "reason": label_for_value("reason_code", after.reason_code),
            "rule_id": after.rule_id,
        },
        "changed_factors": changed_factors,
        "decision_changed": result.decision_changed,
    }
