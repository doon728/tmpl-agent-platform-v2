from __future__ import annotations

from pathlib import Path
import shutil
import yaml

from .models import CreateRepoRequest, CreateRepoResponse


# Template repo mounted into container
CURRENT_REPO_ROOT = Path("/app/template-repo")

# Output location (mounted from host)
GENERATED_REPOS_ROOT = Path("/workspace/generated-repos")


def _build_usecase_yaml(payload: CreateRepoRequest) -> dict:
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


def _build_prompts_yaml(payload: CreateRepoRequest) -> dict:
    return {
        "planner_system_prompt": payload.prompts.planner_system_prompt,
        "responder_system_prompt": payload.prompts.responder_system_prompt,
    }


def _copy_template_repo(target_repo_root: Path) -> None:
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

        if item.name.startswith("__"):
            continue

        if item.name == keep_usecase:
            continue

        shutil.rmtree(item)


def _create_usecase_files(target_repo_root: Path, payload: CreateRepoRequest) -> None:
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


def create_repo(payload: CreateRepoRequest) -> CreateRepoResponse:
    GENERATED_REPOS_ROOT.mkdir(parents=True, exist_ok=True)

    target_repo_root = GENERATED_REPOS_ROOT / payload.repo_name

    _copy_template_repo(target_repo_root)
    _remove_factory_service(target_repo_root)
    _remove_default_usecases(target_repo_root, payload.usecase_name)
    _create_usecase_files(target_repo_root, payload)

    return CreateRepoResponse(
        ok=True,
        repo_name=payload.repo_name,
        usecase_name=payload.usecase_name,
        status="generated_local_repo",
        repo_url=str(target_repo_root),
    )