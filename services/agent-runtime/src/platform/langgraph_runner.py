from __future__ import annotations

from typing import Any, Dict, List

from langgraph.checkpoint.memory import MemorySaver

from src.platform.memory import get_memory_service
from src.platform.observability.tracer import start_run, finish_run
from src.platform.usecase_config_loader import load_usecase_config
from src.platform.config import load_config
from src.platform.agent_types.registry import get_agent_graph_builder

memory = get_memory_service()


class LangGraphRunner:
    def __init__(self, build_graph_fn=None):
        self._build_graph_fn = build_graph_fn
        self._app = None
        self._loaded_agent_type = None

    def _get_checkpointer(self):
        return MemorySaver()

    def _ensure_app(self, agent_type: str):
        if self._app is None or self._loaded_agent_type != agent_type:
            checkpointer = self._get_checkpointer()
            builder = get_agent_graph_builder(agent_type)
            self._app = builder(checkpointer)
            self._loaded_agent_type = agent_type

    def run(self, prompt: str, ctx: Dict[str, Any]) -> Any:
        tenant_id = ctx.get("tenant_id") or "default-tenant"
        thread_id = ctx.get("thread_id") or "default-thread"
        case_id = ctx.get("case_id")

        # Start trace run
        run_id = start_run(
            agent="agent",
            thread_id=thread_id,
            prompt=prompt,
        )

        ctx["run_id"] = run_id

        # Load usecase configuration
        cfg = load_config()
        usecase_cfg = load_usecase_config(cfg.app.active_usecase)

        ctx["usecase_config"] = usecase_cfg.get("usecase", {})
        ctx["prompts_config"] = usecase_cfg.get("prompts", {})

        agent_type = ctx["usecase_config"].get("agent_type", "chat_agent")
        self._ensure_app(agent_type)

        thread_history: List[Dict[str, Any]] = memory.get_history(
            scope="thread",
            tenant_id=tenant_id,
            key=thread_id,
        )

        case_history: List[Dict[str, Any]] = []
        if case_id:
            case_history = memory.get_history(
                scope="case",
                tenant_id=tenant_id,
                key=case_id,
            )

        history = case_history + thread_history

        initial_state = {
            "prompt": prompt,
            "ctx": ctx,
            "history": history,
        }

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        out = self._app.invoke(initial_state, config=config)

        # Critical: preserve approval objects exactly as-is
        if isinstance(out, dict) and isinstance(out.get("result"), dict):
            inner = out["result"]
            if isinstance(inner, dict) and inner.get("result") == "APPROVAL_REQUIRED":
                result = inner
            else:
                result = out.get("answer") or out.get("result") or out
        elif isinstance(out, dict) and out.get("result") == "APPROVAL_REQUIRED":
            result = out
        else:
            result = out.get("answer") if isinstance(out, dict) else out
            if result is None:
                result = out

        memory.append(
            scope="thread",
            tenant_id=tenant_id,
            key=thread_id,
            role="user",
            content=prompt,
        )

        memory.append(
            scope="thread",
            tenant_id=tenant_id,
            key=thread_id,
            role="assistant",
            content=str(result),
        )

        if case_id:
            memory.append(
                scope="case",
                tenant_id=tenant_id,
                key=case_id,
                role="assistant",
                content=str(result),
            )

        # Finish trace run
        finish_run(run_id)

        return result