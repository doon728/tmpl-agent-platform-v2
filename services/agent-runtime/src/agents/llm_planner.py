from __future__ import annotations

import importlib
import os
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.platform.config import load_config

cfg = load_config()
USECASE = cfg.app.active_usecase

prompts_module = importlib.import_module(f"src.usecases.{USECASE}.prompts")
PLANNER_SYSTEM_PROMPT = prompts_module.PLANNER_SYSTEM_PROMPT


def plan(prompt: str, history: List[Dict[str, Any]]) -> List[str]:
    p = (prompt or "").strip()
    if not p:
        return ["search_kb: "]

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)

    history_text = ""
    for m in history[-8:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if content:
            history_text += f"{role.upper()}: {content}\n"

    system = SystemMessage(content=PLANNER_SYSTEM_PROMPT)

    human = HumanMessage(
        content=(
            f"Conversation history:\n{history_text or '(none)'}\n\n"
            f"Current user message:\n{p}\n\n"
            "Return the next tool call."
        )
    )

    resp = llm.invoke([system, human]).content.strip()

    if not resp or ":" not in resp:
        return [f"search_kb: {p}"]

    return [resp]