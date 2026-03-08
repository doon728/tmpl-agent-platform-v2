from __future__ import annotations

from pathlib import Path
import shutil
import yaml

from .models import (
    AgentCreateConfig,
    AgentSpec,
    AppRepoConfig,
    CreateApplicationRequest,
    CreateApplicationResponse,
    CreatedAgentResult,
)

# Current template repo mounted into container
CURRENT_REPO_ROOT = Path("/app/template-repo")

# Output location (mounted from host)
GENERATED_REPOS_ROOT = Path("/workspace/generated-repos")

def _remove_agent_runtime(target_repo_root: Path) -> None:
    runtime_dir = target_repo_root / "services" / "agent-runtime"
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)

def _build_usecase_yaml(payload: AgentCreateConfig) -> dict:
    return {
        "name": payload.usecase_name,
        "agent_type": payload.agent_type,
        "persona": payload.persona,
        "tool_policy": payload.tool_policy.model_dump(),
        "rag": payload.rag.model_dump(),
        "model": payload.model.model_dump(),
        "approval": payload.approval.model_dump(),
        "memory": payload.memory.model_dump(),
        "embeddings": payload.embeddings.model_dump(),
        "chunking": payload.chunking.model_dump(),
        "document_ingestion": payload.document_ingestion.model_dump(),
    }


def _build_prompts_yaml(payload: AgentCreateConfig) -> dict:
    return {
        "planner_system_prompt": payload.prompts.planner_system_prompt,
        "responder_system_prompt": payload.prompts.responder_system_prompt,
    }


def _copy_repo_skeleton(target_repo_root: Path) -> None:
    if target_repo_root.exists():
        raise RuntimeError(f"Target repo already exists: {target_repo_root}")

    shutil.copytree(
        CURRENT_REPO_ROOT,
        target_repo_root,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            "*.pyc",
            ".venv",
            "node_modules",
            "generated-repos",
        ),
    )


def _remove_factory_service(target_repo_root: Path) -> None:
    factory_dir = target_repo_root / "services" / "agent-factory"
    if factory_dir.exists():
        shutil.rmtree(factory_dir)


def _remove_tool_gateway(target_repo_root: Path) -> None:
    gateway_dir = target_repo_root / "services" / "tool-gateway"
    if gateway_dir.exists():
        shutil.rmtree(gateway_dir)


def _remove_ui(target_repo_root: Path) -> None:
    ui_dir = target_repo_root / "services" / "ui"
    if ui_dir.exists():
        shutil.rmtree(ui_dir)


def _remove_demo_assets(target_repo_root: Path) -> None:
    for rel in [
        "data",
        "docs",
        "state",
        "services/state",
        "generated-repos",
    ]:
        p = target_repo_root / rel
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


def _remove_default_usecases(target_repo_root: Path, keep_usecase: str) -> None:
    usecases_root = (
        target_repo_root
        / "services"
        / "agent-runtime"
        / "src"
        / "usecases"
    )

    if not usecases_root.exists():
        return

    for item in usecases_root.iterdir():
        if not item.is_dir():
            continue

        # keep developer example
        if item.name == "cm_assistant":
            continue

        # keep new generated usecase
        if item.name == keep_usecase:
            continue

        shutil.rmtree(item)


def _remove_app_repo_extras(target_repo_root: Path) -> None:
    for rel in [
        "AGENT_FACTORY_TARGET_DESIGN.md",
        "infra",
        "packages",
        "services/shared",
        ".env",
        "docker-compose.yml",
    ]:
        p = target_repo_root / rel
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

def _create_usecase_files(target_repo_root: Path, payload: AgentCreateConfig) -> None:
    usecase_dir = (
        target_repo_root
        / "services"
        / "agent-runtime"
        / "src"
        / "usecases"
        / payload.usecase_name
    )

    usecase_dir.mkdir(parents=True, exist_ok=True)
    (usecase_dir / "__init__.py").write_text("", encoding="utf-8")

    with open(usecase_dir / "usecase.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            _build_usecase_yaml(payload),
            f,
            sort_keys=False,
            allow_unicode=True,
        )

    with open(usecase_dir / "prompts.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            _build_prompts_yaml(payload),
            f,
            sort_keys=False,
            allow_unicode=True,
        )


def _build_app_agents_config(payload: CreateApplicationRequest) -> dict:
    agents = []

    for agent in payload.agents:
        if agent.mode == "reuse_existing":
            agents.append(
                {
                    "agent_name": agent.agent_name,
                    "agent_type": agent.agent_type,
                    "mode": agent.mode,
                    "capabilities": agent.capabilities,
                    "existing_agent_repo": agent.existing_agent_repo,
                    "existing_agent_endpoint": agent.existing_agent_endpoint,
                    "endpoint": agent.existing_agent_endpoint or "TBD",
                }
            )
        else:
            create_cfg = agent.create_config
            if not create_cfg:
                raise RuntimeError(f"Missing create_config for agent: {agent.agent_name}")

            agents.append(
                {
                    "agent_name": agent.agent_name,
                    "agent_type": agent.agent_type,
                    "mode": agent.mode,
                    "capabilities": agent.capabilities,
                    "repo_name": create_cfg.repo_name,
                    "usecase_name": create_cfg.usecase_name,
                    "endpoint": "TBD",
                }
            )

    return {
        "industry": payload.industry,
        "tool_gateway": {
            "name": f"{payload.industry}-tool-gateway",
            "endpoint": "TBD",
        },
        "app_name": payload.app.app_name,
        "agents": agents,
    }

def _create_app_repo(app: AppRepoConfig, payload: CreateApplicationRequest) -> Path:
    target_repo_root = GENERATED_REPOS_ROOT / app.repo_name

    _copy_repo_skeleton(target_repo_root)
    _remove_factory_service(target_repo_root)
    _remove_tool_gateway(target_repo_root)
    _remove_agent_runtime(target_repo_root)
    _remove_demo_assets(target_repo_root)
    _remove_app_repo_extras(target_repo_root)

    # App repo keeps UI, but does not need agent-runtime source as the main artifact.
    # Keep current structure for now to avoid over-refactoring in one step.
    app_config_dir = target_repo_root / "app-config"
    app_config_dir.mkdir(parents=True, exist_ok=True)

    with open(app_config_dir / "agents.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            _build_app_agents_config(payload),
            f,
            sort_keys=False,
            allow_unicode=True,
        )

    return target_repo_root


def _create_agent_repo(create_cfg: AgentCreateConfig) -> Path:
    target_repo_root = GENERATED_REPOS_ROOT / create_cfg.repo_name

    _copy_repo_skeleton(target_repo_root)
    _remove_factory_service(target_repo_root)
    _remove_tool_gateway(target_repo_root)
    _remove_ui(target_repo_root)
    _remove_demo_assets(target_repo_root)
    _remove_default_usecases(target_repo_root, create_cfg.usecase_name)
    _create_usecase_files(target_repo_root, create_cfg)

    return target_repo_root


def create_application(payload: CreateApplicationRequest) -> CreateApplicationResponse:
    GENERATED_REPOS_ROOT.mkdir(parents=True, exist_ok=True)

    app_repo_root = _create_app_repo(payload.app, payload)

    agent_results: list[CreatedAgentResult] = []

    for agent in payload.agents:
        if agent.mode == "reuse_existing":
            agent_results.append(
                CreatedAgentResult(
                    agent_name=agent.agent_name,
                    agent_type=agent.agent_type,
                    mode=agent.mode,
                    existing_agent_repo=agent.existing_agent_repo,
                    existing_agent_endpoint=agent.existing_agent_endpoint,
                    status="reused_existing_agent",
                )
            )
            continue

        if not agent.create_config:
            raise RuntimeError(f"Missing create_config for agent: {agent.agent_name}")

        agent_repo_root = _create_agent_repo(agent.create_config)

        agent_results.append(
            CreatedAgentResult(
                agent_name=agent.agent_name,
                agent_type=agent.agent_type,
                mode=agent.mode,
                repo_name=agent.create_config.repo_name,
                repo_url=str(agent_repo_root),
                status="generated_local_agent_repo",
            )
        )

    return CreateApplicationResponse(
        ok=True,
        industry=payload.industry,
        app_repo_name=payload.app.repo_name,
        app_repo_url=str(app_repo_root),
        agents=agent_results,
        status="application_generated",
    )
