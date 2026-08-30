from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from msb_policy.io import evaluate_directory as evaluate_policy_directory, read_csv
from .engine import RecoveryConfig, RecoveryOpportunityResult, evaluate_recovery


def group(rows: list[dict[str, str]]) -> Mapping[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows: result[row["cif"]].append(row)
    return result


def evaluate_directory(directory: Path) -> list[RecoveryOpportunityResult]:
    manifest = json.loads((directory / "generation_manifest.json").read_text(encoding="utf-8"))
    reference_date = date.fromisoformat(manifest["reference_date"])
    policies = evaluate_policy_directory(directory)
    return evaluate_recovery(policies, group(read_csv(directory, "cashflow_transaction")), group(read_csv(directory, "payment_event")), group(read_csv(directory, "call_history")), group(read_csv(directory, "operation_result")), RecoveryConfig(reference_date))


def write_results(results: list[RecoveryOpportunityResult], output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / "recovery_opportunity_result.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for result in results: handle.write(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    return path

