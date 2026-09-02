from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import DecisionContextStore, assemble_directory
from .io import write_artifacts
from .models import DEFAULT_PREVIEW_LIMIT
from .validate import validate, validate_persisted


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic synthetic Customer Decision Context artifacts")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--output", type=Path, default=Path("build/decision-context"))
    parser.add_argument("--preview-limit", type=int, default=DEFAULT_PREVIEW_LIMIT)
    parser.add_argument("--cif")
    args = parser.parse_args()
    contexts = assemble_directory(args.input, args.preview_limit)
    if args.cif:
        print(json.dumps(DecisionContextStore(contexts).get_customer_context(args.cif).to_dict(), indent=2, sort_keys=True))
        return
    report = validate(args.input, contexts, args.preview_limit)
    artifacts = write_artifacts(contexts, report, args.output, args.preview_limit)
    report = validate_persisted(args.input, args.output, args.preview_limit)
    artifacts["golden_context_validation"].write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "record_count": len(contexts), "artifacts": {key: str(value) for key, value in artifacts.items()}}, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__": main()
