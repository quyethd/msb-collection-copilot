from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import evaluate_directory, write_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic TASK-003 Recovery Opportunity scoring")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/recovery-opportunity"))
    args = parser.parse_args()
    results = evaluate_directory(args.input)
    path = write_results(results, args.output)
    print(json.dumps({"status": "PASS", "record_count": len(results), "output": str(path)}, indent=2, sort_keys=True))


if __name__ == "__main__": main()

