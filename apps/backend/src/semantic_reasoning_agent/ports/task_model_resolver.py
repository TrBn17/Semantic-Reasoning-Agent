from __future__ import annotations

from typing import Protocol


class TaskModelResolverPort(Protocol):
    def resolve_task_model(
        self,
        task_type: str,
        workspace_id: str | None = None,
        agent_profile_id: str | None = None,
    ) -> tuple[str, str]:
        ...

    def is_ready(
        self,
        provider: str,
        model: str,
        workspace_id: str | None = None,
    ) -> bool:
        ...
