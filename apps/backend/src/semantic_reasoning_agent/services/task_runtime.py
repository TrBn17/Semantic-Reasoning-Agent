"""Compatibility shim. Canonical implementation: ``semantic_reasoning_agent.application.task_runtime``."""

from semantic_reasoning_agent.application.task_runtime import (
    AgentExecutionScope,
    SlotToolBinding,
    TaskRuntimeResult,
    TaskRuntimeService,
    ToolPlanStep,
)

__all__ = [
    "AgentExecutionScope",
    "SlotToolBinding",
    "TaskRuntimeResult",
    "TaskRuntimeService",
    "ToolPlanStep",
]
