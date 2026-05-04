from __future__ import annotations

import json
from importlib import resources
from uuid import uuid4

from sqlalchemy import select

from semantic_reasoning_agent.core.time import utc_now

from semantic_reasoning_agent.domain.builtin_agent_roles import (
    BUILTIN_AGENT_ROLES,
    BuiltinAgentRole,
    is_builtin_agent_role,
)
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import BuiltinAgentContextORM

_PACKAGE = "semantic_reasoning_agent"
_SKILLS_NAME = "SKILLS.md"
_MEMORY_NAME = "MEMORY.md"

NOTE_MAX_CHARS = 2048
MEMORY_BODY_MAX_CHARS = 16384


def _path_for(role: BuiltinAgentRole, filename: str) -> str:
    return f"builtin_agents/{role}/{filename}"


def read_packaged_file(role: BuiltinAgentRole, filename: str) -> str:
    root = resources.files(_PACKAGE)
    path = root.joinpath(_path_for(role, filename))
    return path.read_text(encoding="utf-8")


class BuiltinAgentContextService:
    """Workspace overrides for built-in agent SKILLS/MEMORY + episodic append."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def get_skills_text(self, workspace_id: str, role: BuiltinAgentRole) -> str:
        with self._database_manager.session() as session:
            row = session.scalar(
                select(BuiltinAgentContextORM).where(
                    BuiltinAgentContextORM.workspace_id == workspace_id,
                    BuiltinAgentContextORM.agent_role == role,
                )
            )
        if row is not None and row.skills_body is not None:
            return row.skills_body
        return read_packaged_file(role, _SKILLS_NAME)

    def get_memory_text(self, workspace_id: str, role: BuiltinAgentRole) -> str:
        with self._database_manager.session() as session:
            row = session.scalar(
                select(BuiltinAgentContextORM).where(
                    BuiltinAgentContextORM.workspace_id == workspace_id,
                    BuiltinAgentContextORM.agent_role == role,
                )
            )
        if row is not None and row.memory_body is not None:
            return row.memory_body
        return read_packaged_file(role, _MEMORY_NAME)

    def format_system_addendum(self, workspace_id: str, role: BuiltinAgentRole) -> str:
        skills = self.get_skills_text(workspace_id, role)
        memory = self.get_memory_text(workspace_id, role)
        return f"## SKILLS\n{skills}\n\n## MEMORY\n{memory}"

    def record_episodic_note(
        self,
        *,
        workspace_id: str,
        target_role: str,
        note: str,
        mode: str = "append",
    ) -> str:
        if not is_builtin_agent_role(target_role):
            return json.dumps(
                {
                    "status": "rejected",
                    "reason": f"target_role must be one of {list(BUILTIN_AGENT_ROLES)}",
                }
            )
        role: BuiltinAgentRole = target_role  # type: ignore[assignment]
        cleaned = (note or "").strip()
        if not cleaned:
            return json.dumps({"status": "empty", "message": "Note was empty; nothing stored."})
        cleaned = cleaned[:NOTE_MAX_CHARS]
        now = utc_now()
        with self._database_manager.session() as session:
            row = session.scalar(
                select(BuiltinAgentContextORM).where(
                    BuiltinAgentContextORM.workspace_id == workspace_id,
                    BuiltinAgentContextORM.agent_role == role,
                )
            )
            if mode == "replace":
                new_body = cleaned[:MEMORY_BODY_MAX_CHARS]
            else:
                baseline = (
                    row.memory_body
                    if row is not None and row.memory_body is not None
                    else read_packaged_file(role, _MEMORY_NAME)
                )
                merged = f"{baseline.rstrip()}\n\n---\n\n{cleaned}"
                new_body = merged[:MEMORY_BODY_MAX_CHARS]

            if row is None:
                session.add(
                    BuiltinAgentContextORM(
                        id=str(uuid4()),
                        workspace_id=workspace_id,
                        agent_role=role,
                        skills_body=None,
                        memory_body=new_body,
                        updated_at=now,
                    )
                )
            else:
                row.memory_body = new_body
                row.updated_at = now
        return json.dumps({"status": "stored", "target_role": role, "mode": mode})
