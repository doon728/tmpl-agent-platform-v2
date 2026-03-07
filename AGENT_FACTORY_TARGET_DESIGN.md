# Agent Factory Target Design

## Goal
Keep the template repo generic so only use-case-specific config changes when a new agent is created.

## Platform Layer
Shared runtime code lives under:

- services/agent-runtime/src/platform/
- services/agent-runtime/src/platform/agent_types/

This includes:
- runtime
- graph engine
- planner/executor/responder framework
- tool bindings
- RAG
- memory
- observability
- approvals

## Agent Type Layer
Agent workflow patterns live under:

- services/agent-runtime/src/platform/agent_types/

Initial agent types:
- chat_agent
- summarizer_agent
- workflow_agent

Agent types define:
- graph structure
- node chain
- runtime behavior

## Use Case Layer
Use-case-specific files live under:

- services/agent-runtime/src/usecases/<usecase_name>/

Use cases should contain only:
- usecase.yaml
- prompts.yaml

Use cases define:
- name
- agent_type
- persona
- tools
- rag settings
- model settings
- approval settings
- prompts

## Rule
Platform code must never live under usecases.
Use cases configure behavior.
Agent types define workflows.
Platform provides shared runtime.

## Future
Developer UI will generate new use cases automatically by creating:
- usecase.yaml
- prompts.yaml

No manual platform code changes should be required for a new agent.