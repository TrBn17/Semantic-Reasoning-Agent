from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.agent_profiles import AgentProfileORM, AgentProfileTaskModelORM
from semantic_reasoning_agent.schemas.agent_profiles import (
    AgentProfileCreateRequest,
    AgentProfileResponse,
    AgentProfileTaskModelAssignment,
    AgentProfileUpdateRequest,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfileNotFoundError(ValueError):
    """Raised when an agent profile id does not exist."""


class AgentProfileService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        settings: Settings | None = None,
    ) -> None:
        self._database_manager = database_manager
        self._settings = settings or get_settings()

    def list_profiles(self, workspace_id: str | None = None) -> list[AgentProfileResponse]:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            profiles = session.scalars(
                select(AgentProfileORM)
                .options(selectinload(AgentProfileORM.task_models))
                .where(AgentProfileORM.workspace_id == resolved_workspace_id)
            ).all()
            profiles.sort(key=lambda item: (not item.is_default, item.name.lower()))
            return [self._to_schema(profile) for profile in profiles]

    def create_profile(self, payload: AgentProfileCreateRequest) -> AgentProfileResponse:
        profile_id = str(uuid4())
        now = utc_now()
        with self._database_manager.session() as session:
            if payload.is_default:
                self._clear_default_profile(session, payload.workspace_id)
            profile = AgentProfileORM(
                id=profile_id,
                workspace_id=payload.workspace_id,
                name=payload.name,
                description=payload.description,
                system_prompt=payload.system_prompt,
                allow_chat_model_override=payload.allow_chat_model_override,
                is_default=payload.is_default,
                status=payload.status,
                policy_config=payload.policy_config,
                created_at=now,
                updated_at=now,
            )
            session.add(profile)
            session.flush()
            self._replace_task_models(session, profile_id, payload.task_models)
        return self.get_profile(profile_id)

    def get_profile(self, profile_id: str) -> AgentProfileResponse:
        with self._database_manager.session() as session:
            profile = session.scalar(
                select(AgentProfileORM)
                .options(selectinload(AgentProfileORM.task_models))
                .where(AgentProfileORM.id == profile_id)
            )
            if profile is None:
                raise AgentProfileNotFoundError(f"Agent profile '{profile_id}' was not found.")
            return self._to_schema(profile)

    def update_profile(self, profile_id: str, payload: AgentProfileUpdateRequest) -> AgentProfileResponse:
        with self._database_manager.session() as session:
            profile = session.scalar(
                select(AgentProfileORM)
                .options(selectinload(AgentProfileORM.task_models))
                .where(AgentProfileORM.id == profile_id)
            )
            if profile is None:
                raise AgentProfileNotFoundError(f"Agent profile '{profile_id}' was not found.")

            if payload.name is not None:
                profile.name = payload.name
            if payload.description is not None:
                profile.description = payload.description
            if payload.system_prompt is not None:
                profile.system_prompt = payload.system_prompt
            if payload.allow_chat_model_override is not None:
                profile.allow_chat_model_override = payload.allow_chat_model_override
            if payload.status is not None:
                profile.status = payload.status
            if payload.policy_config is not None:
                profile.policy_config = payload.policy_config
            profile.updated_at = utc_now()

            if payload.task_models is not None:
                self._replace_task_models(session, profile_id, payload.task_models)
        return self.get_profile(profile_id)

    def set_default_profile(self, profile_id: str) -> AgentProfileResponse:
        with self._database_manager.session() as session:
            profile = session.get(AgentProfileORM, profile_id)
            if profile is None:
                raise AgentProfileNotFoundError(f"Agent profile '{profile_id}' was not found.")
            self._clear_default_profile(session, profile.workspace_id)
            profile.is_default = True
            profile.updated_at = utc_now()
        return self.get_profile(profile_id)

    def get_default_profile(self, workspace_id: str | None = None) -> AgentProfileResponse | None:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            profile = session.scalar(
                select(AgentProfileORM)
                .options(selectinload(AgentProfileORM.task_models))
                .where(
                    AgentProfileORM.workspace_id == resolved_workspace_id,
                    AgentProfileORM.is_default.is_(True),
                    AgentProfileORM.status == "active",
                )
            )
            return None if profile is None else self._to_schema(profile)

    def _replace_task_models(
        self,
        session,
        profile_id: str,
        task_models: list[AgentProfileTaskModelAssignment],
    ) -> None:
        existing = session.scalars(
            select(AgentProfileTaskModelORM).where(AgentProfileTaskModelORM.agent_profile_id == profile_id)
        ).all()
        for item in existing:
            session.delete(item)
        now = utc_now()
        for task_model in task_models:
            session.add(
                AgentProfileTaskModelORM(
                    id=str(uuid4()),
                    agent_profile_id=profile_id,
                    task_type=task_model.task_type,
                    provider=task_model.provider,
                    model=task_model.model,
                    created_at=now,
                    updated_at=now,
                )
            )

    @staticmethod
    def _clear_default_profile(session, workspace_id: str) -> None:
        profiles = session.scalars(
            select(AgentProfileORM).where(AgentProfileORM.workspace_id == workspace_id)
        ).all()
        now = utc_now()
        for profile in profiles:
            if profile.is_default:
                profile.is_default = False
                profile.updated_at = now

    @staticmethod
    def _to_schema(profile: AgentProfileORM) -> AgentProfileResponse:
        return AgentProfileResponse(
            id=profile.id,
            workspace_id=profile.workspace_id,
            name=profile.name,
            description=profile.description,
            system_prompt=profile.system_prompt,
            allow_chat_model_override=profile.allow_chat_model_override,
            is_default=profile.is_default,
            status=profile.status,
            policy_config=profile.policy_config or {},
            task_models=[
                AgentProfileTaskModelAssignment(
                    task_type=task_model.task_type,
                    provider=task_model.provider,
                    model=task_model.model,
                )
                for task_model in profile.task_models
            ],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
