from __future__ import annotations

from typing import Dict, Any


AGENT_TYPE_NAME = "summarizer_agent"


def get_agent_type_spec() -> Dict[str, Any]:
    return {
        "name": AGENT_TYPE_NAME,
        "description": "Input → summarize → aggregate workflow",
        "graph_type": "summarizer",
        "supports_user_chat": False,
        "supports_rag": True,
        "supports_approvals": False,
    }