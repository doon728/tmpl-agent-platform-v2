from __future__ import annotations

from typing import Any, Dict, List, TypedDict, Optional

from langgraph.graph import StateGraph, START, END

from src.usecase.agents.llm_planner import plan
from src.usecase.agents.executor import execute
from src.usecase.agents.chat_responder import build_chat_answer


class GraphState(TypedDict, total=False):
    prompt: str
    ctx: Dict[str, Any]
    history: List[Dict[str, Any]]
    steps: List[str]
    result: Any
    answer: str


def _planner(state: GraphState) -> GraphState:
    prompt = state.get("prompt", "") or ""
    history = state.get("history") or []
    steps = plan(prompt, history)
    return {"steps": steps}


def _executor(state: GraphState) -> GraphState:
    result = execute(state.get("steps") or [], state.get("ctx") or {})
    return {"result": result}


def _chat_responder(state: GraphState) -> GraphState:
    answer = build_chat_answer(
        prompt=state.get("prompt", "") or "",
        history=state.get("history") or [],
        result=state.get("result"),
    )
    return {"answer": answer}


def build_graph(checkpointer: Optional[object] = None):
    g = StateGraph(GraphState)
    g.add_node("planner", _planner)
    g.add_node("executor", _executor)
    g.add_node("chat_responder", _chat_responder)

    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")
    g.add_edge("executor", "chat_responder")
    g.add_edge("chat_responder", END)

    if checkpointer is None:
        return g.compile()
    return g.compile(checkpointer=checkpointer)