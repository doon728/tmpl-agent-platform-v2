from __future__ import annotations

import os
import json
from typing import Dict, List

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _format_tool_output(tool_name: str, tool_output: Dict) -> str:
    """
    Convert tool output into clean context for the LLM.
    """

    if tool_name == "search_kb":
        results: List[Dict] = tool_output.get("results", [])

        if not results:
            return "No relevant policy documents were found."

        parts = []

        for r in results[:3]:
            title = r.get("title", "Unknown Source")
            snippet = r.get("snippet", "")

            parts.append(
                f"""
Source: {title}

Policy Text:
{snippet}
""".strip()
            )

        return "\n\n---\n\n".join(parts)

    return json.dumps(tool_output, indent=2)


def generate_answer(user_prompt: str, tool_name: str, tool_output: Dict) -> str:
    print("[LLM] generating response", flush=True)

    tool_context = _format_tool_output(tool_name, tool_output)

    system_prompt = """
You are a healthcare care-management assistant helping nurses.

Rules:
- Use ONLY the provided policy information
- Do NOT invent facts
- Be concise and clinically useful
- If the policy does not contain the answer, say so
"""

    prompt = f"""
USER QUESTION:
{user_prompt}

RETRIEVED POLICY CONTEXT:
{tool_context}

Answer the question using ONLY the retrieved policy context.
"""

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.choices[0].message.content.strip()