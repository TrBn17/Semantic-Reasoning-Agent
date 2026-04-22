from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.documents.parsers import build_document_parser
from semantic_reasoning_agent.documents.service import DocumentService
from semantic_reasoning_agent.infrastructure.graphiti import build_graphiti_gateway
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.infrastructure.ontology import OpenDomainLLMExtractor
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry, build_adapter_registry
from semantic_reasoning_agent.infrastructure.storage import build_object_store
from semantic_reasoning_agent.persistence.database import DatabaseManager, get_database_manager
from semantic_reasoning_agent.persistence.repositories.ontology_repo import OntologyRepository
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.agent_capability_service import AgentCapabilityService
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.knowledge_pack_service import KnowledgePackService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_service import OntologyService
from semantic_reasoning_agent.services.provider_models_service import ProviderModelsService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.secret_service import DatabaseSecretRepository, SecretService
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService
from semantic_reasoning_agent.services.tool_registry import ToolRegistry, build_tool_registry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime
from semantic_reasoning_agent.services.workflow_registry_service import WorkflowRegistryService
from semantic_reasoning_agent.tools.ontology.schema_registry import OntologySchemaRegistry
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    database_manager: DatabaseManager
    secret_service: SecretService
    agent_profile_service: AgentProfileService
    knowledge_pack_service: KnowledgePackService
    agent_capability_service: AgentCapabilityService
    model_config_service: ModelConfigService
    provider_models_service: ProviderModelsService
    adapter_registry: AdapterRegistry
    graphiti_gateway: GraphitiGateway
    retrieval_service: RetrievalService
    conversation_service: ConversationService
    task_dispatcher: TaskDispatcher
    document_service: DocumentService
    ontology_service: OntologyService
    tool_registry: ToolRegistry
    tool_runtime: ToolRuntime
    task_runtime_service: TaskRuntimeService
    workflow_registry_service: WorkflowRegistryService
    chat_stream_service: ChatStreamService
    runtime_audit_service: RuntimeAuditService


@lru_cache
def get_app_container() -> AppContainer:
    settings = get_settings()
    database_manager = get_database_manager()
    adapter_registry = AdapterRegistry()
    secret_service = SecretService(DatabaseSecretRepository(database_manager))
    agent_profile_service = AgentProfileService(database_manager, settings)
    knowledge_pack_service = KnowledgePackService(database_manager)
    provider_models_service = ProviderModelsService(settings)
    model_config_service = ModelConfigService(
        database_manager=database_manager,
        adapter_registry=adapter_registry,
        secret_service=secret_service,
        provider_models_service=provider_models_service,
        settings=settings,
    )
    try:
        adapter_registry.refresh(
            build_adapter_registry(
                settings,
                model_config_service=model_config_service,
                workspace_id=settings.default_workspace_id,
            ).adapters
        )
    except Exception:
        # During cold-start test bootstrap, schema may not exist yet.
        adapter_registry.refresh(build_adapter_registry(settings).adapters)
    graphiti_gateway = build_graphiti_gateway(settings)
    runtime_audit_service = RuntimeAuditService(database_manager)
    parser_registry = build_document_parser(settings)
    object_store = build_object_store(settings)
    retrieval_service = RetrievalService(settings, database_manager)
    conversation_service = ConversationService(
        database_manager,
        model_config_service,
        agent_profile_service,
        settings,
    )
    task_dispatcher = TaskDispatcher()
    document_service = DocumentService(
        settings,
        parser_registry,
        retrieval_service,
        database_manager,
        task_dispatcher,
        object_store=object_store,
    )
    ontology_repository = OntologyRepository(database_manager)
    schema_registry = OntologySchemaRegistry(ontology_repository)
    ontology_service = OntologyService(
        settings,
        database_manager,
        task_dispatcher,
        graphiti_gateway,
        ontology_extractor=OpenDomainLLMExtractor(
            settings=settings,
            model_config_service=model_config_service,
            schema_registry=schema_registry,
            adapter_registry=adapter_registry,
        ),
    )
    tool_registry = build_tool_registry(
        retrieval_service=retrieval_service,
        ontology_service=ontology_service,
        graphiti_gateway=graphiti_gateway,
    )
    tool_runtime = ToolRuntime(tool_registry)
    agent_capability_service = AgentCapabilityService(tool_registry)
    task_runtime_service = TaskRuntimeService(
        settings=settings,
        model_config_service=model_config_service,
        adapter_registry=adapter_registry,
        tool_runtime=tool_runtime,
        conversation_service=conversation_service,
        agent_profile_service=agent_profile_service,
        knowledge_pack_service=knowledge_pack_service,
        runtime_audit_service=runtime_audit_service,
    )
    workflow_registry_service = WorkflowRegistryService()
    chat_stream_service = ChatStreamService(
        conversation_service=conversation_service,
        model_config_service=model_config_service,
        task_runtime_service=task_runtime_service,
    )
    return AppContainer(
        settings=settings,
        database_manager=database_manager,
        secret_service=secret_service,
        agent_profile_service=agent_profile_service,
        knowledge_pack_service=knowledge_pack_service,
        agent_capability_service=agent_capability_service,
        model_config_service=model_config_service,
        provider_models_service=provider_models_service,
        adapter_registry=adapter_registry,
        graphiti_gateway=graphiti_gateway,
        retrieval_service=retrieval_service,
        conversation_service=conversation_service,
        task_dispatcher=task_dispatcher,
        document_service=document_service,
        ontology_service=ontology_service,
        tool_registry=tool_registry,
        tool_runtime=tool_runtime,
        task_runtime_service=task_runtime_service,
        workflow_registry_service=workflow_registry_service,
        chat_stream_service=chat_stream_service,
        runtime_audit_service=runtime_audit_service,
    )
