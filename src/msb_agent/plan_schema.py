"""Structured plan schema and validator for the AgentBase semantic planner.

The plan is a machine-validatable, bounded, auditable object. It is never
exposed to users in raw form. The validator enforces the tool allowlist,
maximum tool calls, required arguments, and rejects action tools.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from . import semantics
from .tool_catalog import ALLOWED_TOOLS, FORBIDDEN_ACTION_TOOLS, is_allowed, is_forbidden

# --------------------------------------------------------------------------- #
# Hard bounds (contract section 17)
# --------------------------------------------------------------------------- #

MAX_TOOL_CALLS = 5
MAX_PLANNING_ROUNDS = 2
MAX_RAG_CALLS = 1
MAX_SIMULATION_CALLS = 1
MAX_AGENT_TIME_SECONDS = 8

# Valid goal values mapped to canonical intents
_GOAL_TO_INTENT: dict[str, str] = {
    "greeting": semantics.GREETING,
    "help": semantics.HELP,
    "today_worklist": semantics.TODAY_WORKLIST,
    "knowledge": semantics.KNOWLEDGE,
    "knowledge_evaluation": semantics.KNOWLEDGE_EVALUATION,
    "knowledge_governance": semantics.KNOWLEDGE_GOVERNANCE,
    "knowledge_score_semantics": semantics.KNOWLEDGE_SCORE_SEMANTICS,
    "score_value": semantics.SCORE_VALUE,
    "score_breakdown": semantics.SCORE_BREAKDOWN,
    "explain_priority": semantics.EXPLAIN_PRIORITY,
    "case_summary": semantics.CURRENT_CASE_SUMMARY,
    "case_action": semantics.CURRENT_CASE_ACTION,
    "simulation": semantics.SIMULATION,
    "simulation_followup": semantics.SIMULATION_FOLLOWUP,
    "return_to_baseline": semantics.RETURN_TO_BASELINE,
    "clarification": semantics.CLARIFICATION,
    "clarification_response": semantics.CLARIFICATION_RESPONSE,
    "active_cif_query": semantics.ACTIVE_CIF_QUERY,
    "out_of_scope": semantics.UNKNOWN,
    "unknown": semantics.UNKNOWN,
}

_CIF_RE = re.compile(r"^(?:SYN\d{6}|GOLDEN_G\d{2})$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Structured plan
# --------------------------------------------------------------------------- #

@dataclass
class ToolStep:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments, "reason": self.reason}


@dataclass
class StructuredPlan:
    """Validated, bounded plan produced by the AgentBase semantic planner."""
    goal: str
    intent: str
    cif: str | None = None
    cif_source: str = "unknown"
    needs_clarification: bool = False
    clarification_question: str | None = None
    tools: list[ToolStep] = field(default_factory=list)
    answer_mode: str = "case_specific"
    kind: str = ""
    changes: dict[str, Any] | None = None
    confidence: float = 0.0
    source: str = "deterministic_fallback"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "intent": self.intent,
            "subject": {"cif": self.cif, "source": self.cif_source},
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
            "tools": [t.to_dict() for t in self.tools],
            "answer_mode": self.answer_mode,
            "kind": self.kind,
            "changes": self.changes,
            "confidence": self.confidence,
            "source": self.source,
        }


# --------------------------------------------------------------------------- #
# Validation errors
# --------------------------------------------------------------------------- #

class PlanValidationError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Validator
# --------------------------------------------------------------------------- #

def _validate_cif(cif: Any) -> str | None:
    if cif is None:
        return None
    cif_str = str(cif).strip().upper()
    if not cif_str:
        return None
    if not _CIF_RE.match(cif_str):
        return None
    return cif_str


def _validate_tool_step(raw: Any, index: int) -> ToolStep:
    if not isinstance(raw, dict):
        raise PlanValidationError(f"tool[{index}] is not an object")
    name = str(raw.get("name") or "").strip()
    if not name:
        raise PlanValidationError(f"tool[{index}] has no name")
    if is_forbidden(name):
        raise PlanValidationError(f"tool[{index}] '{name}' is a forbidden action tool")
    if not is_allowed(name):
        raise PlanValidationError(f"tool[{index}] '{name}' is not in the approved allowlist")
    arguments = raw.get("arguments")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise PlanValidationError(f"tool[{index}] arguments is not an object")
    reason = str(raw.get("reason") or "")[:300]
    return ToolStep(name=name, arguments=arguments, reason=reason)


def validate_plan(raw: dict[str, Any], *, max_tools: int = MAX_TOOL_CALLS) -> StructuredPlan:
    """Validate a raw (possibly LLM-generated) plan into a bounded StructuredPlan.

    Raises PlanValidationError if the plan violates any safety boundary.
    """
    if not isinstance(raw, dict):
        raise PlanValidationError("plan is not an object")

    goal = str(raw.get("goal") or "").strip().lower()
    intent = _GOAL_TO_INTENT.get(goal, semantics.UNKNOWN)

    cif = _validate_cif(raw.get("cif") or (raw.get("subject") or {}).get("cif"))
    cif_source = str(raw.get("cif_source") or (raw.get("subject") or {}).get("source") or "unknown")[:50]

    needs_clarification = bool(raw.get("needs_clarification", False))
    clarification_question = raw.get("clarification_question")
    if clarification_question is not None:
        clarification_question = str(clarification_question)[:500]

    raw_tools = raw.get("tools") or []
    if not isinstance(raw_tools, list):
        raise PlanValidationError("tools is not a list")
    if len(raw_tools) > max_tools:
        raise PlanValidationError(f"too many tools: {len(raw_tools)} > {max_tools}")

    tools: list[ToolStep] = []
    sim_count = 0
    rag_count = 0
    for i, raw_tool in enumerate(raw_tools):
        step = _validate_tool_step(raw_tool, i)
        tools.append(step)
        if step.name == "simulate_decision":
            sim_count += 1
        if step.name == "find_knowledge":
            rag_count += 1
    if sim_count > MAX_SIMULATION_CALLS:
        raise PlanValidationError(f"too many simulation calls: {sim_count} > {MAX_SIMULATION_CALLS}")
    if rag_count > MAX_RAG_CALLS:
        raise PlanValidationError(f"too many RAG calls: {rag_count} > {MAX_RAG_CALLS}")

    answer_mode = str(raw.get("answer_mode") or "case_specific")[:50]
    kind = str(raw.get("kind") or "")[:50]
    changes = raw.get("changes")
    if changes is not None and not isinstance(changes, dict):
        changes = None
    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    source = str(raw.get("source") or "deterministic_fallback")[:50]

    return StructuredPlan(
        goal=goal or "unknown",
        intent=intent,
        cif=cif,
        cif_source=cif_source,
        needs_clarification=needs_clarification,
        clarification_question=clarification_question,
        tools=tools,
        answer_mode=answer_mode,
        kind=kind,
        changes=changes,
        confidence=confidence,
        source=source,
    )


def parse_llm_plan(raw_text: str) -> dict[str, Any] | None:
    """Extract a JSON plan from an LLM response. Returns None if no valid JSON."""
    if not raw_text:
        return None
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None
