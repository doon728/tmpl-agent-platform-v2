from __future__ import annotations

from typing import List, Dict, Any
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


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

    system = SystemMessage(
        content=(
            "You are a care management planner.\n"
            "Your job is to choose the NEXT tool call.\n\n"
            "Allowed tool outputs format (return EXACTLY one line):\n"
            "- get_assessment_summary: <assessment_id>\n"
            "- get_member_summary: <member_id>\n"
            "- write_case_note: <case_id> | <note>\n"
            "- search_kb: <query>\n\n"
            "Rules:\n"
            "1. If the current user message refers to something discussed earlier, use conversation history.\n"
            "2. If the user asks follow-up questions like 'what was the risk level', 'what member was that', "
            "'summarize that assessment again', infer the most recent assessment_id or member_id from history.\n"
            "3. Prefer get_assessment_summary if the discussion is about an assessment.\n"
            "4. Prefer get_member_summary if the discussion is about a member.\n"
            "5. Only use search_kb for policy/guideline/coverage questions or when no assessment/member context exists.\n"
            "6. For write_case_note, only return write_case_note if the user explicitly asks to write/add/update a note.\n"
            "7. Return only one tool line. No explanation."
        )
    )

    human = HumanMessage(
        content=(
            f"Conversation history:\n{history_text or '(none)'}\n\n"
            f"Current user message:\n{p}\n\n"
            "Return the next tool call."
        )
    )

    resp = llm.invoke([system, human]).content.strip()

    # Basic safety fallback
    if not resp or ":" not in resp:
        return [f"search_kb: {p}"]

    return [resp]