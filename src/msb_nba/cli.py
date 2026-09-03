from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import DEFAULT_CONFIG
from .engine import decide
from .io import write_artifacts
from .repository import load_inputs
from .validate import validate


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic TASK-007A NBA decisions")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/next-best-action"))
    args = parser.parse_args()
    contexts, calls = load_inputs(args.input)
    decisions = [decide(row, calls.get(row["cif"], ()), DEFAULT_CONFIG) for row in contexts]
    report, golden = validate(contexts, decisions, calls, DEFAULT_CONFIG)
    paths = write_artifacts(decisions, report, golden, args.output, DEFAULT_CONFIG)
    print(json.dumps({"status": report["status"], "decision_count": len(decisions), "artifacts": {key: str(value) for key, value in paths.items()}}, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
