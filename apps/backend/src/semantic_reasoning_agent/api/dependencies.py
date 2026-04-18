from semantic_reasoning_agent.container import get_app_container
from semantic_reasoning_agent.db.database import DatabaseManager
from semantic_reasoning_agent.graphdb.store import GraphStore
from semantic_reasoning_agent.llm.registry import AdapterRegistry
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.document_service import DocumentService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_service import OntologyService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService

def get_db_manager() -> DatabaseManager:
    return get_app_container().database_manager


def get_conversation_service() -> ConversationService:
    return get_app_container().conversation_service


def get_model_config_service() -> ModelConfigService:
    return get_app_container().model_config_service


def get_adapter_registry() -> AdapterRegistry:
    return get_app_container().adapter_registry


def get_document_service() -> DocumentService:
    return get_app_container().document_service


def get_graph_store() -> GraphStore:
    return get_app_container().graph_store


def get_ontology_service() -> OntologyService:
    return get_app_container().ontology_service


def get_retrieval_service() -> RetrievalService:
    return get_app_container().retrieval_service


def get_chat_stream_service() -> ChatStreamService:
    return get_app_container().chat_stream_service
