from __future__ import annotations

from src.platform.tools.registry import ToolSpec, registry
from src.platform.tools.bindings import search_kb, get_member, write_case_note


def register_tools() -> None:

    # --- search KB ---
    registry.register(
        ToolSpec(
            name="search_kb",
            description="Search KB for relevant docs",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=lambda tool_input, ctx: {"results": search_kb(tool_input["query"], ctx)},
            mode="read",
            primary_arg="query",
        )
    )

    # --- get member ---
    registry.register(
        ToolSpec(
            name="get_member",
            description="Fetch member record",
            input_schema={
                "type": "object",
                "properties": {"member_id": {"type": "string"}},
                "required": ["member_id"],
            },
            handler=lambda tool_input, ctx: get_member(tool_input["member_id"], ctx),
            mode="read",
            primary_arg="member_id",
        )
    )

    # --- write case note ---
    registry.register(
        ToolSpec(
            name="write_case_note",
            description="Write note to case",
            input_schema={
                "type": "object",
                "properties": {"note": {"type": "string"}},
                "required": ["note"],
            },
            handler=lambda tool_input, ctx: write_case_note(tool_input["case_id"], tool_input["note"], ctx),
            mode="write",
            primary_arg="note",
        )
    )