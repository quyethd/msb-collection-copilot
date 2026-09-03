from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .config import NBAConfig
from .engine import DECISION_VERSION
from .models import NBADecision
from .rules import RULE_ORDER


def build_manifest(decisions: Sequence[NBADecision], config: NBAConfig) -> dict[str, Any]:
    rules = Counter(row.selected_rule.rule_id for row in decisions)
    whens = Counter(row.recommendation.when.type for row in decisions)
    return {"decision_version": DECISION_VERSION, "reference_date": decisions[0].reference_date if decisions else None,
            "synthetic_data": True, "synthetic_label": "SYNTHETIC PROTOTYPE DATA",
            "input_provenance": {"decision_context": "TASK-005", "call_history_for_best_window": "TASK-001"},
            "rule_contract_version": "TASK-007A_DECISION_CONTRACT_V1", "cif_count": len(decisions),
            "rule_counts": {rule: rules[rule] for rule in RULE_ORDER},
            "when_distribution": {kind: whens[kind] for kind in ("SOURCE_DATETIME", "SOURCE_DATE", "BEST_WINDOW", "TODAY", "NONE")},
            "configuration": {"BROKEN_PTP_RECENT_INFLOW_THRESHOLD_VND": config.broken_ptp_recent_inflow_threshold_vnd,
                              "SELF_CURE_MAX_DPD": config.self_cure_max_dpd, "SELF_CURE_MIN_INFLOW_7D_VND": config.self_cure_min_inflow_7d_vnd,
                              "BEST_CONTACT_LOOKBACK_DAYS": config.best_contact_lookback_days,
                              "BEST_CONTACT_FALLBACK_WINDOW": config.best_contact_fallback_window,
                              "AUTHORIZED_CONTACT_WINDOWS": list(config.authorized_contact_windows)}}


def write_artifacts(decisions: Sequence[NBADecision], validation: dict[str, Any], golden: dict[str, Any], output: Path, config: NBAConfig) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    paths = {name: output / filename for name, filename in {"decisions": "next_best_action.jsonl", "manifest": "nba_manifest.json",
             "validation": "nba_validation.json", "golden": "golden_nba_validation.json"}.items()}
    with paths["decisions"].open("w", encoding="utf-8") as handle:
        for row in sorted(decisions, key=lambda item: item.cif):
            handle.write(json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    for key, value in (("manifest", build_manifest(decisions, config)), ("validation", validation), ("golden", golden)):
        paths[key].write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths


def load_decisions(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle: return [json.loads(line) for line in handle if line.strip()]
