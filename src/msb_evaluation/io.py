from __future__ import annotations

import json
from pathlib import Path

from msb_recovery.io import evaluate_directory as evaluate_recovery_directory
from .engine import CifEvaluation, evaluate_cifs, summarize


def evaluate_directory(input_directory: Path) -> tuple[list[CifEvaluation], dict]:
    rows = evaluate_cifs(evaluate_recovery_directory(input_directory))
    return rows, summarize(rows)


def write_artifacts(rows: list[CifEvaluation], summary: dict, output_directory: Path) -> tuple[Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    detail_path = output_directory / "baseline_vs_recovery.jsonl"
    with detail_path.open("w", encoding="utf-8") as handle:
        for row in sorted(rows, key=lambda item: item.cif):
            handle.write(json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    summary_path = output_directory / "portfolio_evaluation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return detail_path, summary_path

