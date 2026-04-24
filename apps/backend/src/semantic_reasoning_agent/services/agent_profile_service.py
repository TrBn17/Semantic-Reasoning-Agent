from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    AgentProfileORM,
    AgentProfileTaskModelORM,
    SearchToolConfigORM,
)
from semantic_reasoning_agent.schemas.agent_capabilities import (
    EvidencePolicySchema,
    ToolPolicySchema,
)
from semantic_reasoning_agent.schemas.agent_profiles import (
    AgentProfileCreateRequest,
    AgentProfileResponse,
    AgentProfileTaskModelAssignment,
    AgentProfileToolAssignment,
    AgentProfileUpdateRequest,
)
from semantic_reasoning_agent.schemas.orchestration import (
    OrchestrationConfigSchema,
    default_orchestration_config,
)
from semantic_reasoning_agent.services.agent_capability_service import (
    merge_policy_config,
    resolve_capability_config,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfileNotFoundError(ValueError):
    """Raised when an agent profile id does not exist."""


class AgentProfileValidationError(ValueError):
    """Raised when an agent profile payload violates tool binding rules."""


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
                policy_config=self._merge_orchestration_config(
                    merge_policy_config(
                    payload.policy_config,
                    capability_preset=payload.capability_preset,
                    tool_policy=payload.tool_policy,
                    knowledge_pack_ids=payload.knowledge_pack_ids,
                    evidence_policy=payload.evidence_policy,
                    ),
                    payload.orchestration_config,
                ),
                tool_assignments=self._normalize_tool_assignments(
                    payload.tool_assignments,
                    workspace_id=payload.workspace_id,
                    tool_policy=payload.tool_policy,
                ),
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
            profile.policy_config = merge_policy_config(
                payload.policy_config if payload.policy_config is not None else profile.policy_config,
                capability_preset=payload.capability_preset,
                tool_policy=payload.tool_policy,
                knowledge_pack_ids=payload.knowledge_pack_ids,
                evidence_policy=payload.evidence_policy,
            )
            profile.policy_config = self._merge_orchestration_config(
                profile.policy_config,
                payload.orchestration_config,
            )
            effective_tool_policy = payload.tool_policy or ToolPolicySchema.model_validate(
                (profile.policy_config or {}).get("tool_policy") or {}
            )
            if payload.tool_assignments is not None:
                profile.tool_assignments = self._normalize_tool_assignments(
                    payload.tool_assignments,
                    workspace_id=profile.workspace_id,
                    tool_policy=effective_tool_policy,
                )
            elif payload.tool_policy is not None:
                profile.tool_assignments = self._normalize_tool_assignments(
                    profile.tool_assignments or [],
                    workspace_id=profile.workspace_id,
                    tool_policy=effective_tool_policy,
                )
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

    @classmethod
    def _to_schema(cls, profile: AgentProfileORM) -> AgentProfileResponse:
        capability = resolve_capability_config(profile.policy_config)
        orchestration_config = OrchestrationConfigSchema.model_validate(
            (profile.policy_config or {}).get("orchestration_config")
            or (profile.policy_config or {}).get("orchestration")
            or default_orchestration_config().model_dump()
        )
        return AgentProfileResponse(
            id=profile.id,
            workspace_id=profile.workspace_id,
            name=profile.name,
            description=profile.description,
            system_prompt=profile.system_prompt,
            allow_chat_model_override=profile.allow_chat_model_override,
            is_default=profile.is_default,
            status=profile.status,
            capability_preset=capability.capability_preset,
            tool_policy=ToolPolicySchema.model_validate(capability.tool_policy),
            knowledge_pack_ids=list(capability.knowledge_pack_ids),
            evidence_policy=EvidencePolicySchema.model_validate(capability.evidence_policy),
            orchestration_config=orchestration_config,
            policy_config=profile.policy_config or {},
            task_models=[
                AgentProfileTaskModelAssignment(
                    task_type=task_model.task_type,
                    provider=task_model.provider,
                    model=task_model.model,
                )
                for task_model in profile.task_models
            ],
            tool_assignments=cls._read_tool_assignments(profile.tool_assignments),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def _normalize_tool_assignments(
        self,
        assignments: list,
        *,
        workspace_id: str,
        tool_policy: ToolPolicySchema | None,
    ) -> list[dict]:
        normalized: list[dict] = []
        blocked_tools = set((tool_policy or ToolPolicySchema()).blocked_tools)
        allow_mode = (tool_policy or ToolPolicySchema()).mode == "allowlist"
        allowlist = set((tool_policy or ToolPolicySchema()).allowed_tools)
        config_ids = [
            item.config_id
            for item in (
                AgentProfileToolAssignment.model_validate(entry) for entry in (assignments or [])
            )
            if item.config_id
        ]
        config_lookup = self._load_search_tool_configs(workspace_id, config_ids)
        seen_slots: set[str] = set()
        for entry in assignments or []:
            item = AgentProfileToolAssignment.model_validate(entry)
            config = config_lookup.get(item.config_id or "")
            if item.slot in {"rag", "ontology_search"}:
                if item.slot in seen_slots:
                    raise AgentProfileValidationError(
                        f"Only one tool assignment is allowed for slot '{item.slot}'."
                    )
                seen_slots.add(item.slot)
            if item.config_id and config is None:
                raise AgentProfileValidationError(
                    f"Search tool config '{item.config_id}' was not found in workspace '{workspace_id}'."
                )
            resolved_tool_name = (
                "supersearch.docs"
                if config is not None and config.tool_type == "docs"
                else "supersearch.graph"
                if config is not None and config.tool_type == "graph"
                else item.tool_name
            )
            if item.config_id and resolved_tool_name != item.tool_name:
                raise AgentProfileValidationError(
                    f"Tool assignment '{item.slot}' must use tool '{config.tool_name}'."
                )
            if resolved_tool_name in blocked_tools:
                raise AgentProfileValidationError(
                    f"Tool '{resolved_tool_name}' is blocked by the current tool policy."
                )
            if allow_mode and allowlist and resolved_tool_name not in allowlist:
                raise AgentProfileValidationError(
                    f"Tool '{resolved_tool_name}' is not allowlisted by the current tool policy."
                )
            normalized.append(
                AgentProfileToolAssignment(
                    slot=item.slot,
                    tool_name=resolved_tool_name,
                    config_id=item.config_id,
                    enabled=item.enabled,
                    position=item.position,
                ).model_dump()
            )
        normalized.sort(key=lambda item: (int(item.get("position", 0)), str(item.get("slot", ""))))
        return normalized

    def _load_search_tool_configs(
        self,
        workspace_id: str,
        config_ids: list[str],
    ) -> dict[str, SearchToolConfigORM]:
        if not config_ids:
            return {}
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(SearchToolConfigORM).where(
                    SearchToolConfigORM.workspace_id == workspace_id,
                    SearchToolConfigORM.id.in_(config_ids),
                )
            ).all()
            return {row.id: row for row in rows}

    @staticmethod
    def _read_tool_assignments(assignments: list[dict] | None) -> list[AgentProfileToolAssignment]:
        return [
            AgentProfileToolAssignment.model_validate(item)
            for item in (assignments or [])
            if isinstance(item, dict)
        ]

    @staticmethod
    def _merge_orchestration_config(
        policy_config: dict | None,
        orchestration_config: OrchestrationConfigSchema | None,
    ) -> dict:
        merged = dict(policy_config or {})
        if orchestration_config is not None:
            merged["orchestration_config"] = orchestration_config.model_dump()
        elif "orchestration_config" not in merged:
            merged["orchestration_config"] = default_orchestration_config().model_dump()
        return merged
