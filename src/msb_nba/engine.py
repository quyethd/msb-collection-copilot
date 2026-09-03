from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence

from .config import DEFAULT_CONFIG, NBAConfig
from .models import NBADecision, Recommendation, SelectedRule, TraceEntry, When
from .rules import RULE_META, RULE_ORDER
from .timing import select_best_window

DECISION_VERSION = "TASK-007A-V1"


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str): return False
    try: return datetime.fromisoformat(value).utcoffset() is not None
    except ValueError: return False


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str): return False
    try: date.fromisoformat(value); return True
    except ValueError: return False


def decide(context: Mapping[str, Any], calls: Sequence[Mapping[str, Any]], config: NBAConfig = DEFAULT_CONFIG) -> NBADecision:
    cif, ref = str(context["cif"]), str(context.get("as_of_date") or context["provenance"]["reference_date"])
    policy, ptp, cash, availability, debt = context["policy"], context["ptp"], context["cashflow"], context["availability"], context["debt"]
    outcome, state, route = policy.get("latest_business_outcome"), ptp.get("status") or "NONE", policy["final_route"]
    source_dt, promise_date = policy.get("source_next_action_date"), ptp.get("promise_date")
    self_cure = (route in {"CALL", "CBS"} and int(debt["max_dpd_cif"]) <= config.self_cure_max_dpd and state == "NONE"
                 and outcome not in {"RTP", "NIN"} and availability["cashflow_available"] is True
                 and Decimal(str(cash["net_cashflow_30d"])) > 0
                 and Decimal(str(cash["inflow_7d"])) >= config.self_cure_min_inflow_7d_vnd
                 and policy["hard_suppressed"] is False and source_dt is None)
    conditions = {
        "NBA-000": policy["hard_suppressed"] is True,
        "NBA-100": outcome == "NA" and _valid_datetime(source_dt),
        "NBA-110": outcome == "NIN",
        "NBA-200": state == "PARTIAL",
        "NBA-210": state == "BROKEN" and availability["cashflow_available"] is True and Decimal(str(cash["inflow_3d"])) >= config.broken_ptp_recent_inflow_threshold_vnd,
        "NBA-220": state == "BROKEN",
        "NBA-230": state == "OPEN",
        "NBA-240": state == "KEPT",
        "NBA-300": self_cure and route == "CALL",
        "NBA-310": self_cure and route == "CBS",
        "NBA-400": route == "CALL" and outcome == "RTP",
        "NBA-900": route == "CALL", "NBA-910": route == "CBS", "NBA-920": route == "OTHER",
    }
    trace = []
    selected = None
    for rule_id in RULE_ORDER:
        matched = conditions[rule_id]
        trace.append(TraceEntry(rule_id, matched, "SELECTED" if matched else None))
        if matched: selected = rule_id; break
    if selected is None: raise ValueError(f"{cif}: final_route {route!r} has no authorized default")
    priority, reason, treatment, channel, objective = RULE_META[selected]
    best_evidence = None
    if selected == "NBA-100": when = When("SOURCE_DATETIME", datetime=source_dt)
    elif selected == "NBA-110": when = When("TODAY", date=ref)
    elif selected == "NBA-230" and _valid_datetime(source_dt): when = When("SOURCE_DATETIME", datetime=source_dt)
    elif selected == "NBA-230" and _valid_date(promise_date) and promise_date >= ref: when = When("SOURCE_DATE", date=promise_date)
    elif selected in {"NBA-200", "NBA-210", "NBA-220", "NBA-230", "NBA-400", "NBA-900", "NBA-910"}:
        window, best_evidence = select_best_window(calls, date.fromisoformat(ref), config)
        when = When("BEST_WINDOW", date=ref, window=window)
    else: when = When("NONE")
    facts = {"final_route": route, "hard_suppressed": policy["hard_suppressed"], "latest_business_outcome": outcome,
             "ptp_state": state, "max_dpd_cif": debt["max_dpd_cif"], "cashflow_available": availability["cashflow_available"],
             "inflow_3d": cash.get("inflow_3d"), "inflow_7d": cash.get("inflow_7d"), "net_cashflow_30d": cash.get("net_cashflow_30d"),
             "source_next_action_date": source_dt, "promise_date": promise_date}
    evidence = {"selected_rule_facts": facts}
    if best_evidence is not None: evidence["best_window"] = best_evidence
    return NBADecision(DECISION_VERSION, cif, ref, {"final_route": route, "hard_suppressed": policy["hard_suppressed"]},
                       Recommendation(treatment, channel, when, objective), SelectedRule(selected, priority, reason), tuple(trace), evidence,
                       {"synthetic_data": context["provenance"]["synthetic_data"], "synthetic_label": context["provenance"]["synthetic_label"],
                        "decision_input_stage": "TASK-005", "best_window_source_stage": "TASK-001", "rule_contract": "TASK-007A_DECISION_CONTRACT_V1"})
