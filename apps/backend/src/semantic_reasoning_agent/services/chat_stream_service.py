from semantic_reasoning_agent.schemas.chat import (
    ChatReply,
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
        runtime_provider = conversation.provider
        runtime_model = conversation.model

        if payload.provider and payload.model:
            if conversation.provider != payload.provider or conversation.model != payload.model:
                updated = self._conversation_service.update_runtime_selection(
                    payload.conversation_id,
                    ConversationModelSelectionRequest(
                        provider=payload.provider,
                        model=payload.model,
                        workspace_id=payload.workspace_id or conversation.workspace_id,
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
            payload.workspace_id or conversation.workspace_id,
        ):
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
            conversation=updated,
            reply=updated.messages[-1],
            citations=task_result.citations,
        )
