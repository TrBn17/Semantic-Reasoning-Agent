from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import AgentProfileORM, ConversationORM, MessageORM
from semantic_reasoning_agent.schemas.chat import (
    ConversationAgentProfileRequest,
    ConversationCreateRequest,
    ConversationModelSelectionRequest,
    ConversationResponse,
    Message,
)
from semantic_reasoning_agent.services.agent_profile_service import (
    AgentProfileNotFoundError,
    AgentProfileService,
)
from semantic_reasoning_agent.services.model_config_service import ModelConfigService

DEFAULT_EFFECTIVE_TOOL_NAMES = [
    "retrieval.internal",
    "ontology.lookup",
    "graph.search",
    "graph.ingest",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationNotFoundError(ValueError):
    """Raised when a conversation id does not exist."""


class ConversationPolicyError(ValueError):
    """Raised when a conversation action violates profile policy."""


class ConversationService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        model_config_service: ModelConfigService,
        agent_profile_service: AgentProfileService,
        settings: Settings | None = None,
    ) -> None:
        self._database_manager = database_manager
        self._model_config_service = model_config_service
        self._agent_profile_service = agent_profile_service
        self._settings = settings or get_settings()

    def list_conversations(self) -> list[ConversationResponse]:
        with self._database_manager.session() as session:
            conversations = session.scalars(
                select(ConversationORM)
                .options(selectinload(ConversationORM.messages))
                .order_by(desc(ConversationORM.updated_at))
            ).all()
            return [
                self._to_schema(
                    conversation,
                    profile=self._get_profile_record(session, conversation.agent_profile_id),
                )
                for conversation in conversations
            ]

    def create_conversation(self, payload: ConversationCreateRequest) -> ConversationResponse:
        workspace_id = payload.workspace_id or self._settings.default_workspace_id
        agent_profile_id = payload.agent_profile_id
        if agent_profile_id is None:
            default_profile = self._agent_profile_service.get_default_profile(workspace_id)
            agent_profile_id = None if default_profile is None else default_profile.id

        if payload.provider and payload.model:
            provider, model = payload.provider, payload.model
            uses_override = True
        else:
            provider, model = self._model_config_service.resolve_ready_task_model(
                "chat",
                workspace_id,
                agent_profile_id,
            )
            uses_override = False

        conversation = ConversationORM(
            id=str(uuid4()),
            title=payload.title,
            workspace_id=workspace_id,
            agent_profile_id=agent_profile_id,
            provider=provider,
            model=model,
            uses_model_override=uses_override,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        with self._database_manager.session() as session:
            session.add(conversation)
            session.flush()
            session.refresh(conversation)
            return self._to_schema(
                conversation,
                profile=self._get_profile_record(session, conversation.agent_profile_id),
            )

    def get_conversation(self, conversation_id: str) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.scalar(
                select(ConversationORM)
                .options(selectinload(ConversationORM.messages))
                .where(ConversationORM.id == conversation_id)
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            return self._to_schema(
                conversation,
                profile=self._get_profile_record(session, conversation.agent_profile_id),
            )

    def update_runtime_selection(
        self,
        conversation_id: str,
        payload: ConversationModelSelectionRequest,
    ) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.get(ConversationORM, conversation_id)
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            profile = self._get_profile_record(session, conversation.agent_profile_id)
            if profile is not None and not profile.allow_chat_model_override:
                raise ConversationPolicyError(
                    f"Conversation '{conversation_id}' does not allow chat model override."
                )
            if not self._model_config_service.is_ready(
                payload.provider,
                payload.model,
                payload.workspace_id or conversation.workspace_id,
            ):
                raise ConversationPolicyError(
                    f"Provider '{payload.provider}' with model '{payload.model}' is not ready."
                )
            conversation.provider = payload.provider
            conversation.model = payload.model
            conversation.uses_model_override = True
            conversation.updated_at = utc_now()
            session.flush()
            session.refresh(conversation)
            return self._to_schema(conversation, profile=profile)

    def update_agent_profile(
        self,
        conversation_id: str,
        payload: ConversationAgentProfileRequest,
    ) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.get(ConversationORM, conversation_id)
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            if payload.agent_profile_id is not None:
                profile = session.get(AgentProfileORM, payload.agent_profile_id)
                if profile is None:
                    raise AgentProfileNotFoundError(
                        f"Agent profile '{payload.agent_profile_id}' was not found."
                    )
                conversation.agent_profile_id = profile.id
            else:
                conversation.agent_profile_id = None

            if payload.clear_model_override or not conversation.uses_model_override:
                provider, model = self._model_config_service.resolve_ready_task_model(
                    "chat",
                    payload.workspace_id or conversation.workspace_id,
                    conversation.agent_profile_id,
                )
                conversation.provider = provider
                conversation.model = model
                conversation.uses_model_override = False

            conversation.updated_at = utc_now()
            session.flush()
            session.refresh(conversation)
            return self._to_schema(
                conversation,
                profile=self._get_profile_record(session, conversation.agent_profile_id),
            )

    def append_message(self, conversation_id: str, role: str, content: str) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.scalar(
                select(ConversationORM)
                .options(selectinload(ConversationORM.messages))
                .where(ConversationORM.id == conversation_id)
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            message = MessageORM(
                id=str(uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                created_at=utc_now(),
            )
            conversation.messages.append(message)
            conversation.updated_at = message.created_at
            session.flush()
            return self._to_schema(
                conversation,
                profile=self._get_profile_record(session, conversation.agent_profile_id),
            )

    def get_system_prompt(self, conversation_id: str) -> str | None:
        with self._database_manager.session() as session:
            conversation = session.get(ConversationORM, conversation_id)
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            profile = self._get_profile_record(session, conversation.agent_profile_id)
            return None if profile is None or not profile.system_prompt.strip() else profile.system_prompt

    def _get_profile_record(self, session, profile_id: str | None) -> AgentProfileORM | None:
        if profile_id is None:
            return None
        return session.get(AgentProfileORM, profile_id)

    def _to_schema(
        self,
        conversation: ConversationORM,
        *,
        profile: AgentProfileORM | None = None,
    ) -> ConversationResponse:
        messages = [
            Message(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in conversation.messages
        ]
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            workspace_id=conversation.workspace_id,
            agent_profile_id=conversation.agent_profile_id,
            provider=conversation.provider,
            model=conversation.model,
            uses_model_override=conversation.uses_model_override,
            effective_agent_name=profile.name if profile is not None else None,
            effective_tool_names=self._effective_tool_names(profile),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages,
        )

    @staticmethod
    def _effective_tool_names(profile: AgentProfileORM | None) -> list[str]:
        if profile is None or not profile.tool_assignments:
            return DEFAULT_EFFECTIVE_TOOL_NAMES.copy()
        assignment_map = {
            item.get("tool_name"): bool(item.get("enabled", True))
            for item in (profile.tool_assignments or [])
            if item.get("tool_name")
        }
        effective = [
            tool_name
            for tool_name in DEFAULT_EFFECTIVE_TOOL_NAMES
            if assignment_map.get(tool_name, True)
        ]
        extra_enabled = [
            tool_name
            for tool_name, enabled in assignment_map.items()
            if enabled and tool_name not in effective
        ]
        return effective + sorted(extra_enabled)
