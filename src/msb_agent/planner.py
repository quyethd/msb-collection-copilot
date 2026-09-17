"""AgentBase semantic conversation planner.

This is the PRIMARY semantic path (TASK-018). The planner understands natural
Vietnamese conversation, decides what the user means, which tools are needed,
whether clarification is necessary, and how to combine results.

Responsibility split:
    Planner OWNS:     intent, context sufficiency, tool selection, clarification,
                      reference resolution, multi-intent decomposition.
    Planner does NOT: route, score, treatment, channel, policy, business actions.

Architecture:
    1. Deterministic safety guards (always run — security, CIF, greeting/help)
    2. AgentBase LLM semantic planner (when feature flag on + LLM available)
    3. Deterministic fallback (semantics.resolve — Level 2)

The deterministic fallback is the survivable path when LLM is unavailable.
It is NOT deleted; it is the Level 2 degradation in the fallback hierarchy.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from . import semantics
from .context_builder import ConversationContext, build_context, clear_simulation_on_cif_change
from .plan_schema import (
    StructuredPlan, ToolStep, PlanValidationError,
    validate_plan, parse_llm_plan,
    MAX_TOOL_CALLS, MAX_PLANNING_ROUNDS, MAX_AGENT_TIME_SECONDS,
)
from .tool_catalog import catalog_for_prompt, is_allowed
from .llm import LLMClient, maas_client_from_env


# --------------------------------------------------------------------------- #
# Feature flag
# --------------------------------------------------------------------------- #

def agent_first_enabled() -> bool:
    """Runtime feature flag for Agent-first conversation orchestration.

    Defaults to false. When false, the deterministic resolver is the primary
    path. When true and LLM is available, AgentBase is the primary semantic
    planner with deterministic fallback as Level 2.
    """
    return os.environ.get("AGENT_FIRST_CONVERSATION_ENABLED", "").lower() in ("true", "1", "yes", "on")


# --------------------------------------------------------------------------- #
# Deterministic safety guards (always run, never removed)
# --------------------------------------------------------------------------- #

_SECURITY_MARKERS = (
    "api_key", "api key", "llm_api_key", "client_secret", "client secret",
    ".env", "password", "mat khau", "credentials", "credential",
    "reasoning_content", "private prompt", "internal endpoint",
    "system prompt", "secret", "llm api key",
)

_GREETING_EXACT = frozenset({"alo", "chao", "hello", "hi", "xin chao", "yo", "hey", "e"})
_HELP_MARKERS = ("tro giup", "giup gi", "giup duoc gi", "ban lam gi", "ban giup", "can giup", "huong dan", "ban lam duoc gi", "ban co the giup")


def _plain(value: str) -> str:
    return semantics.normalize(value)


def _security_guard(message: str, norm: str) -> StructuredPlan | None:
    """Block security-sensitive requests before any semantic processing."""
    raw_lower = (message or "").lower()
    if any(marker in raw_lower or marker in norm for marker in _SECURITY_MARKERS):
        return StructuredPlan(
            goal="out_of_scope",
            intent=semantics.UNKNOWN,
            confidence=1.0,
            source="security_guard",
            answer_mode="global",
        )
    return None


def _greeting_help_guard(message: str, norm: str) -> StructuredPlan | None:
    """Fast path for exact greeting and explicit help (contract section 5)."""
    if norm in _GREETING_EXACT or any(norm.startswith(p) for p in ("xin chao", "chao ban", "chao em", "chao chi", "chao anh", "hello", "hi ", "alo ", "yo ", "hey ")):
        return StructuredPlan(
            goal="greeting",
            intent=semantics.GREETING,
            confidence=1.0,
            source="deterministic_fast_path",
            answer_mode="global",
        )
    if any(marker in norm for marker in _HELP_MARKERS):
        return StructuredPlan(
            goal="help",
            intent=semantics.HELP,
            confidence=1.0,
            source="deterministic_fast_path",
            answer_mode="global",
        )
    return None


def _empty_guard(norm: str) -> StructuredPlan | None:
    if not norm:
        return StructuredPlan(
            goal="unknown",
            intent=semantics.UNKNOWN,
            confidence=1.0,
            source="empty_guard",
            needs_clarification=True,
            answer_mode="global",
        )
    return None


# --------------------------------------------------------------------------- #
# Deterministic fallback (Level 2) — wraps semantics.resolve
# --------------------------------------------------------------------------- #

def _deterministic_fallback(message: str, ctx: ConversationContext) -> StructuredPlan:
    """Map the shared deterministic resolver to a StructuredPlan.

    This is the Level 2 fallback path. It is the survivable path when the LLM
    is unavailable or the feature flag is off. It uses the existing
    ``semantics.resolve`` which has been validated by TASK-017.
    """
    state = semantics.ConversationState(
        active_cif=ctx.active_cif,
        last_intent=ctx.last_intent,
        last_topic=ctx.last_topic,
        last_cif=ctx.last_cif,
        pending_clarification=ctx.pending_clarification,
        last_simulation_context=ctx.last_simulation,
        previous_intent=ctx.last_intent,
        previous_user_question=ctx.conversation_summary,
    )
    resolved = semantics.resolve(message, state)
    cif = resolved.cif
    cif_source = "explicit" if semantics.extract_cif(message) else ("active_context" if cif == ctx.active_cif else "last_context")
    return StructuredPlan(
        goal=_intent_to_goal(resolved.intent),
        intent=resolved.intent,
        cif=cif,
        cif_source=cif_source,
        needs_clarification=resolved.needs_clarification,
        kind=resolved.kind,
        changes=resolved.changes,
        confidence=resolved.confidence,
        source="deterministic_fallback",
        answer_mode="global" if resolved.is_global else "case_specific",
    )


_GOAL_BY_INTENT: dict[str, str] = {
    semantics.GREETING: "greeting",
    semantics.HELP: "help",
    semantics.TODAY_WORKLIST: "today_worklist",
    semantics.KNOWLEDGE: "knowledge",
    semantics.KNOWLEDGE_EVALUATION: "knowledge_evaluation",
    semantics.KNOWLEDGE_GOVERNANCE: "knowledge_governance",
    semantics.KNOWLEDGE_SCORE_SEMANTICS: "knowledge_score_semantics",
    semantics.SCORE_VALUE: "score_value",
    semantics.SCORE_BREAKDOWN: "score_breakdown",
    semantics.EXPLAIN_PRIORITY: "explain_priority",
    semantics.CURRENT_CASE_SUMMARY: "case_summary",
    semantics.CURRENT_CASE_ACTION: "case_action",
    semantics.SIMULATION: "simulation",
    semantics.SIMULATION_FOLLOWUP: "simulation_followup",
    semantics.RETURN_TO_BASELINE: "return_to_baseline",
    semantics.CLARIFICATION: "clarification",
    semantics.CLARIFICATION_RESPONSE: "clarification_response",
    semantics.ACTIVE_CIF_QUERY: "active_cif_query",
    semantics.UNKNOWN: "unknown",
}


def _intent_to_goal(intent: str) -> str:
    return _GOAL_BY_INTENT.get(intent, "unknown")


# --------------------------------------------------------------------------- #
# AgentBase LLM planner (Level 1 — primary semantic path)
# --------------------------------------------------------------------------- #

_PLANNER_SYSTEM_PROMPT = """\
Bạn là bộ lập kế hoạch hội thoại ngữ nghĩa (semantic planner) cho trợ lý thu hồi nợ MSB.
Nhiệm vụ của bạn: hiểu ý người dùng, chọn công cụ phù hợp, giữ ngữ cảnh hội thoại.

QUYỀN HẠN:
- Bạn CHỈ được hiểu ý và chọn công cụ. KHÔNG được quyết định route, score, treatment, channel.
- Bạn KHÔNG được bịa dữ liệu nghiệp vụ. Mọi câu trả lời phải dựa trên kết quả công cụ.
- Bạn KHÔNG được tạo công cụ action/write (send_zalo, make_call, change_route, v.v.).

CÔNG CỤ ĐƯỢC PHÉP:
{tool_catalog}

INTENT HỢP LỆ (chỉ trả về một trong các giá trị này):
greeting, help, today_worklist, knowledge, knowledge_evaluation,
score_value, score_breakdown, explain_priority, case_summary, case_action,
simulation, simulation_followup, return_to_baseline, clarification,
clarification_response, active_cif_query, out_of_scope, unknown

QUY TẮC:
1. Nếu người dùng nhắc CIF cụ thể (SYNxxxxxx), dùng CIF đó.
2. Nếu người dùng nói "nó", "khách này", "điểm nó" và có active_cif, dùng active_cif.
3. Nếu người dùng nói "khách đầu tiên", "khách thứ 2" và có last_worklist, dùng CIF từ worklist.
4. Nếu câu hỏi có nhiều ý (multi-intent), chọn công cụ cho ý chính; ghi rõ trong reason.
5. Nếu thiếu CIF và câu hỏi cần CIF, đặt needs_clarification=true.
6. Nếu câu hỏi về kiến thức chung (CALL, CBS, quy trình), KHÔNG dùng CIF.
7. "khách không trả nợ thì sao" → clarification (phân biệt mô phỏng vs quy trình).
8. "quay lại dữ liệu thật" → return_to_baseline.
9. Không over-clarify. Chỉ clarify khi thật sự mơ hồ.

Trả về JSON duy nhất dạng:
{{
  "goal": "<intent>",
  "cif": "<SYNxxxxxx hoặc null>",
  "cif_source": "explicit|active_context|worklist|last_context|null",
  "needs_clarification": true/false,
  "clarification_question": "<câu hỏi hoặc null>",
  "tools": [
    {{"name": "<tool_name>", "arguments": {{...}}, "reason": "<ly do chon>"}}
  ],
  "answer_mode": "case_specific|global|knowledge",
  "kind": "<call|cbs|comparison|empty string>",
  "changes": {{"inflow_7d": 0}} hoặc null,
  "confidence": 0.0-1.0
}}
"""


def _build_planner_prompt(message: str, ctx: ConversationContext) -> str:
    tool_text = catalog_for_prompt()
    context_text = ctx.to_prompt_text()
    system = _PLANNER_SYSTEM_PROMPT.format(tool_catalog=tool_text)
    return (
        system
        + f"\n\nNGỮ CẢNH HIỆN TẠI:\n{context_text}\n\n"
        + f"CÂU HỎI CỦA NGƯỜI DÙNG:\n{message[:500]}\n\n"
        + "Trả về JSON:"
    )


def _llm_plan(
    message: str, ctx: ConversationContext, llm: LLMClient,
) -> StructuredPlan | None:
    """Call the AgentBase LLM to produce a structured plan.

    Returns None if the LLM call fails or the plan is invalid. The caller
    then falls back to the deterministic resolver.
    """
    prompt = _build_planner_prompt(message, ctx)
    try:
        raw_text, _model = llm.complete(prompt, max_tokens=400, temperature=0)
    except Exception:
        return None
    if not raw_text:
        return None
    parsed = parse_llm_plan(raw_text)
    if parsed is None:
        return None
    parsed["source"] = "agentbase_llm"
    try:
        plan = validate_plan(parsed)
    except PlanValidationError:
        return None
    if plan.cif is None and ctx.active_cif:
        explicit_cif = semantics.extract_cif(message)
        if explicit_cif:
            plan.cif = explicit_cif
            plan.cif_source = "explicit"
    return plan


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def plan_conversation(
    message: str,
    raw_context: dict[str, Any] | None = None,
    *,
    channel: str = "web",
    active_cif_override: str | None = None,
    llm_client: LLMClient | None = None,
) -> StructuredPlan:
    """Produce a validated StructuredPlan for the user message.

    This is the single entry point for Agent-first conversation orchestration.
    Both Web and Zalo adapters call this function, ensuring semantic parity.

    Flow:
        1. Build bounded context (never raw history, never cross-CIF)
        2. Deterministic safety guards (security, empty, greeting/help)
        3. If feature flag on + LLM available: AgentBase LLM planner
        4. Deterministic fallback (semantics.resolve — Level 2)
    """
    started = time.perf_counter()
    message = (message or "").strip()
    norm = _plain(message)
    ctx = build_context(raw_context, channel=channel, active_cif_override=active_cif_override)

    # 1. Empty guard
    plan = _empty_guard(norm)
    if plan:
        return plan

    # 2. Security guard (always first after empty)
    plan = _security_guard(message, norm)
    if plan:
        return plan

    # 3. Greeting/help fast path (contract section 5 — optional simple fast paths)
    plan = _greeting_help_guard(message, norm)
    if plan:
        return plan

    # 4. AgentBase LLM planner (Level 1 — primary semantic path)
    if agent_first_enabled():
        llm = llm_client
        if llm is None:
            llm = maas_client_from_env(timeout_seconds=MAX_AGENT_TIME_SECONDS)
        if llm is not None and (time.perf_counter() - started) < MAX_AGENT_TIME_SECONDS:
            llm_plan = _llm_plan(message, ctx, llm)
            if llm_plan is not None:
                if llm_plan.cif and llm_plan.cif != ctx.active_cif:
                    clear_simulation_on_cif_change(ctx, llm_plan.cif)
                return llm_plan

    # 5. Deterministic fallback (Level 2)
    return _deterministic_fallback(message, ctx)


def plan_for_shadow(
    message: str,
    raw_context: dict[str, Any] | None = None,
    *,
    channel: str = "web",
    active_cif_override: str | None = None,
) -> tuple[StructuredPlan, StructuredPlan]:
    """Produce both the deterministic plan and the AgentBase plan for shadow
    comparison. Used by the shadow comparison harness to verify parity.

    Returns (deterministic_plan, agentbase_plan).
    """
    message = (message or "").strip()
    norm = _plain(message)
    ctx = build_context(raw_context, channel=channel, active_cif_override=active_cif_override)

    deterministic = _deterministic_fallback(message, ctx)

    plan = _empty_guard(norm)
    if plan is None:
        plan = _security_guard(message, norm)
    if plan is None:
        plan = _greeting_help_guard(message, norm)
    if plan is None:
        if agent_first_enabled():
            llm = maas_client_from_env(timeout_seconds=MAX_AGENT_TIME_SECONDS)
            if llm is not None:
                plan = _llm_plan(message, ctx, llm)
    if plan is None:
        plan = deterministic

    return deterministic, plan
