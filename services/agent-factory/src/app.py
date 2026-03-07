from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from .models import CreateRepoRequest, CreateRepoResponse
from .service import create_repo

app = FastAPI(title="Agent Factory", version="v1")


@app.get("/health")
def health():
    return {"ok": True, "service": "agent-factory"}


@app.post("/create-repo", response_model=CreateRepoResponse)
def create_repo_endpoint(payload: CreateRepoRequest):
    try:
        result = create_repo(payload)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))