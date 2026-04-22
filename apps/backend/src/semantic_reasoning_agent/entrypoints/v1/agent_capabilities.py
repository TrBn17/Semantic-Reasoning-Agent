from fastapi import APIRouter, Depends

from semantic_reasoning_agent.entrypoints.dependencies import get_agent_capability_service
from semantic_reasoning_agent.schemas.agent_capabilities import (
    AgentCapabilityCatalogResponse,
    AgentCapabilityToolSchema,
)
from semantic_reasoning_agent.services.agent_capability_service import AgentCapabilityService


router = APIRouter()


@router.get("/catalog", response_model=AgentCapabilityCatalogResponse)
def get_capability_catalog(
    capability_service: AgentCapabilityService = Depends(get_agent_capability_service),
) -> AgentCapabilityCatalogResponse:
    return capability_service.catalog()


@router.get("/tools", response_model=list[AgentCapabilityToolSchema])
def list_capability_tools(
    capability_service: AgentCapabilityService = Depends(get_agent_capability_service),
) -> list[AgentCapabilityToolSchema]:
    return capability_service.list_user_facing_tools()
