from __future__ import annotations

from typing import Any, Callable

from .models import TOOL_ALLOWLIST, ACTION_TOOLS, ToolSpec
from .tool_descriptions import TOOL_SPECS

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class AgentToolRegistry:
    """Bounded tool registry for AgentBase.

    Only exposes the allowlisted read/compute tools.
    Action/write tools are never registered.
    """

    def __init__(self, tool_caller: ToolCaller):
        self._caller = tool_caller
        self._tools: dict[str, ToolSpec] = dict(TOOL_SPECS)

    @property
    def allowlist(self) -> frozenset[str]:
        return TOOL_ALLOWLIST

    @property
    def action_tools(self) -> frozenset[str]:
        return ACTION_TOOLS

    def available_tools(self) -> list[str]:
        return list(self._tools)

    def get_spec(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def is_allowed(self, name: str) -> bool:
        return name in TOOL_ALLOWLIST

    def is_action_tool(self, name: str) -> bool:
        return name in ACTION_TOOLS

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name in ACTION_TOOLS:
            return {"ok": False, "error": {"code": "ACTION_TOOL_BLOCKED",
                    "message": f"Action tool {name!r} is not exposed"}}
        if name not in TOOL_ALLOWLIST:
            return {"ok": False, "error": {"code": "FORBIDDEN_TOOL",
                    "message": f"Tool {name!r} is not in the allowlist"}}
        spec = self._tools.get(name)
        if spec is None:
            return {"ok": False, "error": {"code": "UNKNOWN_TOOL",
                    "message": f"Unknown tool {name!r}"}}
        return self._caller(name, arguments)

    def description_for_planner(self) -> str:
        from .tool_descriptions import registry_description
        return registry_description()

    def tool_description(self, name: str) -> str:
        from .tool_descriptions import tool_description_for_planner
        return tool_description_for_planner(name)
