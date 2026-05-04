"""Compatibility shim. Canonical implementation: ``semantic_reasoning_agent.application.agentic_loop_service``."""

from semantic_reasoning_agent.application.agentic_loop_service import (
    AgenticLoopResult,
    AgenticLoopService,
    LoopStepTrace,
)

__all__ = ["AgenticLoopResult", "AgenticLoopService", "LoopStepTrace"]
