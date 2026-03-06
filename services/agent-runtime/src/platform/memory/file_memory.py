from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from src.platform.memory.memory_interface import MemoryService


class InMemoryService(MemoryService):
    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def _key(self, scope: str, tenant_id: str, key: str) -> str:
        return f"{scope}::{tenant_id}::{key}"

    def get_history(
        self,
        *,
        scope: str,
        tenant_id: str,
        key: str,
    ) -> List[Dict[str, Any]]:
        return list(self._store.get(self._key(scope, tenant_id, key), []))

    def append(
        self,
        *,
        scope: str,
        tenant_id: str,
        key: str,
        role: str,
        content: str,
    ) -> None:
        k = self._key(scope, tenant_id, key)
        self._store.setdefault(k, []).append({"role": role, "content": content})


class AgentCoreMemoryService(MemoryService):
    def get_history(
        self,
        *,
        scope: str,
        tenant_id: str,
        key: str,
    ) -> List[Dict[str, Any]]:
        raise RuntimeError("AgentCore memory backend not implemented yet")

    def append(
        self,
        *,
        scope: str,
        tenant_id: str,
        key: str,
        role: str,
        content: str,
    ) -> None:
        raise RuntimeError("AgentCore memory backend not implemented yet")


_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _service
    if _service is not None:
        return _service

    backend = (os.getenv("MEMORY_BACKEND", "local") or "local").strip().lower()

    if backend == "local":
        _service = InMemoryService()
        return _service

    if backend == "agentcore":
        _service = AgentCoreMemoryService()
        return _service

    raise RuntimeError(f"Unknown MEMORY_BACKEND: {backend}")


THREAD_FILE = Path("./state/chat_threads.jsonl")


def _ensure_thread_file() -> None:
    THREAD_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not THREAD_FILE.exists():
        THREAD_FILE.write_text("")


def load_thread(thread_id: str) -> List[Dict[str, Any]]:
    _ensure_thread_file()
    history: List[Dict[str, Any]] = []

    with THREAD_FILE.open() as f:
        for line in f:
            row = json.loads(line)
            if row["thread_id"] == thread_id:
                history.append(row["message"])

    return history


def append_thread_message(thread_id: str, role: str, content: str) -> None:
    _ensure_thread_file()

    with THREAD_FILE.open("a") as f:
        f.write(
            json.dumps(
                {
                    "thread_id": thread_id,
                    "message": {
                        "role": role,
                        "content": content,
                    },
                }
            )
            + "\n"
        )
