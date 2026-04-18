from semantic_reasoning_agent.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.chat import (
    ChatReply,
    ConversationModelSelectionRequest,
    SendMessageRequest,
)
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.services.conversation_service import (
    ConversationPolicyError,
    ConversationService,
)
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService


class ProviderNotReadyError(ValueError):
    """Raised when a provider/model pair is not ready for use."""


class ChatStreamService:
    def __init__(
        self,
        conversation_service: ConversationService,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        retrieval_service: RetrievalService,
    ) -> None:
        self._conversation_service = conversation_service
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._retrieval_service = retrieval_service

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

        adapter = self._adapter_registry.get(runtime_provider)
        if adapter is None:
            raise ProviderNotReadyError(f"No adapter is registered for provider '{runtime_provider}'.")

        self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.content,
        )

        citations: list[Citation] = []
        system_prompt = self._conversation_service.get_system_prompt(payload.conversation_id)
        reply_text = adapter.generate_reply(payload.content, system_prompt=system_prompt)
        if payload.use_retrieval:
            search_response = self._retrieval_service.search(
                query=payload.content,
                workspace_id=payload.workspace_id or conversation.workspace_id,
                document_ids=payload.document_ids,
                top_k=payload.top_k,
            )
            citations = [result.citation for result in search_response.results]
            if citations:
                reply_text = self._compose_grounded_reply(payload.content, citations)
            else:
                reply_text = "No indexed document context matched that question."

        updated = self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="assistant",
            content=reply_text,
        )
        return ChatReply(conversation=updated, reply=updated.messages[-1], citations=citations)

    @staticmethod
    def _compose_grounded_reply(prompt: str, citations: list[Citation]) -> str:
        lines = [f"Question: {prompt}", "Relevant context:"]
        for citation in citations:
            lines.append(
                f"- {citation.document_title} ({citation.location_label}): {citation.excerpt}"
            )
        return "\n".join(lines)
