from __future__ import annotations

from typing import Any, Callable, Sequence

from .llm import LLMClient
from .models import (AGENT_VERSION, CANONICAL_MODEL, SIMULATE_RESULT, AgentResponse, decision_from_nba)

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]
_MODE_LABELS = {"PLAN": "Plan", "INVESTIGATE": "Investigate", "EXPLAIN": "Explain", "SIMULATE": "Simulate"}
_OVERRIDE_NOTICE = " The agent cannot override accepted collection policy."

def _tool_ok(envelope: dict[str, Any]) -> bool:
    return bool(envelope.get("ok"))


def _tool_data(envelope: dict[str, Any]) -> dict[str, Any]:
    return envelope.get("data") or {}


def _call(tool_caller: ToolCaller, name: str, cif: str) -> dict[str, Any]:
    return tool_caller(name, {"cif": cif})


def _evidence_from_nba(nba: dict[str, Any]) -> list[dict[str, Any]]:
    facts = nba.get("evidence_refs", {}).get("selected_rule_facts", {})
    items: list[dict[str, Any]] = []
    label_map = {
        "max_dpd_cif": "DPD", "net_cashflow_30d": "net_cashflow_30d",
        "inflow_7d": "inflow_7d", "inflow_3d": "inflow_3d",
        "ptp_state": "PTP state", "final_route": "final_route",
        "hard_suppressed": "hard_suppressed", "cashflow_available": "cashflow_available",
        "latest_business_outcome": "latest_business_outcome",
        "source_next_action_date": "source_next_action_date", "promise_date": "promise_date",
    }
    for key, label in label_map.items():
        if key in facts:
            items.append({"factor": label, "value": facts[key], "source": "get_next_best_action"})
    best_window = nba.get("evidence_refs", {}).get("best_window")
    if best_window:
        items.append({"factor": "best_window", "value": best_window.get("windows", {}), "source": "get_next_best_action"})
    return items


def _evidence_from_context(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    debt = ctx.get("debt", {})
    items.append({"factor": "DPD", "value": debt.get("max_dpd_cif"), "source": "get_customer_360"})
    items.append({"factor": "total_outstanding", "value": debt.get("total_outstanding_cif"), "source": "get_customer_360"})
    items.append({"factor": "loan_count", "value": debt.get("loan_count"), "source": "get_customer_360"})
    cash = ctx.get("cashflow", {})
    items.append({"factor": "inflow_3d", "value": cash.get("inflow_3d"), "source": "get_customer_360"})
    items.append({"factor": "inflow_7d", "value": cash.get("inflow_7d"), "source": "get_customer_360"})
    items.append({"factor": "net_cashflow_30d", "value": cash.get("net_cashflow_30d"), "source": "get_customer_360"})
    ptp = ctx.get("ptp", {})
    items.append({"factor": "PTP_status", "value": ptp.get("status"), "source": "get_customer_360"})
    items.append({"factor": "PTP_promise_date", "value": ptp.get("promise_date"), "source": "get_customer_360"})
    policy = ctx.get("policy", {})
    items.append({"factor": "final_route", "value": policy.get("final_route"), "source": "get_customer_360"})
    items.append({"factor": "hard_suppressed", "value": policy.get("hard_suppressed"), "source": "get_customer_360"})
    recovery = ctx.get("recovery_opportunity", {})
    items.append({"factor": "recovery_opportunity_score", "value": recovery.get("recovery_opportunity_score"), "source": "get_customer_360"})
    contact = ctx.get("contact", {})
    items.append({"factor": "outbound_attempts_30d", "value": contact.get("outbound_attempts_30d"), "source": "get_customer_360"})
    items.append({"factor": "successful_outbound_calls_30d", "value": contact.get("successful_outbound_calls_30d"), "source": "get_customer_360"})
    return items


def _when_label(when: dict[str, Any]) -> str:
    wtype = when.get("type", "NONE")
    if wtype == "NONE":
        return "No immediate action timing required"
    if wtype == "BEST_WINDOW":
        return f"Best contact window {when.get('window')} on {when.get('date')}"
    if wtype == "SOURCE_DATETIME":
        return f"Source datetime {when.get('datetime')}"
    if wtype == "SOURCE_DATE":
        return f"Source date {when.get('date')}"
    if wtype == "TODAY":
        return f"Today ({when.get('date')})"
    return wtype


def _plan_summary(nba: dict[str, Any], llm: LLMClient | None) -> tuple[str, str | None]:
    decision = decision_from_nba(nba)
    template = (
        f"WHO: {nba['cif']}\n"
        f"WHY: {nba['rule_id']} ({nba['reason_code']})\n"
        f"WHAT: {decision['treatment']}\n"
        f"WHEN: {_when_label(decision['when'])}\n"
        f"HOW: {decision['channel']}\n"
        f"EXPECTED OUTCOME: {decision['objective']}")
    if llm is None:
        return template, None
    prompt = (
        "You are a collection decision assistant. Summarize the following deterministic collection plan "
        "in one or two short sentences. Do NOT change, override, or recommend any different treatment, "
        "channel, objective, timing, or routing. The decision is final and deterministic.\n"
        + template)
    content, model = llm.complete(prompt, max_tokens=150, temperature=0)
    return content or template, model


def _explain_summary(nba: dict[str, Any], llm: LLMClient | None) -> tuple[str, str | None]:
    decision = decision_from_nba(nba)
    facts = nba.get("evidence_refs", {}).get("selected_rule_facts", {})
    fact_lines = [f"  {k}: {v}" for k, v in sorted(facts.items())]
    template = (
        f"DETERMINISTIC DECISION:\n"
        f"  treatment: {decision['treatment']}\n"
        f"  channel: {decision['channel']}\n"
        f"  objective: {decision['objective']}\n"
        f"  when: {decision['when']}\n"
        f"Reason:\n"
        f"  rule_id: {nba['rule_id']}\n"
        f"  reason_code: {nba['reason_code']}\n"
        f"Evidence:\n" + "\n".join(fact_lines))
    if llm is None:
        return template + "\n\nThis is a DETERMINISTIC DECISION from the TASK-007A engine, not an AI explanation.", None
    prompt = (
        "You are a collection decision assistant. Explain WHY the deterministic engine selected the "
        "following decision. Ground your explanation ONLY in the provided rule, reason, and evidence. "
        "Do NOT invent new reasons. Do NOT change any decision values. Clearly distinguish the "
        "DETERMINISTIC DECISION from your AI EXPLANATION.\n" + template)
    content, model = llm.complete(prompt, max_tokens=200, temperature=0)
    return (content or template) + "\n\nAI EXPLANATION: The decision above is deterministic from the TASK-007A engine.", model


def _investigate_summary(cif: str, evidence: list[dict[str, Any]], llm: LLMClient | None) -> tuple[str, str | None]:
    lines = [f"{item['factor']}: {item['value']}" for item in evidence]
    template = f"Customer {cif} evidence:\n" + "\n".join(lines)
    if llm is None:
        return template, None
    prompt = (
        "You are a collection decision assistant. Summarize the following customer evidence in one or "
        "two short sentences. Do NOT fabricate fields not present. Do NOT recommend any action.\n"
        + template)
    content, model = llm.complete(prompt, max_tokens=150, temperature=0)
    return content or template, model


class AgentRuntime:
    def __init__(self, tool_caller: ToolCaller, llm_client: LLMClient | None = None):
        self.tool_caller = tool_caller
        self.llm_client = llm_client

    def invoke(self, mode: str, cif: str | None, message: str | None = None,
               changes: dict[str, Any] | None = None) -> AgentResponse:
        if mode not in ("PLAN", "INVESTIGATE", "EXPLAIN", "SIMULATE"):
            return AgentResponse("error", "PLAN", cif, None, [], "Unknown mode", [], None, True, AGENT_VERSION,
                                 {"code": "INVALID_ARGUMENT", "message": f"Unknown mode: {mode}"})
        if mode == "SIMULATE":
            return self._simulate(cif, changes or {})
        if not cif:
            return AgentResponse("error", mode, None, None, [], "No CIF provided", [], None, True, AGENT_VERSION,
                                 {"code": "INVALID_ARGUMENT", "message": "A synthetic CIF is required"})
        nba_envelope = self.tool_caller("get_next_best_action", {"cif": cif})
        if not _tool_ok(nba_envelope):
            code = nba_envelope.get("error", {}).get("code", "INTERNAL_ERROR")
            return AgentResponse("error", mode, cif, None, [],
                                 f"CIF {cif} was not found; no fabricated customer data.", ["get_next_best_action"],
                                 None, True, AGENT_VERSION, {"code": code, "message": f"CIF {cif!r} was not found"})
        if mode == "PLAN":
            return self._plan(cif, nba_envelope)
        if mode == "EXPLAIN":
            return self._explain(cif, nba_envelope)
        if mode == "INVESTIGATE":
            return self._investigate(cif, nba_envelope)
        return AgentResponse("error", mode, cif, None, [], "Unreachable", [], None, True, AGENT_VERSION,
                             {"code": "INTERNAL_ERROR", "message": "Unreachable"})

    def _plan(self, cif: str, nba_envelope: dict[str, Any]) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        ctx_envelope = _call(self.tool_caller, "get_customer_360", cif)
        ctx = _tool_data(ctx_envelope) if _tool_ok(ctx_envelope) else {}
        evidence = _evidence_from_nba(nba)
        summary, model = _plan_summary(nba, self.llm_client)
        return AgentResponse("success", "PLAN", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action", "get_customer_360"], model, True, AGENT_VERSION)

    def _explain(self, cif: str, nba_envelope: dict[str, Any]) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        evidence = _evidence_from_nba(nba)
        summary, model = _explain_summary(nba, self.llm_client)
        return AgentResponse("success", "EXPLAIN", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action"], model, True, AGENT_VERSION)

    def _investigate(self, cif: str, nba_envelope: dict[str, Any]) -> AgentResponse:
        nba = _tool_data(nba_envelope)
        ctx_envelope = _call(self.tool_caller, "get_customer_360", cif)
        ctx = _tool_data(ctx_envelope) if _tool_ok(ctx_envelope) else {}
        evidence = _evidence_from_context(ctx) if ctx else _evidence_from_nba(nba)
        evidence.append({"factor": "NBA_rule_id", "value": nba["rule_id"], "source": "get_next_best_action"})
        evidence.append({"factor": "NBA_treatment", "value": nba["treatment"], "source": "get_next_best_action"})
        summary, model = _investigate_summary(cif, evidence, self.llm_client)
        return AgentResponse("success", "INVESTIGATE", cif, decision_from_nba(nba), evidence, summary,
                             ["get_next_best_action", "get_customer_360"], model, True, AGENT_VERSION)

    def _simulate(self, cif: str | None, changes: dict[str, Any]) -> AgentResponse:
        if not cif:
            return AgentResponse("error", "SIMULATE", cif, None, [], "No CIF provided for simulation.",
                                 [], None, True, AGENT_VERSION,
                                 {"code": "INVALID_ARGUMENT", "message": "A synthetic CIF is required for simulation"})
        sim_envelope = self.tool_caller("simulate_decision", {"cif": cif, "changes": changes})
        if not _tool_ok(sim_envelope):
            error = sim_envelope.get("error", {})
            return AgentResponse("error", "SIMULATE", cif, None, [],
                                 f"Simulation failed: {error.get('message', 'unknown error')}",
                                 ["simulate_decision"], None, True, AGENT_VERSION,
                                 {"code": error.get("code", "INTERNAL_ERROR"),
                                  "message": error.get("message", "Simulation failed")})
        sim_data = _tool_data(sim_envelope)
        diff = sim_data.get("diff", [])
        after_decision = sim_data.get("after", {})
        summary, model = self._simulate_summary(sim_data, self.llm_client)
        return AgentResponse("success", "SIMULATE", cif, after_decision, diff, summary,
                             ["simulate_decision"], model, True, AGENT_VERSION,
                             simulation=sim_data)

    def _simulate_summary(self, sim_data: dict[str, Any], llm: LLMClient | None) -> tuple[str, str | None]:
        before = sim_data.get("before", {})
        after = sim_data.get("after", {})
        changed = sim_data.get("decision_changed", False)
        diff_fields = [entry.get("field", "") for entry in sim_data.get("diff", [])]
        template = (
            f"SIMULATION RESULT (deterministic):\n"
            f"  Before: {before.get('treatment', '?')} ({before.get('rule_id', '?')})\n"
            f"  After: {after.get('treatment', '?')} ({after.get('rule_id', '?')})\n"
            f"  Decision changed: {changed}\n"
            f"  Changed fields: {diff_fields}\n"
            f"The simulation result is deterministic from the TASK-008 engine.")
        if llm is None:
            return template, None
        prompt = (
            "You are a Vietnamese collection decision assistant. Explain the following simulation result "
            "in business-friendly Vietnamese. Do NOT change any decision values. Do NOT calculate new "
            "decisions. Only explain what changed and why, in Vietnamese.\n" + template)
        content, model = llm.complete(prompt, max_tokens=250, temperature=0)
        return content or template, model
