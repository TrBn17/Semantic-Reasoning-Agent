from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway


def build_graphiti_gateway(settings: Settings) -> GraphitiGateway:
    return GraphitiGateway(settings)
