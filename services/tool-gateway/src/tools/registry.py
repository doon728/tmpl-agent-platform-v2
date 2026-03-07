from __future__ import annotations

from typing import Callable, Dict, Type, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from src.data.synth_store import store
from src.rag.retriever import retrieve

import os
import json
from datetime import datetime, timezone


class ToolSpec(BaseModel):
    name: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]
    primary_arg: str = "query"

    model_config = ConfigDict(arbitrary_types_allowed=True)


# -----------------------
# Tool schemas
# -----------------------

class SearchKBInput(BaseModel):
    query: str


class SearchKBResult(BaseModel):
    id: str
    title: str
    score: float
    snippet: str


class SearchKBOutput(BaseModel):
    results: list[SearchKBResult]


class GetMemberInput(BaseModel):
    member_id: str


class Member(BaseModel):
    member_id: str
    first_name: str
    last_name: str
    dob: str
    plan: str


class GetMemberOutput(BaseModel):
    member: Member | None


class WriteCaseNoteInput(BaseModel):
    case_id: str
    note: str


class WriteCaseNoteOutput(BaseModel):
    written: bool
    note_id: str | None


# -----------------------
# Synthetic data tools
# -----------------------

class GetMemberSummaryInput(BaseModel):
    member_id: str = Field(..., description="Member ID like m-000001")


class GetMemberSummaryOutput(BaseModel):
    found: bool
    member_id: str
    data: Optional[dict[str, Any]] = None


def get_member_summary_handler(inp: GetMemberSummaryInput) -> GetMemberSummaryOutput:
    result = store().get_member_summary(inp.member_id)

    if not result.get("found"):
        return GetMemberSummaryOutput(
            found=False,
            member_id=inp.member_id,
            data=None
        )

    return GetMemberSummaryOutput(
        found=True,
        member_id=inp.member_id,
        data=result
    )


class GetAssessmentSummaryInput(BaseModel):
    assessment_id: str = Field(..., description="Assessment ID like asmt-000001")


class GetAssessmentSummaryOutput(BaseModel):
    found: bool
    assessment_id: str
    data: Optional[dict[str, Any]] = None


def get_assessment_summary_handler(inp: GetAssessmentSummaryInput) -> GetAssessmentSummaryOutput:
    result = store().get_assessment_summary(inp.assessment_id)

    if not result.get("found"):
        return GetAssessmentSummaryOutput(
            found=False,
            assessment_id=inp.assessment_id,
            data=None
        )

    return GetAssessmentSummaryOutput(
        found=True,
        assessment_id=inp.assessment_id,
        data=result
    )


# -----------------------
# Tool handlers
# -----------------------

def search_kb_handler(inp: SearchKBInput) -> SearchKBOutput:
    q = (inp.query or "").strip()
    if not q:
        return SearchKBOutput(results=[])

    results = retrieve(q, top_k=3)

    return SearchKBOutput(
        results=[
            SearchKBResult(
                id=r.get("id", "doc-unknown"),
                title=r.get("title", "KB Doc"),
                score=float(r.get("score", 0.0)),
                snippet=r.get("snippet", ""),
            )
            for r in results
        ]
    )


def get_member_handler(inp: GetMemberInput) -> GetMemberOutput:
    member_id = (inp.member_id or "").strip()

    if not member_id:
        return GetMemberOutput(member=None)

    return GetMemberOutput(
        member=Member(
            member_id=member_id,
            first_name="Jane",
            last_name="Doe",
            dob="1990-01-01",
            plan="SamplePlan",
        )
    )


def write_case_note_handler(inp: WriteCaseNoteInput) -> WriteCaseNoteOutput:
    case_id = (inp.case_id or "").strip()
    note = (inp.note or "").strip()

    if not case_id or not note:
        return WriteCaseNoteOutput(written=False, note_id=None)

    member_id = ""

    try:
        a = store().assessments_by_id.get(case_id, {})
        member_id = (a.get("member_id") or "").strip()
    except Exception:
        member_id = ""

    out_path = os.getenv("RUNTIME_NOTES_PATH", "/app/state/written_case_notes.jsonl")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    note_id = f"note-{int(datetime.now(timezone.utc).timestamp())}"

    record = {
        "note_id": note_id,
        "member_id": member_id,
        "assessment_id": case_id,
        "author": "nurse-001",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note_text": note,
    }

    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return WriteCaseNoteOutput(written=True, note_id=note_id)


# -----------------------
# Registry
# -----------------------

TOOL_REGISTRY: Dict[str, ToolSpec] = {

    "search_kb": ToolSpec(
        name="search_kb",
        description="Search the knowledge base for relevant documents.",
        input_model=SearchKBInput,
        output_model=SearchKBOutput,
        handler=search_kb_handler,
        primary_arg="query",
    ),

    "get_member": ToolSpec(
        name="get_member",
        description="Fetch a member record by member_id.",
        input_model=GetMemberInput,
        output_model=GetMemberOutput,
        handler=get_member_handler,
        primary_arg="member_id",
    ),

    "write_case_note": ToolSpec(
        name="write_case_note",
        description="Write a note to a case record.",
        input_model=WriteCaseNoteInput,
        output_model=WriteCaseNoteOutput,
        handler=write_case_note_handler,
        primary_arg="note",
    ),

    "get_member_summary": ToolSpec(
        name="get_member_summary",
        description="Return member profile + care plans + latest assessment + recent claims/auths.",
        input_model=GetMemberSummaryInput,
        output_model=GetMemberSummaryOutput,
        handler=get_member_summary_handler,
        primary_arg="member_id",
    ),

    "get_assessment_summary": ToolSpec(
        name="get_assessment_summary",
        description="Return assessment(case) + responses + flagged answers + recent case notes.",
        input_model=GetAssessmentSummaryInput,
        output_model=GetAssessmentSummaryOutput,
        handler=get_assessment_summary_handler,
        primary_arg="assessment_id",
    ),
}