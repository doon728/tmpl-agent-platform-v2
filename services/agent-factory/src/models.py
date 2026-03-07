from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ToolPolicyConfig(BaseModel):
    mode: str = "selected"
    allowed_tools: List[str] = Field(default_factory=list)
    allowed_tags: List[str] = Field(default_factory=list)


class RagConfig(BaseModel):
    enabled: bool = True
    top_k: int = 3
    score_threshold: float = 0.35


class ModelConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0


class ApprovalConfig(BaseModel):
    enabled: bool = True
    write_tools: List[str] = Field(default_factory=list)


class MemoryConfig(BaseModel):
    enabled: bool = True
    thread: bool = True
    case: bool = True
    long_term: bool = False


class EmbeddingsConfig(BaseModel):
    provider: str = "openai"
    model: str = "text-embedding-3-small"


class ChunkingConfig(BaseModel):
    strategy: str = "fixed"
    chunk_size: int = 500
    chunk_overlap: int = 100


class DocumentIngestionConfig(BaseModel):
    enabled: bool = True
    upload_via_ui: bool = True
    allowed_types: List[str] = Field(default_factory=lambda: ["txt", "pdf", "docx"])
    auto_embed_on_upload: bool = True


class PromptsConfig(BaseModel):
    planner_system_prompt: str
    responder_system_prompt: str


class CreateRepoRequest(BaseModel):
    repo_name: str
    usecase_name: str
    agent_type: str
    persona: str

    tool_policy: ToolPolicyConfig = Field(default_factory=ToolPolicyConfig)

    rag: RagConfig = Field(default_factory=RagConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    approval: ApprovalConfig = Field(default_factory=ApprovalConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    document_ingestion: DocumentIngestionConfig = Field(default_factory=DocumentIngestionConfig)

    prompts: PromptsConfig


class CreateRepoResponse(BaseModel):
    ok: bool = True
    repo_name: str
    usecase_name: str
    status: str
    repo_url: Optional[str] = None