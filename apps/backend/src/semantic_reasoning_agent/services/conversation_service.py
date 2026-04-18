from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.db.database import DatabaseManager
from semantic_reasoning_agent.db.models import ConversationORM, MessageORM
from semantic_reasoning_agent.schemas.chat import (
    ConversationCreateRequest,
    ConversationResponse,
    Message,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationNotFoundError(ValueError):
    """Raised when a conversation id does not exist."""


class ConversationService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def list_conversations(self) -> list[ConversationResponse]:
        with self._database_manager.session() as session:
            conversations = session.scalars(
                select(ConversationORM)
                .options(selectinload(ConversationORM.messages))
                .order_by(desc(ConversationORM.updated_at))
            ).all()
            return [self._to_schema(conversation) for conversation in conversations]

    def create_conversation(self, payload: ConversationCreateRequest) -> ConversationResponse:
        conversation = ConversationORM(
            id=str(uuid4()),
            title=payload.title,
            provider=payload.provider,
            model=payload.model,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        with self._database_manager.session() as session:
            session.add(conversation)
            session.flush()
            session.refresh(conversation)
            return self._to_schema(conversation)

    def get_conversation(self, conversation_id: str) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.scalar(
                select(ConversationORM)
                .options(selectinload(ConversationORM.messages))
                .where(ConversationORM.id == conversation_id)
            )
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")
            return self._to_schema(conversation)

    def update_runtime_selection(
        self,
        conversation_id: str,
        provider: str,
        model: str,
    ) -> ConversationResponse:
        with self._database_manager.session() as session:
            conversation = session.get(ConversationORM, conversation_id)
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation '{conversation_id}' was not found.")

            conversation.provider = provider
            conversation.model = model
            conversation.updated_at = utc_now()
            session.flush()
            return self._to_schema(conversation)

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
            return self._to_schema(conversation)

    def _to_schema(self, conversation: ConversationORM) -> ConversationResponse:
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
            provider=conversation.provider,
            model=conversation.model,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages,
        )
