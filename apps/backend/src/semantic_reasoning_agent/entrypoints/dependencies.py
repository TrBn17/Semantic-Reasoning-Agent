from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.document_service import DocumentService
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_service import OntologyService
from semantic_reasoning_agent.services.provider_models_service import ProviderModelsService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.task_runtime import TaskRuntime
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime
from semantic_reasoning_agent.services.workflow_runtime import WorkflowRuntime


def get_conversation_service() -> ConversationService:
    return get_app_container().conversation_service


def get_agent_profile_service() -> AgentProfileService:
    return get_app_container().agent_profile_service


def get_model_config_service() -> ModelConfigService:
    return get_app_container().model_config_service


def get_document_service() -> DocumentService:
    return get_app_container().document_service


def get_ontology_service() -> OntologyService:
    return get_app_container().ontology_service


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


def get_task_runtime() -> TaskRuntime:
    return get_app_container().task_runtime


def get_workflow_runtime() -> WorkflowRuntime:
    return get_app_container().workflow_runtime


def get_runtime_audit_service() -> RuntimeAuditService:
    return get_app_container().runtime_audit_service
