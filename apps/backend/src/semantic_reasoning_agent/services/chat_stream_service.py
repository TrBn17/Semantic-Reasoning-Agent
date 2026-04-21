import json
from collections.abc import Iterator

from semantic_reasoning_agent.schemas.chat import (
    ChatReply,
    ChatStreamEvent,
    ConversationModelSelectionRequest,
    SendMessageRequest,
)
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService


class ProviderNotReadyError(ValueError):
    """Raised when a provider/model pair is not ready for use."""


class ChatStreamService:
    def __init__(
        self,
        conversation_service: ConversationService,
        model_config_service: ModelConfigService,
        task_runtime_service: TaskRuntimeService,
    ) -> None:
        self._conversation_service = conversation_service
        self._model_config_service = model_config_service
        self._task_runtime_service = task_runtime_service

    def send_message(self, payload: SendMessageRequest) -> ChatReply:
        conversation = self._conversation_service.get_conversation(payload.conversation_id)
        workspace_id = payload.workspace_id or conversation.workspace_id
        runtime_provider = conversation.provider
        runtime_model = conversation.model

        if payload.provider and payload.model:
            if conversation.provider != payload.provider or conversation.model != payload.model:
                updated = self._conversation_service.update_runtime_selection(
                    payload.conversation_id,
                    ConversationModelSelectionRequest(
                        provider=payload.provider,
                        model=payload.model,
                        workspace_id=workspace_id,
                    ),
                )
                runtime_provider = updated.provider
                runtime_model = updated.model
            else:
                runtime_provider = payload.provider
                runtime_model = payload.model

        if not self._model_config_service.is_ready(
            runtime_provider,
            runtime_model,
            workspace_id,
        ):
            if payload.provider or payload.model:
                raise ProviderNotReadyError(
                    f"Provider '{runtime_provider}' with model '{runtime_model}' is not ready yet."
                )
            fallback_provider, fallback_model = self._model_config_service.resolve_ready_task_model(
                "chat",
                workspace_id,
                conversation.agent_profile_id,
            )
            if self._model_config_service.is_ready(fallback_provider, fallback_model, workspace_id):
                updated = self._conversation_service.update_runtime_selection(
                    payload.conversation_id,
                    ConversationModelSelectionRequest(
                        provider=fallback_provider,
                        model=fallback_model,
                        workspace_id=workspace_id,
                    ),
                )
                runtime_provider = updated.provider
                runtime_model = updated.model
            else:
                raise ProviderNotReadyError(
                    f"Provider '{runtime_provider}' with model '{runtime_model}' is not ready yet."
                )

        self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.content,
        )

        system_prompt = self._conversation_service.get_system_prompt(payload.conversation_id)
        task_result = self._task_runtime_service.resolve_chat_request(
            payload,
            provider=runtime_provider,
            model=runtime_model,
            system_prompt=system_prompt,
        )

        updated = self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="assistant",
            content=task_result.content,
        )
        return ChatReply(
            conversation_id=updated.id,
            reply=updated.messages[-1],
            citations=task_result.citations,
            tool_calls=task_result.tool_calls,
        )

    def stream_message(self, payload: SendMessageRequest) -> Iterator[str]:
        yield self._serialize_event(
            ChatStreamEvent(
                event="message_start",
                data={"conversation_id": payload.conversation_id},
            )
        )
        try:
            reply = self.send_message(payload)
            for tool_call in reply.tool_calls:
                yield self._serialize_event(ChatStreamEvent(event="tool_call_start", data=tool_call))
                yield self._serialize_event(ChatStreamEvent(event="tool_call_end", data=tool_call))
            for chunk in _chunk_text(reply.reply.content):
                yield self._serialize_event(
                    ChatStreamEvent(event="content_delta", data={"delta": chunk})
                )
            if reply.citations:
                yield self._serialize_event(
                    ChatStreamEvent(
                        event="citations",
                        data={
                            "citations": [
                                citation.model_dump(mode="json") for citation in reply.citations
                            ]
                        },
                    )
                )
            yield self._serialize_event(
                ChatStreamEvent(
                    event="message_complete",
                    data={
                        "conversation_id": reply.conversation_id,
                        "reply": reply.reply.model_dump(mode="json"),
                        "citations": [
                            citation.model_dump(mode="json") for citation in reply.citations
                        ],
                        "tool_calls": reply.tool_calls,
                    },
                )
            )
        except Exception as exc:
            yield self._serialize_event(
                ChatStreamEvent(event="error", data={"message": str(exc)})
            )

    @staticmethod
    def _serialize_event(event: ChatStreamEvent) -> str:
        return f"event: {event.event}\ndata: {json.dumps(event.data, default=str)}\n\n"


def _chunk_text(text: str, size: int = 120) -> list[str]:
    if not text:
        return [""]
    return [text[index:index + size] for index in range(0, len(text), size)]
