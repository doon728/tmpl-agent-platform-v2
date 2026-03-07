from __future__ import annotations

import importlib
from typing import Any, Dict, List

from src.platform.config import load_config
from src.platform.llm.responder import generate_answer
from src.platform.observability.tracer import start_run, add_step, finish_run
from src.platform.tools.registry import registry


cfg = load_config()
USECASE = cfg.app.active_usecase

router_module = importlib.import_module(f"src.usecases.{USECASE}.router")
route_step = router_module.route_step


def _invoke_tool(tool_name: str, tool_input: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
    result = registry.invoke(tool_name, tool_input, ctx)

    if isinstance(result, dict) and result.get("approval_required"):
        return {"result": "APPROVAL_REQUIRED", "approval": result}

    return result


def execute(steps: List[str], ctx: Dict[str, Any]) -> Any:
    step = (steps[0] if steps else "").strip()
    ctx = dict(ctx or {})
    ctx["prompt"] = step if not ctx.get("prompt") else ctx["prompt"]

    print(f"[executor] planner_step={step}")

    run_id = start_run(
        agent=USECASE,
        thread_id=ctx.get("thread_id"),
        prompt=ctx.get("prompt", ""),
    )
    add_step(run_id, "planner", step)

    if not step:
        finish_run(run_id)
        return {"result": "OK", "answer": "No action planned."}

    plan = route_step(step, ctx, raw_prompt=ctx.get("prompt", step))
    mode = plan.get("mode")

    if mode == "direct_tool":
        tool = plan["tool"]
        tool_input = plan["input"]

        add_step(run_id, "tool_call", {"tool": tool, "input": tool_input})
        result = _invoke_tool(tool, tool_input, ctx)

        if isinstance(result, dict) and result.get("result") == "APPROVAL_REQUIRED":
            finish_run(run_id)
            return result

        add_step(run_id, "llm_response", {"tool": tool})
        answer = generate_answer(ctx.get("prompt", ""), tool, result)

        finish_run(run_id)
        return {
            "result": "OK",
            "mode": "DIRECT_TOOL",
            "answer": answer,
            "tool": tool,
            "input": tool_input,
            "output": result,
        }

    finish_run(run_id)
    return {"result": "OK", "answer": "Unhandled routing mode"}