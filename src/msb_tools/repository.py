from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from msb_context.assembler import assemble_directory
from msb_context.io import portfolio_index
from msb_policy.io import read_csv

from .errors import ToolFailure

SYNTHETIC_LABEL = "SYNTHETIC PROTOTYPE DATA"


class ToolRepository:
    """Read-only snapshot of accepted deterministic stage outputs."""

    def __init__(self, input_directory: Path):
        self.input_directory = Path(input_directory)
        try:
            manifest = json.loads((self.input_directory / "generation_manifest.json").read_text(encoding="utf-8"))
            contexts = assemble_directory(self.input_directory)
        except Exception as error:
            raise ToolFailure("DATA_INTEGRITY_ERROR", f"Unable to load accepted deterministic data: {error}") from error
        self.reference_date = str(manifest["reference_date"])
        self._contexts = {row.cif: row.to_dict() for row in contexts}
        self._portfolio = portfolio_index(contexts)
        self._events = {
            "CALL": read_csv(self.input_directory, "call_history"),
            "OPERATION": read_csv(self.input_directory, "operation_result"),
            "PAYMENT": read_csv(self.input_directory, "payment_event"),
        }

    @property
    def meta(self) -> dict[str, Any]:
        return {"synthetic_data": True, "synthetic_label": SYNTHETIC_LABEL,
                "reference_date": self.reference_date}

    @property
    def cifs(self) -> set[str]:
        return set(self._contexts)

    def context(self, cif: str) -> dict[str, Any]:
        try:
            return copy.deepcopy(self._contexts[cif])
        except KeyError as error:
            raise ToolFailure("NOT_FOUND", f"CIF {cif!r} was not found") from error

    def portfolio(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._portfolio)

    def source_events(self, family: str) -> list[dict[str, str]]:
        return copy.deepcopy(self._events[family])
