"""Approved read/compute tool catalog for the AgentBase semantic planner.

Each entry defines the contract that the planner uses to select tools. The
catalog is the single source of truth for the tool allowlist. Action/write
tools are deliberately absent and must never be added here.

This module is metadata only. Tool implementations live in ``msb_tools`` and
are not modified.
"""
from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------- #
# Tool allowlist (read/compute only)
# --------------------------------------------------------------------------- #

ALLOWED_TOOLS: frozenset[str] = frozenset({
    "get_portfolio",
    "get_customer_360",
    "get_next_best_action",
    "get_recovery_opportunity",
    "get_cashflow_intelligence",
    "get_collection_history",
    "get_collection_policy",
    "simulate_decision",
    "find_knowledge",
})

# Tools that are explicitly forbidden (action/write). This list is checked at
# validation time so that a model-generated plan can never surface them.
FORBIDDEN_ACTION_TOOLS: frozenset[str] = frozenset({
    "send_zalo", "send_sms", "send_email", "make_call",
    "change_route", "change_score", "change_treatment",
    "create_ptp", "update_ptp", "update_customer",
})

# --------------------------------------------------------------------------- #
# Tool descriptions — the Agent contract
# --------------------------------------------------------------------------- #

TOOL_CATALOG: dict[str, dict[str, Any]] = {
    "get_portfolio": {
        "name": "get_portfolio",
        "purpose": "List all cases in the collection portfolio with their recovery opportunity scores and routes.",
        "when_to_use": [
            "User asks what to do today / what is the priority list / what cases need attention.",
            "User asks 'khách đầu tiên' / 'khách thứ 2' and no worklist has been shown yet.",
            "Assistant needs the full case list before selecting a specific case.",
        ],
        "when_not_to_use": [
            "User already asks about a specific CIF — use get_customer_360 or get_next_best_action instead.",
            "User asks about score breakdown — use get_recovery_opportunity.",
            "User asks a knowledge question — use find_knowledge.",
        ],
        "authority": "read_only",
        "required_args": [],
        "optional_args": {},
        "output_semantics": "List of cases with cif, recovery_opportunity_score, final_route, and basic debt info.",
        "timeout_seconds": 3,
        "fallback": "Return empty list; assistant explains no data available.",
    },
    "get_customer_360": {
        "name": "get_customer_360",
        "purpose": "Full 360-degree view of a single customer: debt, cashflow, PTP, policy, contact history.",
        "when_to_use": [
            "User requests a general overview / summary of a specific customer.",
            "Assistant needs basic context before another case-specific tool.",
            "User says 'tóm tắt', 'tình trạng', 'thông tin khách' with a CIF.",
        ],
        "when_not_to_use": [
            "User explicitly asks about score — use get_recovery_opportunity.",
            "User explicitly asks about score breakdown — use get_recovery_opportunity.",
            "User explicitly asks about current decision/NBA — use get_next_best_action.",
            "User explicitly asks about PTP — the 360 includes it but a focused answer is better.",
            "User explicitly asks about cashflow — use get_cashflow_intelligence.",
            "User explicitly asks about simulation — use simulate_decision.",
            "User asks about today's worklist — use get_portfolio.",
        ],
        "authority": "read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "Dict with debt, cashflow, ptp, policy, recovery_opportunity, contact sub-objects.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant asks for a valid CIF.",
    },
    "get_next_best_action": {
        "name": "get_next_best_action",
        "purpose": "Deterministic next-best-action for a CIF: route, treatment, channel, when, reason.",
        "when_to_use": [
            "User asks 'tại sao chưa gọi', 'sao lại chờ', 'quyết định hiện tại', 'nên làm gì'.",
            "User asks about the current decision/action for a case.",
            "Assistant needs the authoritative decision to explain or compare.",
        ],
        "when_not_to_use": [
            "User asks about score calculation — use get_recovery_opportunity.",
            "User asks a knowledge/policy question — use find_knowledge.",
            "User asks about a hypothetical — use simulate_decision.",
        ],
        "authority": "decision_core_read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "Dict with final_route, treatment, channel, when, reason_code, rule_id, recovery_opportunity_score, evidence_refs.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant explains no decision found for this CIF.",
    },
    "get_recovery_opportunity": {
        "name": "get_recovery_opportunity",
        "purpose": "Recovery opportunity score (0-100) and its component breakdown for a CIF.",
        "when_to_use": [
            "User asks how the score is calculated / why score is high or low.",
            "User asks about one score component.",
            "User refers to 'điểm này', 'điểm của khách', 'sao lại 69', 'cách tính điểm'.",
            "User asks 'điểm bao nhiêu' for a specific CIF.",
        ],
        "when_not_to_use": [
            "User asks about the current action/decision — use get_next_best_action.",
            "User asks a knowledge question — use find_knowledge.",
            "User asks about today's worklist — use get_portfolio.",
        ],
        "authority": "scoring_core_read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "Dict with recovery_opportunity_score (int 0-100) and component_breakdown list.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant explains no score data for this CIF.",
    },
    "get_cashflow_intelligence": {
        "name": "get_cashflow_intelligence",
        "purpose": "Cashflow summary: inflow 3d/7d, net cashflow 30d, and trend signals for a CIF.",
        "when_to_use": [
            "User asks about 'dòng tiền', 'tiền vào', 'tiền về', 'cashflow'.",
            "User asks 'tuần này không có tiền vào' as a factual question (not hypothetical).",
        ],
        "when_not_to_use": [
            "User asks about a hypothetical cashflow change — use simulate_decision.",
            "User asks about score — use get_recovery_opportunity.",
            "User asks about the decision — use get_next_best_action.",
        ],
        "authority": "read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "Dict with inflow_3d, inflow_7d, net_cashflow_30d, and trend indicators.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant explains no cashflow data for this CIF.",
    },
    "get_collection_history": {
        "name": "get_collection_history",
        "purpose": "Contact/interaction history for a CIF: outbound attempts, results, dates.",
        "when_to_use": [
            "User asks about 'lịch sử liên hệ', 'đã gọi bao nhiêu lần', 'kết quả tương tác'.",
        ],
        "when_not_to_use": [
            "User asks about the current decision — use get_next_best_action.",
            "User asks about score — use get_recovery_opportunity.",
        ],
        "authority": "read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "List of interaction records with date, channel, outcome.",
        "timeout_seconds": 3,
        "fallback": "Return empty list; assistant explains no contact history.",
    },
    "get_collection_policy": {
        "name": "get_collection_policy",
        "purpose": "Collection policy metadata for a CIF: route assignment, hard suppression flags.",
        "when_to_use": [
            "User asks about 'tuyến', 'route', 'tại sao thuộc tuyến CALL/CBS'.",
            "Assistant needs to explain why a case is on a specific route.",
        ],
        "when_not_to_use": [
            "User asks about the action/treatment — use get_next_best_action.",
            "User asks a general knowledge question about CALL/CBS — use find_knowledge.",
        ],
        "authority": "read_only",
        "required_args": ["cif"],
        "optional_args": {},
        "output_semantics": "Dict with final_route, hard_suppressed, and policy metadata.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant explains no policy data for this CIF.",
    },
    "simulate_decision": {
        "name": "simulate_decision",
        "purpose": "Hypothetical decision recomputation: apply changes to a CIF and compare before/after.",
        "when_to_use": [
            "User asks 'nếu...thì sao', 'giả sử', 'mô phỏng', 'what if'.",
            "User asks about a hypothetical cashflow or PTP state change.",
            "User asks 'thế giờ làm gì' after a simulation was shown.",
        ],
        "when_not_to_use": [
            "User asks about the current (real) decision — use get_next_best_action.",
            "User asks a knowledge question — use find_knowledge.",
            "No CIF is identified and none can be inferred — ask clarification.",
        ],
        "authority": "simulation_core_read_only",
        "required_args": ["cif"],
        "optional_args": {"changes": "dict of hypothetical field changes (inflow_7d, ptp_state, etc.)"},
        "output_semantics": "Dict with before, after, diff, decision_changed flag. Never mutates real data.",
        "timeout_seconds": 3,
        "fallback": "Return error; assistant explains simulation is not available for this case.",
    },
    "find_knowledge": {
        "name": "find_knowledge",
        "purpose": "Project/domain knowledge retrieval: CALL/CBS definitions, policies, processes, evaluation criteria.",
        "when_to_use": [
            "User asks '... là gì', '... khác nhau thế nào', '... dùng để làm gì'.",
            "User asks about CALL vs CBS, routing concepts, collection policy.",
            "User asks about the evaluation system itself.",
        ],
        "when_not_to_use": [
            "User asks about a specific customer's score — use get_recovery_opportunity.",
            "User asks about a specific customer's decision — use get_next_best_action.",
            "User asks about today's worklist — use get_portfolio.",
        ],
        "authority": "rag_read_only",
        "required_args": [],
        "optional_args": {"query": "natural language knowledge question"},
        "output_semantics": "Answer text with source citations from the knowledge corpus.",
        "timeout_seconds": 6,
        "fallback": "Return low-confidence refusal; assistant explains the topic is not in the knowledge base.",
    },
}


def is_allowed(tool_name: str) -> bool:
    """Check whether a tool name is in the approved allowlist."""
    return tool_name in ALLOWED_TOOLS


def is_forbidden(tool_name: str) -> bool:
    """Check whether a tool name is an explicitly forbidden action tool."""
    return tool_name in FORBIDDEN_ACTION_TOOLS


def catalog_for_prompt() -> str:
    """Render the tool catalog as a compact text block for the planner prompt."""
    lines: list[str] = []
    for name in sorted(ALLOWED_TOOLS):
        entry = TOOL_CATALOG.get(name, {})
        lines.append(f"### {name}")
        lines.append(f"  Purpose: {entry.get('purpose', '')}")
        when_to = entry.get("when_to_use", [])
        if when_to:
            lines.append("  When to use:")
            for item in when_to:
                lines.append(f"    - {item}")
        when_not = entry.get("when_not_to_use", [])
        if when_not:
            lines.append("  When NOT to use:")
            for item in when_not:
                lines.append(f"    - {item}")
        lines.append(f"  Authority: {entry.get('authority', 'read_only')}")
        req = entry.get("required_args", [])
        if req:
            lines.append(f"  Required args: {', '.join(req)}")
        lines.append("")
    return "\n".join(lines)
