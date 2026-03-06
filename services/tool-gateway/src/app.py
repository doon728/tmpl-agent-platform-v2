from __future__ import annotations

from typing import Any, Dict, Optional, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from src.contract import (
    CONTRACT_VERSION,
    ok_response,
    err_response,
)

from src.tools.registry import TOOL_REGISTRY, ToolSpec

app = FastAPI(title="Tool Gateway", version=CONTRACT_VERSION)


# -----------------------
# Return envelope (not 422) on validation errors
# -----------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    tool_name = "<invalid>"
    try:
        body = await request.json()
        if isinstance(body, dict) and body.get("tool_name"):
            tool_name = body["tool_name"]
    except Exception:
        pass

    payload = err_response(
        tool_name=tool_name,
        code="VALIDATION_ERROR",
        message="Request validation failed",
    )
    payload["error"]["details"] = exc.errors()
    return JSONResponse(status_code=200, content=payload)


# -----------------------
# Request model (envelope stays stable)
# -----------------------
class ToolInvokeRequestModel(BaseModel):
    contract_version: str = CONTRACT_VERSION
    tool_name: str = Field(..., min_length=1)
    input: Dict[str, Any]
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


# -----------------------
# Minimal auth/context middleware (stub)
# -----------------------
@app.middleware("http")
async def log_context(request: Request, call_next: Callable):
    tenant_id = request.headers.get("x-tenant-id")
    user_id = request.headers.get("x-user-id")
    correlation_id = request.headers.get("x-correlation-id")

    print(
        f"[tool-gateway] {request.method} {request.url.path} "
        f"tenant={tenant_id} user={user_id} corr={correlation_id}"
    )

    return await call_next(request)


# -----------------------
# Endpoints
# -----------------------
@app.get("/health")
def health() -> dict:
    return {"ok": True, "contract_version": CONTRACT_VERSION}

@app.get("/tools/specs")
def list_tool_specs() -> dict:
    """
    Discovery endpoint so agent-runtime (or UI) can see what tools exist.
    """
    tools = []
    for name, spec in TOOL_REGISTRY.items():
        tools.append(
            {
                "name": spec.name,
                "description": spec.description,
                # derive primary arg from input model fields (first field)
                "primary_arg": spec.primary_arg,
            }
        )
    return {"ok": True, "contract_version": CONTRACT_VERSION, "tools": tools}


@app.post("/tools/invoke")
def invoke_tool(req: ToolInvokeRequestModel) -> dict:
    # Contract version check (agent + gateway must match)
    if req.contract_version != CONTRACT_VERSION:
        return err_response(
            tool_name=req.tool_name,
            code="CONTRACT_VERSION_MISMATCH",
            message=f"Expected {CONTRACT_VERSION}, got {req.contract_version}",
        )

    spec: ToolSpec | None = TOOL_REGISTRY.get(req.tool_name)
    if spec is None:
        return err_response(
            tool_name=req.tool_name,
            code="UNKNOWN_TOOL",
            message=f"Unknown tool: {req.tool_name}",
        )

    # Validate tool input against tool-specific schema
    try:
        typed_input = spec.input_model.model_validate(req.input)
    except ValidationError as e:
        payload = err_response(
            tool_name=req.tool_name,
            code="TOOL_INPUT_INVALID",
            message="Tool input validation failed",
        )
        payload["error"]["details"] = e.errors()
        return payload

    # Execute tool
    try:
        typed_output = spec.handler(typed_input)
    except Exception as e:
        return err_response(
            tool_name=req.tool_name,
            code="TOOL_EXECUTION_ERROR",
            message=str(e),
        )

    # Validate tool output schema (defensive)
    try:
        validated_output = spec.output_model.model_validate(typed_output)
    except ValidationError as e:
        payload = err_response(
            tool_name=req.tool_name,
            code="TOOL_OUTPUT_INVALID",
            message="Tool output validation failed",
        )
        payload["error"]["details"] = e.errors()
        return payload

    return ok_response(req.tool_name, validated_output.model_dump())


@app.post("/invocations")
async def invocations(request: Request) -> JSONResponse:
    """
    AgentCore container contract endpoint.

    Behavior:
    - If payload looks like ToolInvokeRequestModel ({tool_name, input, ...}), pass-through
    - Else, if payload has {prompt|text}, map it to a default tool "search_kb" with {query: ...}
    """
    # Try JSON first
    try:
        payload: Any = await request.json()
    except Exception:
        payload = None

    # Pass-through if already in tool-gateway format
    if isinstance(payload, dict) and "tool_name" in payload and "input" in payload:
        req = ToolInvokeRequestModel(**payload)
        return JSONResponse(content=invoke_tool(req))

    # Otherwise map a simple prompt/text to a default tool
    prompt = ""
    if isinstance(payload, dict):
        prompt = payload.get("prompt") or payload.get("text") or ""

    req = ToolInvokeRequestModel(
        tool_name="search_kb",
        input={"query": prompt},
    )
    return JSONResponse(content=invoke_tool(req))
