from __future__ import annotations

from pydantic import BaseModel, Field

from src.platform.tools.registry import registry
from src.platform.tools.types import ToolSpec


class SearchKbInput(BaseModel):
    query: str = Field(min_length=1)


class SearchKbOutput(BaseModel):
    results: list[dict]


def register_platform_tools() -> None:
    # idempotent-ish for local dev; ignore if already registered
    try:
        registry.register(
            ToolSpec(
                name="search_kb",
                mode="read",
                description="Search knowledge base",
                input_model=SearchKbInput,
                output_model=SearchKbOutput,
            )
        )
    except Exception:
        pass