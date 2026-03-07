from __future__ import annotations

from typing import Dict, Any


AGENT_TYPE_NAME = "chat_agent"


def get_agent_type_spec() -> Dict[str, Any]:
    return {
        "name": AGENT_TYPE_NAME,
        "description": "Planner → tool → LLM response chat workflow",
        "graph_type": "chat",
        "supports_user_chat": True,
        "supports_rag": True,
        "supports_approvals": True,
    }