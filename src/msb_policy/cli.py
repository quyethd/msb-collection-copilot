from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import PolicyConfig
from .io import evaluate_directory, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate deterministic TASK-002 policy facts")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/policy-results"))
    parser.add_argument("--ptp-grace-days", type=int, default=1, help="Configurable prototype grace period; not production MSB policy")
    args = parser.parse_args()
    results = evaluate_directory(args.input, PolicyConfig(args.ptp_grace_days))
    output = args.output / "policy_result.jsonl"
    write_jsonl(results, output)
    print(json.dumps({"status": "PASS", "record_count": len(results), "output": str(output), "ptp_grace_days": args.ptp_grace_days}, indent=2, sort_keys=True))


if __name__ == "__main__": main()

