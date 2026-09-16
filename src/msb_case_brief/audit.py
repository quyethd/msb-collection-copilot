from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import (AuditMetadata, AgentPath, PROMPT_VERSION, TOOL_REGISTRY_VERSION,
                     ValidationResult, now_iso, _hash_dict)


class CaseBriefAudit:
    """Record safe audit metadata. Never logs secrets."""

    def build(
        self,
        cif: str,
        context_hash: str,
        decision_snapshot_hash: str,
        agent_path: AgentPath,
        tools_used: list[str],
        model: str,
        knowledge_refs: list[dict[str, Any]],
        validation: ValidationResult,
        latency_ms: float,
    ) -> AuditMetadata:
        return AuditMetadata(
            cif=cif,
            generated_at=now_iso(),
            case_context_hash=context_hash,
            decision_snapshot_hash=decision_snapshot_hash,
            prompt_version=PROMPT_VERSION,
            tool_registry_version=TOOL_REGISTRY_VERSION,
            agent_path=agent_path,
            tools_used=tools_used,
            model=model,
            knowledge_refs=knowledge_refs,
            validation_result="PASS" if validation.passed else "FAIL",
            latency_ms=round(latency_ms, 2),
        )

    def to_safe_log(self, audit: AuditMetadata) -> dict[str, Any]:
        """Return only safe fields for logging. No secrets, no full prompts."""
        return {
            "cif": audit.cif,
            "generated_at": audit.generated_at,
            "agent_path": audit.agent_path,
            "tools_used": audit.tools_used,
            "model": audit.model,
            "validation_result": audit.validation_result,
            "latency_ms": audit.latency_ms,
            "prompt_version": audit.prompt_version,
            "tool_registry_version": audit.tool_registry_version,
        }
