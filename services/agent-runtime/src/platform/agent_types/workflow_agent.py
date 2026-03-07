from __future__ import annotations

from typing import Dict, Any


AGENT_TYPE_NAME = "workflow_agent"


def get_agent_type_spec() -> Dict[str, Any]:
    return {
        "name": AGENT_TYPE_NAME,
        "description": "Planner → multi-step tools → decision/action workflow",
        "graph_type": "workflow",
        "supports_user_chat": True,
        "supports_rag": True,
        "supports_approvals": True,
    }