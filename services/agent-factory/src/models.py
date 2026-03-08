from __future__ import annotations

from typing import List, Literal, Optional
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


class AgentCreateConfig(BaseModel):
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


class AgentSpec(BaseModel):
    agent_name: str
    agent_type: str
    mode: Literal["create_new", "reuse_existing"] = "create_new"
    capabilities: List[str] = Field(default_factory=list)

    existing_agent_repo: Optional[str] = None
    existing_agent_endpoint: Optional[str] = None

    create_config: Optional[AgentCreateConfig] = None


class AppRepoConfig(BaseModel):
    repo_name: str
    app_name: str
    ui_type: str = "end_user_ui"


class CreateApplicationRequest(BaseModel):
    industry: str
    app: AppRepoConfig
    agents: List[AgentSpec] = Field(default_factory=list)


class CreatedAgentResult(BaseModel):
    agent_name: str
    agent_type: str
    mode: Literal["create_new", "reuse_existing"]
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    existing_agent_repo: Optional[str] = None
    existing_agent_endpoint: Optional[str] = None
    status: str
    capabilities: List[str] = Field(default_factory=list)



class CreateApplicationResponse(BaseModel):
    ok: bool = True
    industry: str
    app_repo_name: str
    app_repo_url: Optional[str] = None
    agents: List[CreatedAgentResult] = Field(default_factory=list)
    status: str = "application_generated"