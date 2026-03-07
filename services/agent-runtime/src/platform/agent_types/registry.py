from __future__ import annotations

from typing import Callable, Dict, Any

from src.graph.build_graph import build_graph
from src.platform.agent_types.chat_agent import get_agent_type_spec as get_chat_agent_spec
from src.platform.agent_types.summarizer_agent import get_agent_type_spec as get_summarizer_agent_spec
from src.platform.agent_types.workflow_agent import get_agent_type_spec as get_workflow_agent_spec


def get_agent_type_registry() -> Dict[str, Dict[str, Any]]:
    return {
        "chat_agent": get_chat_agent_spec(),
        "summarizer_agent": get_summarizer_agent_spec(),
        "workflow_agent": get_workflow_agent_spec(),
    }


def get_agent_type_spec(agent_type_name: str) -> Dict[str, Any]:
    registry = get_agent_type_registry()

    if agent_type_name not in registry:
        raise ValueError(f"Unsupported agent type: {agent_type_name}")

    return registry[agent_type_name]


def get_agent_graph_builder(agent_type_name: str) -> Callable:
    if agent_type_name == "chat_agent":
        return build_graph

    raise RuntimeError(f"No graph builder registered for agent_type: {agent_type_name}")