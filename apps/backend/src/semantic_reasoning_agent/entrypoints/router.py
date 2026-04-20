from fastapi import APIRouter

from semantic_reasoning_agent.entrypoints.v1.agent_profiles import router as agent_profiles_router
from semantic_reasoning_agent.entrypoints.v1.agents import router as agents_router
from semantic_reasoning_agent.entrypoints.v1.auth import router as auth_router
from semantic_reasoning_agent.entrypoints.v1.chat import router as chat_router
from semantic_reasoning_agent.entrypoints.v1.conversations import router as conversations_router
from semantic_reasoning_agent.entrypoints.v1.documents import router as documents_router
from semantic_reasoning_agent.entrypoints.v1.models import router as models_router
from semantic_reasoning_agent.entrypoints.v1.ontology import router as ontology_router
from semantic_reasoning_agent.entrypoints.v1.provider_models import router as provider_models_router
from semantic_reasoning_agent.entrypoints.v1.retrieval import router as retrieval_router
from semantic_reasoning_agent.entrypoints.v1.tools import router as tools_router


api_router = APIRouter()
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(agent_profiles_router, prefix="/agents/profiles", tags=["agent-profiles"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(ontology_router, prefix="/ontology", tags=["ontology"])
api_router.include_router(provider_models_router, prefix="", tags=["provider-models"])
api_router.include_router(retrieval_router, prefix="/retrieval", tags=["retrieval"])
api_router.include_router(tools_router, prefix="/tools", tags=["tools"])
