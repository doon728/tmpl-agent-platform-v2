from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.platform.tools.registry import registry


# --- MVP: natural nurse routing helpers ---
MEMBER_ID_RE = re.compile(r"\b(m-\d{6})\b", re.IGNORECASE)
ASMT_ID_RE = re.compile(r"\b(asmt-\d{6})\b", re.IGNORECASE)

POLICY_KWS = [
    "policy",
    "guideline",
    "coverage",
    "medical necessity",
    "prior auth",
    "prior authorization",
    "denial",
    "denied",
    "criteria",
    "pended",
]

SUMMARY_KWS = [
    "summarize",
    "summary",
    "what did we decide",
    "confirm",
    "recorded",
    "did we write",
    "case note",
    "note recorded",
]
def _has_summary_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in SUMMARY_KWS)

def _has_policy_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in POLICY_KWS)

def _extract_ids(text: str) -> Tuple[Optional[str], Optional[str]]:
    t = text or ""
    m = MEMBER_ID_RE.search(t)
    a = ASMT_ID_RE.search(t)
    return (m.group(1) if m else None, a.group(1) if a else None)

def _build_policy_query(prompt: str, member_id: Optional[str], assessment_id: Optional[str]) -> str:
    parts = []
    if member_id:
        parts.append(f"member_id={member_id}")
    if assessment_id:
        parts.append(f"assessment_id={assessment_id}")
    parts.append(f"nurse_question={prompt.strip()}")
    return " | ".join(parts)

def _safe_get(d: Any, *path: str, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def _fmt_money(x: Any) -> str:
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return str(x)

def _format_member_summary(step1_output: Dict[str, Any]) -> str:
    # step1_output is the tool output from agent-runtime registry.invoke(tool,...)
    data = step1_output.get("data") if isinstance(step1_output, dict) else None
    if not isinstance(data, dict) or not data.get("found"):
        return "Member summary: not found."

    member = data.get("member", {}) or {}
    pcp = data.get("pcp", {}) or {}
    claims = data.get("recent_claims", []) or []
    auths = data.get("recent_auths", []) or []

    # Denied/pended highlights
    denied = [c for c in claims if (c.get("status") == "DENIED")]
    pended = [c for c in claims if (c.get("status") == "PENDED")]

    lines = []
    lines.append(
        f"Member {member.get('member_id')} — {member.get('first_name','')} {member.get('last_name','')} "
        f"(DOB {member.get('dob')}, State {member.get('state')}, Plan {member.get('plan_id')})"
    )
    lines.append(
        f"PCP: {pcp.get('provider_name','N/A')} ({pcp.get('specialty','')}) | Network={pcp.get('network_status','')}"
    )
    lines.append(f"Risk score: {member.get('risk_score','')} | Chronic: {member.get('chronic_conditions','') or 'None listed'}")

    # Recent activity summary
    if claims:
        most_recent = claims[0]
        lines.append(
            f"Most recent claim: {most_recent.get('claim_id')} {most_recent.get('claim_type')} "
            f"{most_recent.get('service_from_date')} status={most_recent.get('status')} "
            f"total={_fmt_money(most_recent.get('total_amount'))} paid={_fmt_money(most_recent.get('paid_amount'))}"
        )
    if auths:
        a = auths[0]
        lines.append(
            f"Most recent auth: {a.get('auth_id')} {a.get('service_type')} {a.get('request_date')} status={a.get('status')}"
        )

    # Denied/pended callouts
    if denied or pended:
        lines.append("Claims requiring attention:")
        for c in (denied + pended)[:5]:
            lines.append(
                f"- {c.get('claim_id')} {c.get('claim_type')} {c.get('service_from_date')} "
                f"status={c.get('status')} total={_fmt_money(c.get('total_amount'))}"
            )
    else:
        lines.append("No DENIED/PENDED claims found in the last 10 claims.")

    return "\n".join(lines)

def _format_assessment_summary(step1_output: Dict[str, Any]) -> str:
    data = step1_output.get("data") if isinstance(step1_output, dict) else None
    if not isinstance(data, dict) or not data.get("found"):
        return "Assessment summary: not found."

    a = data.get("assessment", {}) or {}
    member = data.get("member", {}) or {}
    care_plan = data.get("care_plan", {}) or {}
    flagged = data.get("flagged_responses", []) or []
    notes = data.get("recent_case_notes", []) or []

    # Simple “risk drivers” extraction (MVP)
    risk_drivers = []
    for r in flagged[:5]:
        dom = r.get("domain")
        q = r.get("question_text")
        ans = r.get("answer_value")
        risk_drivers.append(f"[{dom}] {q} => {ans}")

    # Simple “next actions” suggestions (rule-based, MVP)
    next_actions = []
    overall = (a.get("overall_risk_level") or "").upper()
    if overall in ("HIGH", "MEDIUM"):
        next_actions.append("Review flagged assessment responses and confirm care plan barriers.")
        next_actions.append("Check for any missing documentation tied to pended/denied items.")
        next_actions.append("Consider outreach: schedule follow-up touchpoint within 7–14 days.")
    else:
        next_actions.append("Continue routine monitoring; confirm next scheduled touchpoint.")

    if notes:
        next_actions.append("Update case note with summary + actions (requires approval).")

    lines = []
    lines.append(
        f"Assessment {a.get('assessment_id')} — {a.get('assessment_type')} status={a.get('status')} "
        f"priority={a.get('priority')} risk={a.get('overall_risk_level')}"
    )
    lines.append(
        f"Member {member.get('member_id')} — {member.get('first_name','')} {member.get('last_name','')} "
        f"(DOB {member.get('dob')}, State {member.get('state')}, Plan {member.get('plan_id')})"
    )
    lines.append(f"Care plan: {care_plan.get('program','')} (status={care_plan.get('status','')})")
    lines.append(f"Summary: {a.get('summary','')}")

    if risk_drivers:
        lines.append("Key risk drivers:")
        for x in risk_drivers:
            lines.append(f"- {x}")
    else:
        lines.append("Key risk drivers: none flagged.")

    if notes:
        n = notes[0]
        lines.append(f"Latest case note ({n.get('created_at')} by {n.get('author')}): {n.get('note_text')}")
    else:
        lines.append("Latest case note: none.")

    lines.append("Recommended next actions:")
    for act in next_actions[:5]:
        lines.append(f"- {act}")

    return "\n".join(lines)

def _format_policy_snippets(step2_output: Dict[str, Any]) -> str:
    # search_kb output is like {"results":[{id,title,score,snippet},...]}
    results = step2_output.get("results") if isinstance(step2_output, dict) else None
    if not isinstance(results, list) or not results:
        return "Policy/guidance: no snippets found."

    lines = ["Policy / coverage guidance (top matches):"]
    for r in results[:3]:
        lines.append(f"- {r.get('title','Doc')} (score {r.get('score')}): {r.get('snippet')}")
    return "\n".join(lines)


def execute(steps: List[str], ctx: Dict[str, Any]) -> Any:
    step = steps[0] if steps else ""
    step = (step or "").strip()
    print(f"[executor] planner_step={step}")

    # -----------------------------
    # MVP Option B: 2-step execution
    # summary (member/assessment) + policy lookup
    # -----------------------------
    member_id, assessment_id = _extract_ids(step)
    # IMPORTANT: explicit tool calls must win (especially write_case_note)
    is_explicit_write = step.lower().startswith("write_case_note:")

    if (not is_explicit_write) and ( (_has_policy_intent(step) or _has_summary_intent(step)) ) and (member_id or assessment_id):

    
        # Step 1: fetch context
        if assessment_id:
            t1_name = "get_assessment_summary"
            t1_input = {"assessment_id": assessment_id}
        else:
            t1_name = "get_member_summary"
            t1_input = {"member_id": member_id}

        t1 = registry.invoke(t1_name, t1_input, ctx)

        if isinstance(t1, dict) and t1.get("approval_required"):
            return {"result": "APPROVAL_REQUIRED", "approval": t1}

        # Step 2: policy lookup (MVP uses search_kb; later swap to RAG policy tool)
        policy_query = _build_policy_query(step, member_id, assessment_id)
        t2 = registry.invoke("search_kb", {"query": policy_query}, ctx)

        if isinstance(t2, dict) and t2.get("approval_required"):
            return {"result": "APPROVAL_REQUIRED", "approval": t2}

        # Nurse-friendly text
        if t1_name == "get_member_summary":
            summary_text = _format_member_summary(t1)
        else:
            summary_text = _format_assessment_summary(t1)

        policy_text = _format_policy_snippets(t2)

        return {
            "result": "OK",
            "mode": "TWO_STEP",
            "nurse_summary": summary_text,
            "policy_summary": policy_text,
            "step1": {"tool": t1_name, "input": t1_input, "output": t1},
            "step2": {"tool": "search_kb", "input": {"query": policy_query}, "output": t2},
        }

    # -----------------------------
    # Existing behavior (unchanged)
    # -----------------------------
    # Parse tool_name + payload
    if ":" in step:
        tool_name, tool_value = step.split(":", 1)
        tool_name = tool_name.strip()
        tool_value = tool_value.strip()
    else:
        # Default tool if planner didn't specify one
        tool_name = "search_kb"
        tool_value = step

    if not tool_value:
        return {"results": []}

    # Look up tool spec (discovered tools have primary_arg set)
    spec = registry.get_spec(tool_name)

    # Build tool_input
    # 1) Special-case multi-arg tools
    if tool_name == "write_case_note":
        # Expect: "case_id | note"
        if "|" not in tool_value:
            raise RuntimeError(
                "write_case_note requires: write_case_note: <case_id> | <note>"
            )
        case_id, note = [x.strip() for x in tool_value.split("|", 1)]
        tool_input = {"case_id": case_id, "note": note}

    # 2) All other tools treated as single-arg tools
    else:
        tool_input = {spec.primary_arg: tool_value}

    result = registry.invoke(tool_name, tool_input, ctx)

    if isinstance(result, dict) and result.get("approval_required"):
        return {"result": "APPROVAL_REQUIRED", "approval": result}

    return f"RESULTS: {result}"