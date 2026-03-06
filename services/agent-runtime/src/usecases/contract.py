from __future__ import annotations

from typing import Any, Dict

from src.platform.langgraph_runner import LangGraphRunner
from src.graph.build_graph import build_graph

runner = LangGraphRunner(build_graph)


def execute(prompt: str, ctx: Dict[str, Any]) -> Any:
    out = runner.run(prompt, ctx)

    # build_graph returns {"answer": "..."} at the end
    if isinstance(out, dict) and "answer" in out:
        return {"answer": out["answer"]}

    # fallback (shouldn't happen)
    return {"answer": str(out)}