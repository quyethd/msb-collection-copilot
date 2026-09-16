from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

CaseState = Literal["BASELINE", "SIMULATION"]
AgentPath = Literal["AGENTBASE", "STATIC", "DETERMINISTIC"]
BriefStatus = Literal["IDLE", "LOADING", "READY", "FALLBACK", "ERROR"]

PROMPT_VERSION = "TASK-015-V1"
TOOL_REGISTRY_VERSION = "TASK-015-V1"
CANONICAL_MODEL = "glm-5.2"
DISCLAIMER = "AI hỗ trợ tóm tắt và giải thích; quyết định nghiệp vụ do Bộ máy quyết định xác định."

MAX_TOOL_CALLS = 5
MAX_PLANNING_ROUNDS = 2
MAX_RAG_CALLS = 1
MAX_SIMULATION_CALLS = 1
MAX_AGENT_TIME_SECONDS = 8

TOOL_ALLOWLIST = frozenset({
    "get_customer_360",
    "get_current_decision",
    "get_cashflow_summary",
    "get_ptp_context",
    "get_contact_history",
    "get_score_breakdown",
    "simulate_decision",
    "find_knowledge",
})

ACTION_TOOLS = frozenset({
    "send_zalo", "send_sms", "send_email", "make_call",
    "create_ptp", "update_ptp", "update_customer",
    "change_route", "change_score", "override_policy",
})


@dataclass(frozen=True)
class ToolSpec:
    name: str
    purpose: str
    when_to_use: list[str]
    when_not_to_use: list[str]
    authority: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    timeout_ms: int
    fallback: str
    permission: Literal["READ", "COMPUTE"]


@dataclass(frozen=True)
class CaseContext:
    cif: str
    as_of: str
    state: CaseState
    customer: dict[str, Any]
    decision: dict[str, Any]
    score_breakdown: dict[str, Any]
    cashflow: dict[str, Any]
    ptp: dict[str, Any]
    contact: dict[str, Any]
    simulation: dict[str, Any] | None
    knowledge: list[dict[str, Any]]
    missing_data: list[str]
    data_quality: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cif": self.cif,
            "as_of": self.as_of,
            "state": self.state,
            "customer": self.customer,
            "decision": self.decision,
            "score_breakdown": self.score_breakdown,
            "cashflow": self.cashflow,
            "ptp": self.ptp,
            "contact": self.contact,
            "simulation": self.simulation,
            "knowledge": self.knowledge,
            "missing_data": self.missing_data,
            "data_quality": self.data_quality,
        }

    def hash(self) -> str:
        data = self.to_dict()
        data.pop("as_of", None)
        payload = json.dumps(data, sort_keys=True, default=str).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class KeyEvidence:
    label: str
    value: str
    reason: str
    source: str


@dataclass(frozen=True)
class KnowledgeRef:
    title: str
    source_id: str


@dataclass(frozen=True)
class CaseBrief:
    headline: str
    summary: str
    key_evidence: list[KeyEvidence]
    decision_explanation: list[str]
    officer_focus: list[str]
    knowledge_refs: list[KnowledgeRef]
    missing_data: list[str]
    state: CaseState
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "summary": self.summary,
            "key_evidence": [
                {"label": e.label, "value": e.value, "reason": e.reason, "source": e.source}
                for e in self.key_evidence
            ],
            "decision_explanation": self.decision_explanation,
            "officer_focus": self.officer_focus,
            "knowledge_refs": [
                {"title": r.title, "source_id": r.source_id}
                for r in self.knowledge_refs
            ],
            "missing_data": self.missing_data,
            "state": self.state,
            "disclaimer": self.disclaimer,
        }


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditMetadata:
    cif: str
    generated_at: str
    case_context_hash: str
    decision_snapshot_hash: str
    prompt_version: str
    tool_registry_version: str
    agent_path: AgentPath
    tools_used: list[str]
    model: str
    knowledge_refs: list[dict[str, Any]]
    validation_result: str
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cif": self.cif,
            "generated_at": self.generated_at,
            "case_context_hash": self.case_context_hash,
            "decision_snapshot_hash": self.decision_snapshot_hash,
            "prompt_version": self.prompt_version,
            "tool_registry_version": self.tool_registry_version,
            "agent_path": self.agent_path,
            "tools_used": self.tools_used,
            "model": self.model,
            "knowledge_refs": self.knowledge_refs,
            "validation_result": self.validation_result,
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True)
class CaseBriefResult:
    brief: CaseBrief
    agent_path: AgentPath
    tools_used: list[str]
    validation: ValidationResult
    audit: AuditMetadata
    cache_hit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "success",
            "brief": self.brief.to_dict(),
            "agent_path": self.agent_path,
            "tools_used": self.tools_used,
            "validation": {"passed": self.validation.passed, "reasons": self.validation.reasons},
            "audit": self.audit.to_dict(),
            "cache_hit": self.cache_hit,
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_dict(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()
