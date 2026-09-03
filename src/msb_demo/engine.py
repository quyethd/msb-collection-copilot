from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

from msb_nba.config import DEFAULT_CONFIG, NBAConfig
from msb_nba.engine import decide

from msb_tools.errors import ToolFailure

from msb_simulation.labels import (CHANNEL_LABELS, REASON_CODE_LABELS, TREATMENT_LABELS,
                                   label_for_field, label_for_value, label_for_when)

from .models import (DEMO_VERSION, DIFF_FIELDS, DecisionSnapshot, DiffEntry, DemoEvent,
                     EVENT_LABELS, SUPPORTED_EVENT_TYPES, TimelineEntry)


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
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def _invalid(message: str) -> ToolFailure:
    return ToolFailure("INVALID_ARGUMENT", message)


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


def _apply_overlay(context: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    modified = copy.deepcopy(context)
    if "inflow_7d" in overlay:
        modified["cashflow"]["inflow_7d"] = overlay["inflow_7d"]
    if "net_cashflow_30d" in overlay:
        modified["cashflow"]["net_cashflow_30d"] = overlay["net_cashflow_30d"]
    if "ptp_state" in overlay:
        modified["ptp"]["status"] = overlay["ptp_state"]
    if "promise_date" in overlay:
        modified["ptp"]["promise_date"] = overlay["promise_date"]
    return modified


def _get_input_value(context: dict[str, Any], field: str) -> Any:
    if field == "inflow_7d":
        return context["cashflow"].get("inflow_7d")
    if field == "net_cashflow_30d":
        return context["cashflow"].get("net_cashflow_30d")
    if field == "ptp_state":
        return context["ptp"].get("status") or "NONE"
    if field == "promise_date":
        return context["ptp"].get("promise_date")
    return None


def _diff(before_snap: DecisionSnapshot, after_snap: DecisionSnapshot,
          before_ctx: dict[str, Any], after_ctx: dict[str, Any]) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    before_d = before_snap.to_dict()
    after_d = after_snap.to_dict()
    for field in DIFF_FIELDS:
        if before_d[field] != after_d[field]:
            entries.append(DiffEntry(field, before_d[field], after_d[field]))
    for field in ("inflow_7d", "net_cashflow_30d", "ptp_state", "promise_date"):
        before_val = _get_input_value(before_ctx, field)
        after_val = _get_input_value(after_ctx, field)
        if before_val != after_val:
            entries.append(DiffEntry(field, before_val, after_val))
    return entries


def _format_amount(amount: int) -> str:
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} tỷ đồng"
    if amount >= 1_000_000:
        return f"{amount // 1_000_000} triệu đồng"
    if amount >= 1_000:
        return f"{amount // 1_000} nghìn đồng"
    return f"{amount} đồng"


class DemoEventEngine:
    """In-memory demo event processor — DEMO ONLY, non-persistent."""

    def __init__(self, repository, config: NBAConfig = DEFAULT_CONFIG, llm_client=None):
        self.repository = repository
        self.config = config
        self.llm_client = llm_client
        self._overlays: dict[str, dict[str, Any]] = {}
        self._timelines: dict[str, list[TimelineEntry]] = {}
        self._results: dict[tuple[str, str], dict[str, Any]] = {}

    def process_event(self, event: DemoEvent) -> dict[str, Any]:
        self._validate_event(event)
        if event.event_id is not None:
            key = (event.cif, event.event_id)
            if key in self._results:
                return self._results[key]
        original_context = self.repository.context(event.cif)
        calls = self.repository.calls_for_cif(event.cif)
        current_overlay = dict(self._overlays.get(event.cif, {}))
        before_context = _apply_overlay(original_context, current_overlay)
        before_decision = decide(before_context, calls, self.config)
        before_snap = _snapshot(before_decision, before_context)
        new_overlay = dict(current_overlay)
        self._apply_event_to_overlay(event, new_overlay, original_context)
        after_context = _apply_overlay(original_context, new_overlay)
        after_decision = decide(after_context, calls, self.config)
        after_snap = _snapshot(after_decision, after_context)
        diff = _diff(before_snap, after_snap, before_context, after_context)
        self._overlays[event.cif] = new_overlay
        explanation = self._explain(event, before_snap, after_snap, diff)
        timeline_entry = TimelineEntry(
            timestamp=event.occurred_at,
            event_type=event.event_type,
            event_label=EVENT_LABELS[event.event_type],
            before_action=before_snap.treatment,
            after_action=after_snap.treatment,
            decision_changed=len(diff) > 0,
            changed_factors=[e.to_dict() for e in diff],
            rule_before=before_snap.rule_id,
            rule_after=after_snap.rule_id,
        )
        self._timelines.setdefault(event.cif, []).append(timeline_entry)
        result = {
            "status": "success",
            "event": event.to_dict(),
            "cif": event.cif,
            "before": before_snap.to_dict(),
            "after": after_snap.to_dict(),
            "decision_changed": len(diff) > 0,
            "diff": [e.to_dict() for e in diff],
            "timeline_entry": timeline_entry.to_dict(),
            "display": self._display(event, before_snap, after_snap, diff, explanation),
            "explanation": explanation,
            "demo_version": DEMO_VERSION,
            "synthetic_data": True,
            "demo_only": True,
        }
        if event.event_id is not None:
            self._results[(event.cif, event.event_id)] = result
        return result

    def get_timeline(self, cif: str) -> list[dict[str, Any]]:
        if cif not in self.repository.cifs:
            raise ToolFailure("NOT_FOUND", f"CIF {cif!r} was not found")
        return [entry.to_dict() for entry in self._timelines.get(cif, [])]

    def reset(self, cif: str) -> dict[str, Any]:
        if cif not in self.repository.cifs:
            raise ToolFailure("NOT_FOUND", f"CIF {cif!r} was not found")
        self._overlays.pop(cif, None)
        self._timelines.pop(cif, None)
        for key in list(self._results):
            if key[0] == cif:
                del self._results[key]
        return {"status": "success", "cif": cif, "reset": True, "demo_only": True}

    def has_overlay(self, cif: str) -> bool:
        return cif in self._overlays

    def _validate_event(self, event: DemoEvent) -> None:
        if not isinstance(event.event_type, str) or event.event_type not in SUPPORTED_EVENT_TYPES:
            raise ToolFailure("UNSUPPORTED_EVENT",
                              f"Event type {event.event_type!r} is not supported. "
                              f"Supported: {sorted(SUPPORTED_EVENT_TYPES)}")
        if not isinstance(event.cif, str) or not event.cif.strip():
            raise _invalid("cif must be a non-blank string")
        if event.cif not in self.repository.cifs:
            raise ToolFailure("NOT_FOUND", f"CIF {event.cif!r} was not found")
        if not _valid_datetime(event.occurred_at):
            raise _invalid("occurred_at must be a valid ISO datetime")
        if not isinstance(event.data, dict):
            raise _invalid("data must be an object")
        if event.event_type == "CASH_IN_RECEIVED":
            amount = event.data.get("amount")
            if isinstance(amount, bool) or not isinstance(amount, int):
                raise _invalid("amount must be a positive integer")
            if amount <= 0:
                raise _invalid("amount must be greater than 0")
        elif event.event_type == "PAYMENT_PROMISE_CREATED":
            promise_date = event.data.get("promise_date")
            if not _valid_date(promise_date):
                raise _invalid("promise_date must be a valid date (YYYY-MM-DD)")
        elif event.event_type == "PAYMENT_PROMISE_BROKEN":
            pass

    def _apply_event_to_overlay(self, event: DemoEvent, overlay: dict[str, Any],
                                original_context: dict[str, Any]) -> None:
        if event.event_type == "CASH_IN_RECEIVED":
            amount = event.data["amount"]
            current_inflow = overlay.get("inflow_7d", original_context["cashflow"]["inflow_7d"])
            current_net = overlay.get("net_cashflow_30d", original_context["cashflow"]["net_cashflow_30d"])
            overlay["inflow_7d"] = current_inflow + amount
            overlay["net_cashflow_30d"] = current_net + amount
        elif event.event_type == "PAYMENT_PROMISE_CREATED":
            overlay["ptp_state"] = "OPEN"
            overlay["promise_date"] = event.data["promise_date"]
        elif event.event_type == "PAYMENT_PROMISE_BROKEN":
            overlay["ptp_state"] = "BROKEN"

    def _explain(self, event: DemoEvent, before: DecisionSnapshot,
                 after: DecisionSnapshot, diff: list[DiffEntry]) -> str:
        template = self._template_explanation(event, before, after, diff)
        if self.llm_client is None:
            return template
        prompt = self._build_llm_prompt(event, before, after, diff, template)
        try:
            content, _ = self.llm_client.complete(prompt, max_tokens=300, temperature=0)
        except Exception:
            content = None
        return content or template

    def _template_explanation(self, event: DemoEvent, before: DecisionSnapshot,
                              after: DecisionSnapshot, diff: list[DiffEntry]) -> str:
        changed = len(diff) > 0
        before_label = TREATMENT_LABELS.get(before.treatment, before.treatment)
        after_label = TREATMENT_LABELS.get(after.treatment, after.treatment)
        lq, rq = "\u201c", "\u201d"
        if event.event_type == "CASH_IN_RECEIVED":
            amount_str = _format_amount(event.data["amount"])
            if changed and after.treatment == "WAIT_SELF_CURE":
                return (f"Hệ thống vừa ghi nhận thêm {amount_str} tiền vào. "
                        f"Sau khi đánh giá lại các tín hiệu hiện tại, khách hàng đáp ứng điều kiện "
                        f"để tiếp tục chờ tự thanh toán thay vì cần liên hệ ngay.")
            if changed:
                return (f"Hệ thống vừa ghi nhận thêm {amount_str} tiền vào. "
                        f"Sau khi đánh giá lại, hệ thống chuyển đề xuất từ {lq}{before_label}{rq} "
                        f"sang {lq}{after_label}{rq}.")
            return (f"Hệ thống vừa ghi nhận thêm {amount_str} tiền vào. "
                    f"Sau khi đánh giá lại các tín hiệu hiện tại, đề xuất xử lý không thay đổi.")
        if event.event_type == "PAYMENT_PROMISE_CREATED":
            promise_date = event.data["promise_date"]
            if changed and after.treatment == "PTP_FOLLOW_UP":
                return (f"Khách hàng vừa đưa ra cam kết thanh toán vào ngày {promise_date}. "
                        f"Sau khi đánh giá lại, hệ thống chuyển sang theo dõi cam kết thanh toán "
                        f"thay vì tiếp tục đề xuất hiện tại.")
            if changed:
                return (f"Khách hàng vừa đưa ra cam kết thanh toán vào ngày {promise_date}. "
                        f"Sau khi đánh giá lại, hệ thống chuyển đề xuất từ {lq}{before_label}{rq} "
                        f"sang {lq}{after_label}{rq}.")
            return (f"Khách hàng vừa đưa ra cam kết thanh toán vào ngày {promise_date}. "
                    f"Sau khi đánh giá lại các tín hiệu hiện tại, đề xuất xử lý không thay đổi.")
        if event.event_type == "PAYMENT_PROMISE_BROKEN":
            if changed and after.treatment == "PTP_RECOVERY":
                return ("Khách hàng không thực hiện cam kết thanh toán đã đưa ra. "
                        "Sau khi đánh giá lại các tín hiệu hiện tại, hệ thống chuyển sang "
                        "xử lý cam kết thanh toán không thực hiện.")
            if changed:
                return (f"Khách hàng không thực hiện cam kết thanh toán đã đưa ra. "
                        f"Sau khi đánh giá lại, hệ thống chuyển đề xuất từ {lq}{before_label}{rq} "
                        f"sang {lq}{after_label}{rq}.")
            return ("Khách hàng không thực hiện cam kết thanh toán đã đưa ra. "
                    "Sau khi đánh giá lại các tín hiệu hiện tại, đề xuất xử lý không thay đổi.")
        return ""

    def _build_llm_prompt(self, event: DemoEvent, before: DecisionSnapshot,
                          after: DecisionSnapshot, diff: list[DiffEntry],
                          template: str) -> str:
        return (
            "You are a Vietnamese collection decision assistant. Explain the following demo event "
            "result in business-friendly Vietnamese for a non-technical listener. Do NOT change any "
            "decision values. Do NOT calculate new decisions. Do NOT claim the customer will "
            "definitely pay. Use phrases like 'đáp ứng điều kiện' or 'tín hiệu hiện tại cho phép "
            "ưu tiên'. Only produce the explanation text.\n"
            f"Event: {event.event_type} ({EVENT_LABELS[event.event_type]})\n"
            f"Before treatment: {before.treatment}\n"
            f"After treatment: {after.treatment}\n"
            f"Decision changed: {len(diff) > 0}\n"
            f"Reference explanation: {template}"
        )

    def _display(self, event: DemoEvent, before: DecisionSnapshot,
                 after: DecisionSnapshot, diff: list[DiffEntry],
                 explanation: str) -> dict[str, Any]:
        changed = len(diff) > 0
        changed_factors = []
        for entry in diff:
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
            "event_label": EVENT_LABELS[event.event_type],
            "before_event": "Trước sự kiện",
            "after_event": "Sau sự kiện",
            "decision_status": "Quyết định đã thay đổi" if changed else "Quyết định không thay đổi",
            "reason_for_change": "Lý do thay đổi" if changed else "",
            "updated_info": "Thông tin vừa cập nhật",
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
            "decision_changed": changed,
            "explanation": explanation,
            "demo_only": "API mô phỏng sự kiện nghiệp vụ",
        }
