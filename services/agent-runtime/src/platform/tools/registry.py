from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from src.platform.tools.validation import validate_tool_input
from config.settings import get_config


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
    mode: str = "read"          # "read" or "write"
    primary_arg: str = "query"  # default for single-arg tools


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    # -------------------------
    # Config helpers
    # -------------------------
    def allowed_tools(self) -> list[str]:
        """
        List of tools allowed for this runtime (from config).
        """
        return get_config("tools.allowed", [])

    def is_allowed(self, name: str) -> bool:
        return name in set(self.allowed_tools())

    def risk_for(self, name: str) -> str:
        """
        Returns risk level for a tool: "low" (default) or "high".
        Used by planner heuristics.
        """
        risk_levels = get_config("tools.risk_levels", {}) or {}
        return (risk_levels.get(name) or "low").lower()

    # -------------------------
    # Registry ops
    # -------------------------
    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise RuntimeError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_spec(self, name: str) -> ToolSpec:
        return self.get(name)

    def _check_allowed(self, name: str) -> None:
        if not self.is_allowed(name):
            raise RuntimeError(f"TOOL_NOT_ALLOWED: {name}")

    # -------------------------
    # Invocation
    # -------------------------
    def invoke(self, name: str, tool_input: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normal invocation path (may require approval).
        """
        self._check_allowed(name)

        risk = self.risk_for(name)

        spec = self.get(name)
        validate_tool_input(spec, tool_input)

        # Risk gate first
        if risk == "high":
            return {
                "approval_required": True,
                "tool_name": spec.name,
                "tool_input": tool_input,
                "ctx": ctx,
                "message": f"High risk tool requires approval: {spec.name}",
            }

        # Mode gate next
        if spec.mode == "write":
            return {
                "approval_required": True,
                "tool_name": spec.name,
                "tool_input": tool_input,
                "ctx": ctx,
                "message": f"Approval required before executing write tool: {spec.name}",
            }

        return spec.handler(tool_input, ctx)

    def invoke_approved(self, name: str, tool_input: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-approval execution path (bypasses approval gates).
        Only call this from /approvals/resume after a human approved.
        """
        self._check_allowed(name)

        spec = self.get(name)
        validate_tool_input(spec, tool_input)

        # Execute directly (NO approval gates here)
        return spec.handler(tool_input, ctx)


registry = ToolRegistry()