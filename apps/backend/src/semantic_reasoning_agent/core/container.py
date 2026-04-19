from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager, get_database_manager
from semantic_reasoning_agent.infrastructure.graph import build_graph_store
from semantic_reasoning_agent.ports.graph_store import GraphStore
from semantic_reasoning_agent.infrastructure.ontology import (
    HybridOntologyExtractor,
    LLMStructuredExtractor,
    RuleSeedExtractor,
)
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry, build_adapter_registry
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.chat_stream_service import ChatStreamService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.document_service import DocumentService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_service import OntologyService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.services.secret_service import DatabaseSecretRepository, SecretService
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    database_manager: DatabaseManager
    secret_service: SecretService
    agent_profile_service: AgentProfileService
    model_config_service: ModelConfigService
    adapter_registry: AdapterRegistry
    graph_store: GraphStore
    retrieval_service: RetrievalService
    conversation_service: ConversationService
    task_dispatcher: TaskDispatcher
    document_service: DocumentService
    ontology_service: OntologyService
    chat_stream_service: ChatStreamService


@lru_cache
def get_app_container() -> AppContainer:
    settings = get_settings()
    database_manager = get_database_manager()
    adapter_registry = build_adapter_registry()
    secret_service = SecretService(DatabaseSecretRepository(database_manager))
    agent_profile_service = AgentProfileService(database_manager, settings)
    model_config_service = ModelConfigService(
        database_manager=database_manager,
        adapter_registry=adapter_registry,
        secret_service=secret_service,
        settings=settings,
    )
    graph_store = build_graph_store(settings)
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
        retrieval_service,
        database_manager,
        task_dispatcher,
    )
    ontology_service = OntologyService(
        settings,
        database_manager,
        task_dispatcher,
        graph_store,
        ontology_extractor=HybridOntologyExtractor(
            llm_extractor=LLMStructuredExtractor(settings, model_config_service),
            rule_extractor=RuleSeedExtractor(),
        ),
    )
    chat_stream_service = ChatStreamService(
        conversation_service=conversation_service,
        model_config_service=model_config_service,
        adapter_registry=adapter_registry,
        retrieval_service=retrieval_service,
    )
    return AppContainer(
        settings=settings,
        database_manager=database_manager,
        secret_service=secret_service,
        agent_profile_service=agent_profile_service,
        model_config_service=model_config_service,
        adapter_registry=adapter_registry,
        graph_store=graph_store,
        retrieval_service=retrieval_service,
        conversation_service=conversation_service,
        task_dispatcher=task_dispatcher,
        document_service=document_service,
        ontology_service=ontology_service,
        chat_stream_service=chat_stream_service,
    )
