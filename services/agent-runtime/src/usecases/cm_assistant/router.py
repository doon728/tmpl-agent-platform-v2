from __future__ import annotations

from typing import Dict, Any

from src.usecases.cm_assistant.routing import EXPLICIT_TOOL_PREFIXES


def route_step(step: str, ctx: Dict[str, Any], raw_prompt: str | None = None) -> Dict[str, Any]:
    """
    Minimal router.

    Responsibility:
    - Parse planner tool calls
    - Validate arguments
    - Return tool execution plan

    No intent detection.
    No heuristics.
    """

    step = (step or "").strip()
    lower_step = step.lower()

    if not step:
        return {"mode": "none"}

    # ---------------------------------------------------
    # Explicit tool call from planner
    # ---------------------------------------------------

    if lower_step.startswith(EXPLICIT_TOOL_PREFIXES):

        tool_name, tool_value = step.split(":", 1)

        tool_name = tool_name.strip()
        tool_value = tool_value.strip()

        # write_case_note special argument format
        if tool_name == "write_case_note":

            if "|" not in tool_value:
                raise RuntimeError(
                    "write_case_note requires: write_case_note: <assessment_id> | <note>"
                )

            case_id, note = [x.strip() for x in tool_value.split("|", 1)]

            return {
                "mode": "direct_tool",
                "tool": "write_case_note",
                "input": {
                    "case_id": case_id,
                    "note": note,
                },
            }

        # all other tools use a single argument
        if tool_name == "get_assessment_summary":

            return {
                "mode": "direct_tool",
                "tool": "get_assessment_summary",
                "input": {"assessment_id": tool_value},
            }

        if tool_name == "get_member_summary":

            return {
                "mode": "direct_tool",
                "tool": "get_member_summary",
                "input": {"member_id": tool_value},
            }

        if tool_name == "search_kb":

            return {
                "mode": "direct_tool",
                "tool": "search_kb",
                "input": {"query": tool_value},
            }

    # ---------------------------------------------------
    # fallback
    # ---------------------------------------------------

    return {
        "mode": "direct_tool",
        "tool": "search_kb",
        "input": {"query": raw_prompt or step},
    }