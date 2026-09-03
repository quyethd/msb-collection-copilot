from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .errors import ToolFailure, invalid
from .models import ToolEnvelope
from .repository import ToolRepository
from .tools import (get_cashflow_intelligence, get_collection_history, get_collection_policy,
                    get_customer_360, get_portfolio, get_recovery_opportunity)

ToolCallable = Callable[[dict[str, Any], ToolRepository], dict[str, Any]]
TOOL_REGISTRY: dict[str, ToolCallable] = {
    "get_portfolio": get_portfolio,
    "get_customer_360": get_customer_360,
    "get_collection_history": get_collection_history,
    "get_cashflow_intelligence": get_cashflow_intelligence,
    "get_collection_policy": get_collection_policy,
    "get_recovery_opportunity": get_recovery_opportunity,
}


def invoke_tool(tool_name: str, arguments: dict[str, Any], *, input_directory: Path | str = Path("build/synthetic-data"), repository: ToolRepository | None = None) -> dict[str, Any]:
    repo = repository
    try:
        if not isinstance(tool_name, str) or tool_name not in TOOL_REGISTRY:
            raise invalid(f"unknown tool: {tool_name!r}")
        if not isinstance(arguments, dict):
            raise invalid("arguments must be an object")
        repo = repo or ToolRepository(Path(input_directory))
        data = TOOL_REGISTRY[tool_name](arguments, repo)
        return ToolEnvelope(True, tool_name, data, repo.meta, None).to_dict()
    except ToolFailure as error:
        meta = repo.meta if repo is not None else _safe_meta(Path(input_directory))
        return ToolEnvelope(False, tool_name if isinstance(tool_name, str) else "", None, meta,
                            {"code": error.code, "message": error.message}).to_dict()
    except Exception:
        meta = repo.meta if repo is not None else _safe_meta(Path(input_directory))
        return ToolEnvelope(False, tool_name if isinstance(tool_name, str) else "", None, meta,
                            {"code": "INTERNAL_ERROR", "message": "Unexpected local tool failure"}).to_dict()


def _safe_meta(path: Path) -> dict[str, Any]:
    import json
    try: reference = str(json.loads((path / "generation_manifest.json").read_text())["reference_date"])
    except Exception: reference = ""
    return {"synthetic_data": True, "synthetic_label": "SYNTHETIC PROTOTYPE DATA", "reference_date": reference}
