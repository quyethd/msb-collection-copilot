from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from .models import CONTEXT_VERSION, DEFAULT_PREVIEW_LIMIT, SYNTHETIC_LABEL, DecisionContext, encode


def portfolio_index(contexts: Sequence[DecisionContext]) -> list[dict[str, Any]]:
    rows = []
    for context in contexts:
        debt, policy = context.debt, context.policy
        ranking, recovery = context.ranking, context.recovery_opportunity
        rows.append({
            "cif": context.cif, "final_route": policy["final_route"],
            "hard_suppressed": policy["hard_suppressed"],
            "total_outstanding_cif": debt["total_outstanding_cif"], "max_dpd_cif": debt["max_dpd_cif"],
            "baseline_rank": ranking["baseline_rank"], "recovery_rank": ranking["recovery_rank"],
            "rank_delta": ranking["rank_delta"], "movement": ranking["movement"],
            "recovery_opportunity_score": recovery["recovery_opportunity_score"],
            "business_urgency_score": recovery["business_urgency_score"],
            "ability_to_pay_score": recovery["ability_to_pay_score"],
            "willingness_to_pay_score": recovery["willingness_to_pay_score"],
            "contactability_score": recovery["contactability_score"],
            "timing_opportunity_score": recovery["timing_opportunity_score"],
            "strategic_adjustment_score": recovery["strategic_adjustment_score"],
            "availability": dict(context.availability),
            "synthetic_label": SYNTHETIC_LABEL,
        })
    return encode(sorted(rows, key=lambda row: row["recovery_rank"]))


def manifest(reference_date: str, customer_count: int, preview_limit: int) -> dict[str, Any]:
    return {
        "context_version": CONTEXT_VERSION, "reference_date": reference_date,
        "synthetic_data": True, "synthetic_label": SYNTHETIC_LABEL,
        "customer_count": customer_count, "preview_limit": preview_limit,
        "input_stages": {"source": "TASK-001", "policy": "TASK-002", "recovery": "TASK-003", "evaluation": "TASK-004"},
        "context_stage": "TASK-005",
        "artifacts": ["customer_context.jsonl", "portfolio_context_index.json", "golden_context_validation.json", "context_manifest.json"],
    }


def write_artifacts(contexts: Sequence[DecisionContext], validation: dict[str, Any], output: Path, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    context_path = output / "customer_context.jsonl"
    with context_path.open("w", encoding="utf-8") as handle:
        for context in sorted(contexts, key=lambda row: row.cif):
            handle.write(json.dumps(context.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    index_path = output / "portfolio_context_index.json"
    index_path.write_text(json.dumps(portfolio_index(contexts), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_path = output / "golden_context_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = output / "context_manifest.json"
    reference_date = contexts[0].as_of_date if contexts else ""
    manifest_path.write_text(json.dumps(manifest(reference_date, len(contexts), preview_limit), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"customer_context": context_path, "portfolio_context_index": index_path, "golden_context_validation": validation_path, "context_manifest": manifest_path}


def load_contexts(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
