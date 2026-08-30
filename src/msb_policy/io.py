from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from .engine import PolicyConfig, PolicyResult, evaluate_dataset


def read_csv(directory: Path, table: str) -> list[dict[str, str]]:
    with (directory / f"{table}.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def evaluate_directory(directory: Path, config: PolicyConfig = PolicyConfig()) -> list[PolicyResult]:
    manifest = json.loads((directory / "generation_manifest.json").read_text(encoding="utf-8"))
    return evaluate_dataset(
        read_csv(directory, "customer"), read_csv(directory, "loan_account"),
        read_csv(directory, "collection_assignment"), read_csv(directory, "operation_result"),
        read_csv(directory, "payment_event"), read_csv(directory, "call_history"),
        date.fromisoformat(manifest["reference_date"]), config,
    )


def write_jsonl(results: list[PolicyResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")

