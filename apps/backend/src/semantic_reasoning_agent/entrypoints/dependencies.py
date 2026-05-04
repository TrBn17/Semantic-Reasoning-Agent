from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.documents.service import DocumentService
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.agent_capability_service import AgentCapabilityService
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.knowledge_pack_service import KnowledgePackService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_graph_projection_service import (
    OntologyGraphProjectionService,
)
from semantic_reasoning_agent.services.ontology_service import OntologyService
from semantic_reasoning_agent.services.provider_models_service import ProviderModelsService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.search_tool_service import SearchToolConfigService
from semantic_reasoning_agent.services.secret_service import SecretService
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime
from semantic_reasoning_agent.services.workflow_registry_service import WorkflowRegistryService


def get_database_manager() -> DatabaseManager:
    return get_app_container().database_manager


def get_conversation_service() -> ConversationService:
    return get_app_container().conversation_service


def get_agent_profile_service() -> AgentProfileService:
    return get_app_container().agent_profile_service


def get_knowledge_pack_service() -> KnowledgePackService:
    return get_app_container().knowledge_pack_service


def get_agent_capability_service() -> AgentCapabilityService:
    return get_app_container().agent_capability_service


def get_model_config_service() -> ModelConfigService:
    return get_app_container().model_config_service


def get_secret_service() -> SecretService:
    return get_app_container().secret_service


def get_adapter_registry() -> AdapterRegistry:
    return get_app_container().adapter_registry


def get_document_service() -> DocumentService:
    return get_app_container().document_service


def get_ontology_service() -> OntologyService:
    return get_app_container().ontology_service


def get_ontology_graph_projection_service() -> OntologyGraphProjectionService:
    return get_app_container().ontology_graph_projection_service


def get_retrieval_service() -> RetrievalService:
    return get_app_container().retrieval_service


def get_chat_stream_service() -> ChatStreamService:
    return get_app_container().chat_stream_service


def get_provider_models_service() -> ProviderModelsService:
    return get_app_container().provider_models_service


def get_tool_registry() -> ToolRegistry:
    return get_app_container().tool_registry


def get_tool_runtime() -> ToolRuntime:
    return get_app_container().tool_runtime


def get_task_runtime_service() -> TaskRuntimeService:
    return get_app_container().task_runtime_service


def get_workflow_registry_service() -> WorkflowRegistryService:
    return get_app_container().workflow_registry_service


def get_runtime_audit_service() -> RuntimeAuditService:
    return get_app_container().runtime_audit_service


def get_search_tool_service() -> SearchToolConfigService:
    return get_app_container().search_tool_service
