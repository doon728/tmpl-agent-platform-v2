from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.chat_responder import build_chat_answer
from src.agents.executor import execute
from src.agents.llm_planner import plan


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


def _after_executor(state: GraphState) -> str:
    result = state.get("result")
    if isinstance(result, dict) and result.get("result") == "APPROVAL_REQUIRED":
        return "end"
    return "chat_responder"


def _chat_responder(state: GraphState) -> GraphState:
    result = state.get("result")

    # If executor already produced final text, do not re-wrap it
    if isinstance(result, dict) and isinstance(result.get("answer"), str):
        return {"answer": result["answer"]}

    answer = build_chat_answer(
        prompt=state.get("prompt", "") or "",
        history=state.get("history") or [],
        result=result,
    )
    return {"answer": answer}


def build_graph(checkpointer: Optional[object] = None):
    g = StateGraph(GraphState)
    g.add_node("planner", _planner)
    g.add_node("executor", _executor)
    g.add_node("chat_responder", _chat_responder)

    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")

    g.add_conditional_edges(
        "executor",
        _after_executor,
        {
            "chat_responder": "chat_responder",
            "end": END,
        },
    )

    g.add_edge("chat_responder", END)

    if checkpointer is None:
        return g.compile()
    return g.compile(checkpointer=checkpointer)