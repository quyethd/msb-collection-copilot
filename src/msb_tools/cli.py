from __future__ import annotations

import argparse
import json
from pathlib import Path

from .registry import invoke_tool


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke one deterministic TASK-006 collection tool")
    parser.add_argument("--input", type=Path, default=Path("build/synthetic-data"))
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args", default="{}")
    args = parser.parse_args()
    try: arguments = json.loads(args.args)
    except json.JSONDecodeError as error:
        parser.error(f"--args must be valid JSON: {error}")
    result = invoke_tool(args.tool, arguments, input_directory=args.input)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__": main()
