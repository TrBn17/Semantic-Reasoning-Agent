from fastapi import APIRouter

from semantic_reasoning_agent.api.routes.auth import router as auth_router
from semantic_reasoning_agent.api.routes.chat import router as chat_router
from semantic_reasoning_agent.api.routes.conversations import router as conversations_router
from semantic_reasoning_agent.api.routes.documents import router as documents_router
from semantic_reasoning_agent.api.routes.models import router as models_router
from semantic_reasoning_agent.api.routes.ontology import router as ontology_router
from semantic_reasoning_agent.api.routes.retrieval import router as retrieval_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(ontology_router, prefix="/ontology", tags=["ontology"])
api_router.include_router(retrieval_router, prefix="/retrieval", tags=["retrieval"])
