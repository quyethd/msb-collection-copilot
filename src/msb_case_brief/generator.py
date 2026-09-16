from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

from .audit import CaseBriefAudit
from .cache import CaseBriefCache
from .context_builder import CaseContextBuilder
from .fallback import CaseBriefFallback
from .models import (AgentPath, AuditMetadata, CaseBrief, CaseBriefResult, CaseContext,
                     CaseState, CANONICAL_MODEL, DISCLAIMER, KeyEvidence, KnowledgeRef,
                     MAX_AGENT_TIME_SECONDS, PROMPT_VERSION, TOOL_REGISTRY_VERSION,
                     ValidationResult, now_iso, _hash_dict)
from .planner import AgentPlannerAdapter
from .tool_registry import AgentToolRegistry
from .validator import CaseBriefValidator

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]
LLMComplete = Callable[[str, int, float], tuple[str | None, str | None]]


def brief_from_dict(data: dict[str, Any]) -> CaseBrief:
    return CaseBrief(
        headline=data.get("headline", ""),
        summary=data.get("summary", ""),
        key_evidence=[KeyEvidence(**e) for e in data.get("key_evidence", [])],
        decision_explanation=data.get("decision_explanation", []),
        officer_focus=data.get("officer_focus", []),
        knowledge_refs=[KnowledgeRef(**r) for r in data.get("knowledge_refs", [])],
        missing_data=data.get("missing_data", []),
        state=data.get("state", "BASELINE"),
        disclaimer=data.get("disclaimer", ""),
    )


def audit_from_dict(data: dict[str, Any]) -> AuditMetadata:
    return AuditMetadata(
        cif=data["cif"], generated_at=data["generated_at"],
        case_context_hash=data["case_context_hash"],
        decision_snapshot_hash=data["decision_snapshot_hash"],
        prompt_version=data["prompt_version"],
        tool_registry_version=data["tool_registry_version"],
        agent_path=data["agent_path"], tools_used=data["tools_used"],
        model=data["model"], knowledge_refs=data["knowledge_refs"],
        validation_result=data["validation_result"],
        latency_ms=data["latency_ms"],
    )


_GLM_SYSTEM_PROMPT = """\
Bạn là Trợ lý Thu hồi Nợ dành cho cán bộ MSB.

Nhiệm vụ:
TÓM TẮT và GIẢI THÍCH dữ liệu được cung cấp.

Bạn KHÔNG có quyền:
- thay đổi tuyến xử lý;
- tính hoặc sửa Recovery Opportunity score;
- thay đổi treatment;
- chọn/thay đổi channel;
- tạo chính sách nghiệp vụ;
- suy đoán dữ liệu không được cung cấp.

Decision Snapshot là kết quả chính thức từ Decision Core.
Simulation Snapshot là kết quả chính thức từ Simulation Core.

Mọi diễn giải phải nhất quán tuyệt đối với snapshot tương ứng.

Chỉ sử dụng:
1. Canonical Case Context.
2. Knowledge snippets có nguồn.

Nếu dữ liệu không tồn tại:
hãy nói rõ "chưa có dữ liệu".

Không suy diễn:
- ý định thanh toán;
- khả năng tài chính;
- nguyên nhân quá hạn;
- tình trạng liên hệ
nếu không có bằng chứng.

Trả đúng JSON schema.

Ngôn ngữ:
tiếng Việt ngắn gọn, nghiệp vụ, dễ đọc.

Đối tượng:
Collection Officer.

Mục tiêu:
giúp cán bộ hiểu hồ sơ trong khoảng 15–30 giây.
"""

_GLM_OUTPUT_SCHEMA = """\
Trả về JSON đúng theo schema sau:
{
  "headline": "string — tiêu đề ngắn 1 câu",
  "summary": "string — tóm tắt 2-3 câu",
  "key_evidence": [
    {"label": "string", "value": "string", "reason": "string", "source": "customer360|cashflow|ptp|contact|decision|score|knowledge|simulation"}
  ],
  "decision_explanation": ["string"],
  "officer_focus": ["string"],
  "knowledge_refs": [
    {"title": "string", "source_id": "string"}
  ],
  "missing_data": ["string"],
  "state": "BASELINE|SIMULATION",
  "disclaimer": "AI hỗ trợ tóm tắt và giải thích; quyết định nghiệp vụ do Bộ máy quyết định xác định."
}

KHÔNG tạo các trường: recommended_action, new_score, new_route, new_channel, new_treatment, payment_probability.
"""


def _extract_json(text: str) -> dict[str, Any] | None:
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None


class CaseBriefGenerator:
    """Three-level fallback generator.

    LEVEL 1: AgentBase + dynamic tools + optional RAG + GLM + validator
    LEVEL 2: Static canonical orchestration + GLM + validator
    LEVEL 3: Deterministic safe template
    """

    def __init__(
        self,
        tool_caller: ToolCaller,
        llm_complete: LLMComplete | None = None,
        knowledge_answer: Callable[[str], dict[str, Any]] | None = None,
        cache: CaseBriefCache | None = None,
    ):
        self._raw_caller = tool_caller
        self._llm_complete = llm_complete
        self._knowledge_answer = knowledge_answer
        self._cache = cache or CaseBriefCache()
        self._registry = AgentToolRegistry(self._adapted_caller)
        self._planner = AgentPlannerAdapter(self._registry)
        self._context_builder = CaseContextBuilder()
        self._validator = CaseBriefValidator()
        self._fallback = CaseBriefFallback()
        self._audit = CaseBriefAudit()

    def _adapted_caller(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Map allowlisted tool names to actual tool implementations."""
        if name == "get_customer_360":
            return self._raw_caller("get_customer_360", args)
        if name == "get_current_decision":
            return self._raw_caller("get_next_best_action", args)
        if name == "get_cashflow_summary":
            return self._raw_caller("get_cashflow_intelligence", args)
        if name == "get_ptp_context":
            ctx = self._raw_caller("get_customer_360", args)
            if ctx.get("ok") and ctx.get("data"):
                return {"ok": True, "data": ctx["data"].get("ptp", {})}
            return ctx
        if name == "get_contact_history":
            return self._raw_caller("get_collection_history", args)
        if name == "get_score_breakdown":
            return self._raw_caller("get_recovery_opportunity", args)
        if name == "simulate_decision":
            return self._raw_caller("simulate_decision", args)
        if name == "find_knowledge":
            if self._knowledge_answer:
                try:
                    result = self._knowledge_answer(args.get("question", ""))
                    return {"ok": True, "data": result}
                except Exception:
                    return {"ok": False, "error": {"code": "KNOWLEDGE_ERROR", "message": "Knowledge retrieval failed"}}
            return {"ok": False, "error": {"code": "NOT_CONFIGURED", "message": "Knowledge RAG not configured"}}
        return {"ok": False, "error": {"code": "UNKNOWN_TOOL", "message": f"Unknown tool {name!r}"}}

    def _call_tool(self, name: str, cif: str, **extra: Any) -> tuple[dict[str, Any] | None, bool]:
        args = {"cif": cif, **extra}
        result = self._registry.invoke(name, args)
        if result.get("ok") and result.get("data"):
            return result["data"], True
        return None, False

    def _gather_tool_results(self, tools: list[str], cif: str,
                             simulation_changes: dict[str, Any] | None = None,
                             question: str | None = None) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name in tools:
            if name == "simulate_decision":
                data, ok = self._call_tool(name, cif, changes=simulation_changes or {})
            elif name == "find_knowledge":
                if question:
                    data, ok = self._call_tool(name, cif, question=question)
                else:
                    continue
            else:
                data, ok = self._call_tool(name, cif)
            if ok:
                results[name] = data
        return results

    def _build_context(self, cif: str, tool_results: dict[str, Any],
                       state: CaseState = "BASELINE") -> CaseContext:
        knowledge: list[dict[str, Any]] = []
        if "find_knowledge" in tool_results:
            kr = tool_results["find_knowledge"]
            if isinstance(kr, dict):
                for src in kr.get("sources", []):
                    knowledge.append({
                        "title": src.get("title", ""),
                        "source_id": src.get("chunk_id", src.get("document_id", "")),
                    })

        return self._context_builder.build(
            cif=cif,
            customer_360=tool_results.get("get_customer_360"),
            decision=tool_results.get("get_current_decision"),
            cashflow=tool_results.get("get_cashflow_summary"),
            ptp=tool_results.get("get_ptp_context"),
            contact=tool_results.get("get_contact_history"),
            score_breakdown=tool_results.get("get_score_breakdown"),
            simulation=tool_results.get("simulate_decision"),
            knowledge=knowledge,
            state=state,
        )

    def _generate_glm_brief(self, context: CaseContext, question: str | None = None) -> CaseBrief | None:
        if self._llm_complete is None:
            return None
        context_json = json.dumps(context.to_dict(), ensure_ascii=False, default=str)
        prompt = _GLM_SYSTEM_PROMPT + "\n\n" + _GLM_OUTPUT_SCHEMA + "\n\n"
        if question:
            prompt += f"Câu hỏi: {question}\n\n"
        prompt += f"Case Context:\n{context_json}\n\nTrả về JSON:"
        try:
            content, _ = self._llm_complete(prompt, 800, 0)
        except Exception:
            return None
        if not content:
            return None
        parsed = _extract_json(content)
        if parsed is None:
            return None
        return self._validator.validate_parsed_json(parsed, context)

    def generate_brief(
        self,
        cif: str,
        simulation_changes: dict[str, Any] | None = None,
    ) -> CaseBriefResult:
        started = time.perf_counter()
        state: CaseState = "SIMULATION" if simulation_changes else "BASELINE"

        context_hash = _hash_dict({"cif": cif, "state": state})
        decision_hash = _hash_dict({"cif": cif})
        sim_hash = _hash_dict(simulation_changes or {})
        cached = self._cache.get(cif, context_hash, decision_hash, sim_hash)
        if cached:
            return CaseBriefResult(
                brief=brief_from_dict(cached["brief"]),
                agent_path=cached["agent_path"],
                tools_used=cached["tools_used"],
                validation=ValidationResult(passed=cached["validation"]["passed"], reasons=cached["validation"]["reasons"]),
                audit=audit_from_dict(cached["audit"]),
                cache_hit=True,
            )

        tools = self._planner.plan_initial_brief(cif)
        tool_results = self._gather_tool_results(tools, cif, simulation_changes=simulation_changes)
        context = self._build_context(cif, tool_results, state=state)

        brief, agent_path, tools_used, validation = self._try_levels(context, cif, tools, simulation_changes)

        latency_ms = (time.perf_counter() - started) * 1000
        audit = self._audit.build(
            cif=cif,
            context_hash=context.hash(),
            decision_snapshot_hash=_hash_dict(context.decision),
            agent_path=agent_path,
            tools_used=tools_used,
            model=CANONICAL_MODEL if agent_path in ("AGENTBASE", "STATIC") else "deterministic",
            knowledge_refs=[{"title": r.title, "source_id": r.source_id} for r in brief.knowledge_refs],
            validation=validation,
            latency_ms=latency_ms,
        )

        result = CaseBriefResult(
            brief=brief,
            agent_path=agent_path,
            tools_used=tools_used,
            validation=validation,
            audit=audit,
        )
        self._cache.put(cif, context_hash, decision_hash, sim_hash, result.to_dict())
        return result

    def answer_question(
        self,
        cif: str,
        question: str,
        simulation_changes: dict[str, Any] | None = None,
    ) -> CaseBriefResult:
        started = time.perf_counter()
        state: CaseState = "SIMULATION" if simulation_changes else "BASELINE"

        tools = self._planner.plan_followup(cif, question)
        tool_results = self._gather_tool_results(tools, cif, simulation_changes=simulation_changes, question=question)
        context = self._build_context(cif, tool_results, state=state)

        brief, agent_path, tools_used, validation = self._try_levels(context, cif, tools, simulation_changes, question)

        latency_ms = (time.perf_counter() - started) * 1000
        audit = self._audit.build(
            cif=cif,
            context_hash=context.hash(),
            decision_snapshot_hash=_hash_dict(context.decision),
            agent_path=agent_path,
            tools_used=tools_used,
            model=CANONICAL_MODEL if agent_path in ("AGENTBASE", "STATIC") else "deterministic",
            knowledge_refs=[{"title": r.title, "source_id": r.source_id} for r in brief.knowledge_refs],
            validation=validation,
            latency_ms=latency_ms,
        )

        return CaseBriefResult(
            brief=brief,
            agent_path=agent_path,
            tools_used=tools_used,
            validation=validation,
            audit=audit,
        )

    def _try_levels(
        self,
        context: CaseContext,
        cif: str,
        planned_tools: list[str],
        simulation_changes: dict[str, Any] | None = None,
        question: str | None = None,
    ) -> tuple[CaseBrief, AgentPath, list[str], ValidationResult]:
        elapsed = 0.0
        tools_used = list(planned_tools)

        if self._llm_complete is not None:
            brief = self._generate_glm_brief(context, question)
            if brief is not None:
                validation = self._validator.validate(brief, context)
                if validation.passed:
                    return brief, "AGENTBASE", tools_used, validation

        if self._llm_complete is not None:
            static_tools = ["get_current_decision", "get_customer_360"]
            static_results = self._gather_tool_results(static_tools, cif, simulation_changes=simulation_changes)
            static_context = self._build_context(cif, static_results, state=context.state)
            brief = self._generate_glm_brief(static_context, question)
            if brief is not None:
                validation = self._validator.validate(brief, static_context)
                if validation.passed:
                    return brief, "STATIC", static_tools, validation

        brief = self._fallback.generate(context)
        validation = self._validator.validate(brief, context)
        return brief, "DETERMINISTIC", tools_used, validation
