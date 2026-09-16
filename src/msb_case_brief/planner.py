from __future__ import annotations

import re
import time
import unicodedata
from typing import Any

from .models import (MAX_PLANNING_ROUNDS, MAX_RAG_CALLS, MAX_SIMULATION_CALLS,
                     MAX_TOOL_CALLS, TOOL_ALLOWLIST)
from .tool_registry import AgentToolRegistry

_PLANNER_SYSTEM = """\
You are a bounded tool planner for MSB Collection Copilot.

Your job is to select the minimum set of allowed tools needed to answer the user's question.

Rules:
1. Never create business decisions.
2. get_current_decision is authoritative for route, score, treatment and channel.
3. Prefer factual tools before knowledge retrieval.
4. Use find_knowledge only for policy/definition or when facts are insufficient.
5. Use simulate_decision only for explicit hypothetical questions.
6. Reuse existing context before another tool call.
7. Never call a tool only "just in case".
8. Never call write/action tools.
9. Stop when sufficient evidence is available.
10. Never infer active CIF; it must come from application state.
11. Never mix facts from different CIFs.
12. Never present simulation output as current-state fact.
"""


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower()).replace("đ", "d")
    return "".join(c for c in normalized if not unicodedata.combining(c))


_KNOWLEDGE_MARKERS = (
    "la gi", "de lam gi", "dong vai tro", "khac nhau the nao",
    "khac nhau nhu the nao", "khac nhau", "khac cbs", "khac call",
    "nam o dau", "chay o dau",
    "duoc tinh nhu the nao", "duoc tinh the nao", "tu quyet dinh",
    "tu dua ra quyet dinh", "ai quyet dinh", "quyen quyet dinh",
    "lien quan gi", "nghia la", "dinh nghia", "policy", "quy trinh",
    "thuat ngu", "huong dan",
)

_SIMULATION_MARKERS = (
    "neu ", "gia su", "mo phong", "tinh huong", "what if",
    "dieu gi xay ra", "xay ra neu",
)

_PTP_MARKERS = ("cam ket", "ptp", "hua tra", "hứa trả", "thất hứa", "pha vo",
                "that hua", "thanh toan mot phan", "hen tra", "hẹn trả")

_CASHFLOW_MARKERS = ("dong tien", "tien vao", "tien ve", "cashflow",
                     "tuan nay khong co tien", "tu thanh toan", "self cure",
                     "tai chinh", "thay doi tai chinh")

_CONTACT_MARKERS = ("lien he", "goi gan nhat", "da lien he", "bat may",
                    "ket qua goi", "ket qua cuoc goi", "callback", "verify contact",
                    "xac minh", "lich su goi", "lich su lien he", "cuoc goi")

_SCORE_MARKERS = ("vi sao diem", "diem la", "breakdown", "thanh phan",
                  "ability", "willingness", "contactability", "timing",
                  "keo diem", "diem len", "diem xuong", "diem nhu the nao",
                  "giai thich diem", "diem duoc tinh", "cac thanh phan diem")

_DECISION_MARKERS = ("tai sao", "sao ", "nen goi", "chua goi", "chua nen",
                     "goi ngay", "de xuat", "hanh dong", "xu ly sao",
                     "quyet dinh", "tuyen", "call hay cbs", "thuoc call",
                     "thuoc cbs", "channel", "kenh", "treatment",
                     "vay nen lam gi", "nen lam gi", "diem co hoi")

_CUSTOMER_MARKERS = ("tom tat", "tinh trang", "thong tin khach", "ho so",
                     "dpd", "du no", "phan khuc", "tong quan")


def _mentions(text: str, markers: tuple[str, ...]) -> bool:
    return any(m in text for m in markers)


class AgentPlannerAdapter:
    """Bounded planner that selects minimum necessary tools.

    Uses deterministic intent classification to choose tools.
    Never calls more than MAX_TOOL_CALLS tools.
    Never creates business decisions.
    """

    def __init__(self, registry: AgentToolRegistry):
        self.registry = registry

    def plan_initial_brief(self, cif: str) -> list[str]:
        """Select tools for the initial case brief.

        Always needs current decision. Other tools only when relevant.
        RAG is NOT called by default for every CIF.
        """
        tools = ["get_current_decision", "get_customer_360"]
        return tools[:MAX_TOOL_CALLS]

    def plan_followup(self, cif: str, question: str) -> list[str]:
        """Select minimum tools for a follow-up question.

        Uses deterministic intent classification.
        Respects all bounds: MAX_TOOL_CALLS, MAX_RAG_CALLS, MAX_SIMULATION_CALLS.
        """
        text = _plain(question.strip())
        if not text:
            return ["get_current_decision"]

        tools: list[str] = []
        rag_count = 0
        sim_count = 0

        if _mentions(text, _SCORE_MARKERS) and "get_score_breakdown" not in tools:
            tools.append("get_score_breakdown")
        elif "diem" in text and "duoc tinh" in text and "get_score_breakdown" not in tools:
            tools.append("get_score_breakdown")

        if _mentions(text, _PTP_MARKERS) and "get_ptp_context" not in tools:
            tools.append("get_ptp_context")

        if _mentions(text, _CASHFLOW_MARKERS) and "get_cashflow_summary" not in tools:
            tools.append("get_cashflow_summary")

        if _mentions(text, _CONTACT_MARKERS) and "get_contact_history" not in tools:
            tools.append("get_contact_history")

        if _mentions(text, _SIMULATION_MARKERS):
            if "get_current_decision" not in tools:
                tools.append("get_current_decision")
            if sim_count < MAX_SIMULATION_CALLS:
                tools.append("simulate_decision")
                sim_count = 1

        if _mentions(text, _KNOWLEDGE_MARKERS):
            tools.append("find_knowledge")
            rag_count = 1

        if _mentions(text, _DECISION_MARKERS) and "get_current_decision" not in tools:
            tools.append("get_current_decision")

        if _mentions(text, _CUSTOMER_MARKERS) and "get_customer_360" not in tools:
            tools.append("get_customer_360")

        if not tools:
            tools.append("get_current_decision")

        if rag_count > MAX_RAG_CALLS:
            tools = [t for t in tools if t != "find_knowledge"]
        if sim_count > MAX_SIMULATION_CALLS:
            tools = [t for t in tools if t != "simulate_decision"]

        allowed = [t for t in tools if t in TOOL_ALLOWLIST]
        return allowed[:MAX_TOOL_CALLS]

    def system_prompt(self) -> str:
        return _PLANNER_SYSTEM

    def is_bounded(self, tools_used: list[str]) -> bool:
        return len(tools_used) <= MAX_TOOL_CALLS
