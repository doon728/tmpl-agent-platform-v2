from __future__ import annotations

from typing import Any, Dict, List

from langgraph.checkpoint.memory import MemorySaver
from src.platform.memory import get_memory_service
from src.platform.memory import load_thread, append_thread_message

memory = get_memory_service()


class LangGraphRunner:
    def __init__(self, build_graph_fn):
        self._build_graph_fn = build_graph_fn
        self._app = None

    def _get_checkpointer(self):
        return MemorySaver()

    def _ensure_app(self):
        if self._app is None:
            checkpointer = self._get_checkpointer()
            self._app = self._build_graph_fn(checkpointer)

    def run(self, prompt: str, ctx: Dict[str, Any]) -> Any:
        self._ensure_app()

        tenant_id = ctx.get("tenant_id") or "default-tenant"
        user_id = ctx.get("user_id") or "default-user"
        thread_id = ctx.get("thread_id") or "default-thread"
        case_id = ctx.get("case_id")

        # ------------------------
        # 1️⃣ Load Thread History
        # ------------------------
        thread_history: List[Dict[str, Any]] = memory.get_history(
            scope="thread",
            tenant_id=tenant_id,
            key=thread_id,
        )

        # ------------------------
        # 2️⃣ Load Case History
        # ------------------------
        case_history: List[Dict[str, Any]] = []
        if case_id:
            case_history = memory.get_history(
                scope="case",
                tenant_id=tenant_id,
                key=case_id,
            )

        # Case history first, then thread history
        history = case_history + thread_history

        # ------------------------
        # 3️⃣ Invoke Graph
        # ------------------------
        initial_state = {
            "prompt": prompt,
            "ctx": ctx,
            "history": history,
        }

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        out = self._app.invoke(initial_state, config=config)
        result = out.get("answer") or out.get("result") or out

        # ------------------------
        # 4️⃣ Persist Thread Memory
        # ------------------------
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

        # ------------------------
        # 5️⃣ Persist Case Memory
        # ------------------------
        if case_id:
            memory.append(
                scope="case",
                tenant_id=tenant_id,
                key=case_id,
                role="assistant",
                content=str(result),
            )

        return result