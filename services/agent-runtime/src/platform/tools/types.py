from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolSpec:
    name: str
    mode: str  # "read" | "write"
    description: str
    mode: str = "read"
    input_model: Type[BaseModel]
    output_model: Optional[Type[BaseModel]] = None

    # tool implementation lives in tool-gateway, not agent-runtime
    # (agent-runtime just validates and calls gateway)


class ToolValidationError(RuntimeError):
    pass