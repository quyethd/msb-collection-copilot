"""Conversation context builder for the AgentBase semantic planner.

Produces a compact, explicit context rather than the entire raw chat history.
The context is bounded and never crosses user/chat/CIF boundaries.

State separation:
    BASELINE STATE      — real customer data, no simulation
    SIMULATION STATE    — hypothetical changes for the active CIF only
    KNOWLEDGE TOPIC     — last knowledge subject (e.g. ROUTING_CALL_CBS)
    WORKLIST CONTEXT    — last portfolio/worklist result (CIF list)
    ACTIVE CASE         — the currently selected CIF
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import semantics


# --------------------------------------------------------------------------- #
# Compact conversation context
# --------------------------------------------------------------------------- #

@dataclass
class ConversationContext:
    """Bounded context passed to the planner. Never raw chat history."""
    active_cif: str = ""
    last_cif: str = ""
    previous_cif: str = ""
    last_intent: str = ""
    last_goal: str = ""
    last_topic: str = ""
    last_worklist: list[str] = field(default_factory=list)
    last_decision: dict[str, Any] | None = None
    last_score: dict[str, Any] | None = None
    last_simulation: dict[str, Any] | None = None
    pending_clarification: str = ""
    conversation_summary: str = ""
    channel: str = "web"

    def to_prompt_dict(self) -> dict[str, Any]:
        """Render as a compact dict for the planner prompt. Sensitive or large
        fields are omitted or truncated."""
        result: dict[str, Any] = {
            "active_cif": self.active_cif or None,
            "last_cif": self.last_cif or None,
            "last_intent": self.last_intent or None,
            "last_topic": self.last_topic or None,
            "pending_clarification": self.pending_clarification or None,
            "channel": self.channel,
        }
        if self.previous_cif:
            result["previous_cif"] = self.previous_cif
        if self.last_worklist:
            result["last_worklist"] = self.last_worklist[:5]
        if self.last_simulation and self.last_simulation.get("cif") == self.active_cif:
            result["last_simulation"] = {
                "cif": self.last_simulation.get("cif"),
                "changes": self.last_simulation.get("changes"),
            }
        return result

    def to_prompt_text(self) -> str:
        """Render as a compact text block for the planner prompt."""
        parts: list[str] = []
        if self.active_cif:
            parts.append(f"Active CIF: {self.active_cif}")
        if self.last_cif and self.last_cif != self.active_cif:
            parts.append(f"Last CIF: {self.last_cif}")
        if self.previous_cif:
            parts.append(f"Previous CIF: {self.previous_cif}")
        if self.last_intent:
            parts.append(f"Last intent: {self.last_intent}")
        if self.last_topic:
            parts.append(f"Last knowledge topic: {self.last_topic}")
        if self.last_worklist:
            parts.append(f"Last worklist (top 5): {', '.join(self.last_worklist[:5])}")
        if self.last_simulation and self.last_simulation.get("cif") == self.active_cif:
            parts.append(f"Last simulation: CIF={self.last_simulation.get('cif')}, changes={self.last_simulation.get('changes')}")
        if self.pending_clarification:
            parts.append(f"Pending clarification: {self.pending_clarification}")
        parts.append(f"Channel: {self.channel}")
        return "; ".join(parts) if parts else "No prior context"


# --------------------------------------------------------------------------- #
# Builder
# --------------------------------------------------------------------------- #

_ALLOWED_CONTEXT_KEYS = frozenset({
    "active_cif", "last_cif", "previous_cif", "last_intent", "previous_intent",
    "last_goal", "last_topic", "previous_topic", "last_worklist",
    "last_decision", "last_score", "last_simulation", "last_simulation_context",
    "last_simulation_changes", "pending_clarification", "conversation_summary",
    "previous_user_question", "previous_path", "channel",
})


def build_context(
    raw_context: dict[str, Any] | None,
    *,
    channel: str = "web",
    active_cif_override: str | None = None,
) -> ConversationContext:
    """Build a bounded ConversationContext from raw UI/adapter state.

    Only whitelisted keys are read. String values are truncated. Cross-CIF
    simulation state is dropped if the simulation CIF does not match the
    active CIF.
    """
    raw = raw_context or {}
    ctx = ConversationContext(channel=channel)

    active_cif = active_cif_override or _str(raw, "active_cif")
    ctx.active_cif = active_cif
    ctx.last_cif = _str(raw, "last_cif") or active_cif
    ctx.previous_cif = _str(raw, "previous_cif")
    ctx.last_intent = _str(raw, "last_intent") or _str(raw, "previous_intent")
    ctx.last_goal = _str(raw, "last_goal")
    ctx.last_topic = _str(raw, "last_topic") or _str(raw, "previous_topic")
    ctx.pending_clarification = _str(raw, "pending_clarification")
    ctx.conversation_summary = _str(raw, "conversation_summary")

    worklist = raw.get("last_worklist")
    if isinstance(worklist, list):
        ctx.last_worklist = [str(c)[:20] for c in worklist if c][:10]

    decision = raw.get("last_decision")
    if isinstance(decision, dict):
        ctx.last_decision = _bounded_dict(decision)

    score = raw.get("last_score")
    if isinstance(score, dict):
        ctx.last_score = _bounded_dict(score)

    sim = raw.get("last_simulation") or raw.get("last_simulation_context")
    if isinstance(sim, dict):
        sim_cif = str(sim.get("cif") or "")
        sim_changes = sim.get("changes") or raw.get("last_simulation_changes")
        if isinstance(sim_changes, dict):
            sim_changes = _bounded_sim_changes(sim_changes)
        else:
            sim_changes = {}
        ctx.last_simulation = {"cif": sim_cif, "changes": sim_changes}

    return ctx


def _str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()[:160]
    return ""


def _bounded_dict(d: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(key, str) and len(key) <= 50:
            safe[key] = value
    return safe


def _bounded_sim_changes(changes: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for field in ("inflow_7d", "inflow_3d", "net_cashflow_30d", "ptp_state"):
        if field in changes:
            safe[field] = changes[field]
    return safe


def clear_simulation_on_cif_change(ctx: ConversationContext, new_cif: str) -> ConversationContext:
    """If the CIF is changing, clear case-local simulation state.

    Simulation state is never carried across CIFs (contract section 9).
    """
    if new_cif and ctx.last_simulation and ctx.last_simulation.get("cif") != new_cif:
        ctx.last_simulation = None
    return ctx
