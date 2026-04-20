from semantic_reasoning_agent.schemas.chat import (
    ChatReply,
    SendMessageRequest,
)
from semantic_reasoning_agent.services.conversation_service import (
    ConversationService,
)
from semantic_reasoning_agent.services.task_runtime import TaskRuntime


class ChatStreamService:
    def __init__(
        self,
        conversation_service: ConversationService,
        task_runtime: TaskRuntime,
    ) -> None:
        self._conversation_service = conversation_service
        self._task_runtime = task_runtime

    def send_message(self, payload: SendMessageRequest) -> ChatReply:
        self._conversation_service.get_conversation(payload.conversation_id)
        return self._task_runtime.resolve_chat_message(payload)
