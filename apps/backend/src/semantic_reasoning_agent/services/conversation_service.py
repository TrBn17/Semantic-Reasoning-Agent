from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    AgentProfileORM,
    ConversationORM,
    MessageORM,
    SearchToolConfigORM,
)
from semantic_reasoning_agent.schemas.chat import (
    ConversationAgentProfileRequest,
    ConversationCreateRequest,
    ConversationModelSelectionRequest,
    ConversationResponse,
    ConversationToolBinding,
    Message,
)
from semantic_reasoning_agent.schemas.agent_profiles import AgentProfileToolAssignment
from semantic_reasoning_agent.services.agent_profile_service import (
    AgentProfileNotFoundError,
    AgentProfileService,
)
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


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
            effective_tool_names=[
                item.tool_name for item in self._effective_tool_bindings(profile)
            ],
            effective_tool_bindings=self._effective_tool_bindings(profile),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages,
        )

    def _effective_tool_bindings(
        self,
        profile: AgentProfileORM | None,
    ) -> list[ConversationToolBinding]:
        if profile is None or not profile.tool_assignments:
            return []
        normalized = sorted(
            [
                AgentProfileToolAssignment.model_validate(item)
                for item in (profile.tool_assignments or [])
                if isinstance(item, dict)
                and bool((item.get("enabled", item.get("is_enabled", True))))
            ],
            key=lambda item: int(item.position),
        )
        config_lookup = self._load_config_lookup(
            profile.workspace_id,
            [
                str(item.config_id)
                for item in normalized
                if item.config_id
            ],
        )
        bindings: list[ConversationToolBinding] = []
        for index, item in enumerate(normalized):
            tool_name = item.tool_name.strip()
            if not tool_name:
                continue
            config_id = item.config_id
            config = config_lookup.get(str(config_id)) if config_id else None
            bindings.append(
                ConversationToolBinding(
                    slot=item.slot,
                    tool_name=tool_name,
                    config_id=str(config_id) if config_id else None,
                    label=config.name if config is not None else tool_name,
                    enabled=item.enabled,
                    position=item.position if item.position is not None else index,
                    is_system=bool(config.is_system) if config is not None else False,
                    system_key=config.system_key if config is not None else None,
                )
            )
        return bindings

    def _load_config_lookup(
        self,
        workspace_id: str,
        config_ids: list[str],
    ) -> dict[str, SearchToolConfigORM]:
        if not config_ids:
            return {}
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(SearchToolConfigORM).where(
                    SearchToolConfigORM.workspace_id == workspace_id,
                    SearchToolConfigORM.id.in_(config_ids),
                )
            ).all()
            return {row.id: row for row in rows}
