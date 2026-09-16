from __future__ import annotations

import time
from typing import Any, Callable

from .cache import CaseBriefCache
from .generator import CaseBriefGenerator
from .models import CaseBriefResult

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class CaseBriefService:
    """High-level service for AI Case Brief generation.

    Wraps CaseBriefGenerator with the existing tool caller, LLM client,
    and optional knowledge RAG service.
    """

    def __init__(
        self,
        tool_caller: ToolCaller,
        llm_complete: Callable[[str, int, float], tuple[str | None, str | None]] | None = None,
        knowledge_answer: Callable[[str], dict[str, Any]] | None = None,
        cache: CaseBriefCache | None = None,
    ):
        self._generator = CaseBriefGenerator(
            tool_caller=tool_caller,
            llm_complete=llm_complete,
            knowledge_answer=knowledge_answer,
            cache=cache or CaseBriefCache(),
        )

    def generate_brief(
        self,
        cif: str,
        simulation_changes: dict[str, Any] | None = None,
    ) -> CaseBriefResult:
        return self._generator.generate_brief(cif, simulation_changes)

    def answer_question(
        self,
        cif: str,
        question: str,
        simulation_changes: dict[str, Any] | None = None,
    ) -> CaseBriefResult:
        return self._generator.answer_question(cif, question, simulation_changes)

    def invalidate_cache(self, cif: str) -> None:
        self._generator._cache.invalidate(cif)
