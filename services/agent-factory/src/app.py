from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from .models import CreateApplicationRequest, CreateApplicationResponse
from .service import create_application

app = FastAPI(title="Agent Factory", version="v1")


@app.get("/health")
def health():
    return {"ok": True, "service": "agent-factory"}


@app.post("/create-application", response_model=CreateApplicationResponse)
def create_application_endpoint(payload: CreateApplicationRequest):
    try:
        result = create_application(payload)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))