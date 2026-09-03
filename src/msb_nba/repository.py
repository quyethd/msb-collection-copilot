from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from msb_context.assembler import assemble_directory
from msb_policy.io import read_csv


def load_inputs(source_directory: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]]]:
    contexts = [row.to_dict() for row in assemble_directory(source_directory)]
    calls: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(source_directory, "call_history"): calls[row["cif"]].append(row)
    return contexts, calls
