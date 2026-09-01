from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import evaluate_directory, write_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate baseline versus Recovery Opportunity rankings")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/evaluation"))
    args = parser.parse_args()
    rows, summary = evaluate_directory(args.input)
    detail, portfolio = write_artifacts(rows, summary, args.output)
    print(json.dumps({"status": "PASS", "record_count": len(rows), "detail": str(detail), "summary": str(portfolio)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

