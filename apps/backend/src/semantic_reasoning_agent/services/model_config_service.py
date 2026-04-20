from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    AgentProfileTaskModelORM,
    ProviderConfigORM,
    TaskModelConfigORM,
)
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.agents import (
    AgentSettingsResponse,
    AgentSettingsUpdateRequest,
    ModelOption,
    ProviderConfigResponse,
    ProviderFieldDefinition,
    ProviderFieldValue,
    TaskAssignmentResponse,
    TaskDefinition,
    TaskType,
)
from semantic_reasoning_agent.services.secret_service import SecretService
from semantic_reasoning_agent.services.provider_models_service import ProviderModelsService, ProviderModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ProviderFieldSpec:
    key: str
    label: str
    placeholder: str
    help_text: str
    required: bool = True
    secret: bool = False


@dataclass(frozen=True)
class ProviderSpec:
    provider: str
    label: str
    description: str
    fields: tuple[ProviderFieldSpec, ...]


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    label: str
    description: str
    context_window: int | None
    supports_streaming: bool
    supports_structured_output: bool
    recommended_for: tuple[TaskType, ...]


TASK_DEFINITIONS: tuple[TaskDefinition, ...] = (
    TaskDefinition(
        task_type="chat",
        label="Chat",
        description="Model mặc định cho chat tương tác với người dùng.",
    ),
    TaskDefinition(
        task_type="retrieval",
        label="Retrieval QA",
        description="Model dùng để tổng hợp câu trả lời có grounding từ tài liệu.",
    ),
    TaskDefinition(
        task_type="ontology_extraction",
        label="Ontology Extraction",
        description="Model ưu tiên structured output để trích entity và relation.",
    ),
    TaskDefinition(
        task_type="narrative_generation",
        label="Narrative",
        description="Model dùng để viết summary, brief và narrative từ graph.",
    ),
    TaskDefinition(
        task_type="dashboard_generation",
        label="Dashboard",
        description="Model dùng để đề xuất widget và sinh dashboard HTML.",
    ),
)

PROVIDER_SPECS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        provider="echo",
        label="Local Echo",
        description="Placeholder adapter cho local development và smoke test.",
        fields=(),
    ),
    ProviderSpec(
        provider="openai",
        label="OpenAI",
        description="Phù hợp chat, structured generation và tác vụ tổng hợp.",
        fields=(
            ProviderFieldSpec(
                key="OPENAI_API_KEY",
                label="OpenAI API Key",
                placeholder="sk-...",
                help_text="API key để gọi model OpenAI.",
                secret=True,
            ),
        ),
    ),
    ProviderSpec(
        provider="anthropic",
        label="Anthropic",
        description="Phù hợp long-context reasoning và structured extraction ổn định.",
        fields=(
            ProviderFieldSpec(
                key="ANTHROPIC_API_KEY",
                label="Anthropic API Key",
                placeholder="sk-ant-...",
                help_text="API key để gọi model Anthropic.",
                secret=True,
            ),
            ProviderFieldSpec(
                key="ANTHROPIC_BASE_URL",
                label="Anthropic Base URL",
                placeholder="https://api.anthropic.com",
                help_text="Endpoint tùy chỉnh cho Anthropic-compatible gateway (optional).",
                required=False,
                secret=False,
            ),
        ),
    ),
    ProviderSpec(
        provider="gemini",
        label="Google Gemini",
        description="Phù hợp tác vụ tốc độ cao, chi phí thấp và multimodal roadmap.",
        fields=(
            ProviderFieldSpec(
                key="GOOGLE_API_KEY",
                label="Google API Key",
                placeholder="AIza...",
                help_text="API key để gọi model Gemini.",
                secret=True,
            ),
        ),
    ),
    ProviderSpec(
        provider="ollama",
        label="Ollama",
        description="Phù hợp tài liệu private hoặc chạy local/on-prem.",
        fields=(
            ProviderFieldSpec(
                key="OLLAMA_BASE_URL",
                label="Ollama Base URL",
                placeholder="http://localhost:11434",
                help_text="Endpoint của Ollama server nội bộ.",
                secret=False,
            ),
        ),
    ),
)

MODEL_SPECS: tuple[ModelSpec, ...] = ()  # Legacy: now using ProviderModelsService for dynamic models


class ModelConfigService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        adapter_registry: AdapterRegistry,
        secret_service: SecretService,
        provider_models_service: ProviderModelsService,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._database_manager = database_manager
        self._adapter_registry = adapter_registry
        self._secret_service = secret_service
        self._provider_models_service = provider_models_service

    async def list_models(self, workspace_id: str | None = None) -> list[ModelOption]:
        """
        List all available models from configured providers.
        Fetches models dynamically from provider APIs instead of hardcoded list.
        """
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        credentials: dict[str, dict[str, str | None]] = {
            "openai": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "openai",
                    "OPENAI_API_KEY",
                    provider_configs,
                    secret=True,
                ),
            },
            "anthropic": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "anthropic",
                    "ANTHROPIC_API_KEY",
                    provider_configs,
                    secret=True,
                ),
                "base_url": self._resolve_provider_field_value(
                    workspace_id,
                    "anthropic",
                    "ANTHROPIC_BASE_URL",
                    provider_configs,
                    secret=False,
                ),
            },
            "gemini": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "gemini",
                    "GOOGLE_API_KEY",
                    provider_configs,
                    secret=True,
                ),
            },
            "ollama": {
                "base_url": self._resolve_provider_field_value(
                    workspace_id,
                    "ollama",
                    "OLLAMA_BASE_URL",
                    provider_configs,
                    secret=False,
                ),
            },
        }
        
        # Fetch models from all providers
        all_models: list[ModelOption] = []
        provider_models = await self._provider_models_service.get_all_provider_models(credentials)
        
        for provider, provider_models_list in provider_models.items():
            provider_spec = next((spec for spec in PROVIDER_SPECS if spec.provider == provider), None)
            if not provider_spec:
                continue
                
            for model in provider_models_list:
                model_option = self._provider_model_to_option(
                    provider,
                    model,
                    provider_spec,
                    provider_configs,
                    workspace_id,
                )
                all_models.append(model_option)
        
        return sorted(all_models, key=lambda x: (x.provider, x.model))

    def _resolve_provider_field_value(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
        provider_configs: dict[str, ProviderConfigORM],
        *,
        secret: bool,
    ) -> str | None:
        if secret:
            secret_value = self._secret_service.get_provider_secret(workspace_id, provider, field_key)
            if secret_value:
                return secret_value
            return self._runtime_env_value(field_key)

        provider_config = provider_configs.get(provider)
        if provider_config is not None:
            configured_value = (provider_config.env_values or {}).get(field_key)
            if configured_value:
                return configured_value
        return self._runtime_env_value(field_key)

    def list_tasks(self) -> list[TaskDefinition]:
        return list(TASK_DEFINITIONS)

    async def get_catalog(self, workspace_id: str | None = None) -> list[ModelOption]:
        return await self.list_models(workspace_id)

    async def get_agent_settings(self, workspace_id: str | None = None) -> AgentSettingsResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        models = await self.list_models(workspace_id)
        task_assignments = self._resolve_task_assignments(workspace_id, models)
        return AgentSettingsResponse(
            workspace_id=workspace_id,
            models=models,
            providers=[
                self._build_provider_response(spec, provider_configs, workspace_id)
                for spec in PROVIDER_SPECS
            ],
            tasks=list(TASK_DEFINITIONS),
            task_assignments=task_assignments,
        )

    async def update_agent_settings(self, payload: AgentSettingsUpdateRequest) -> AgentSettingsResponse:
        provider_specs = {spec.provider: spec for spec in PROVIDER_SPECS}
        with self._database_manager.session() as session:
            for provider_update in payload.providers:
                spec = provider_specs.get(provider_update.provider)
                if spec is None:
                    continue
                existing = session.scalar(
                    select(ProviderConfigORM).where(
                        ProviderConfigORM.workspace_id == payload.workspace_id,
                        ProviderConfigORM.provider == provider_update.provider,
                    )
                )
                filtered_values = {
                    field.key: provider_update.values.get(field.key, "").strip()
                    for field in spec.fields
                    if not field.secret and provider_update.values.get(field.key, "").strip()
                }
                for field in spec.fields:
                    if not field.secret:
                        continue
                    value = provider_update.values.get(field.key, "").strip()
                    if value:
                        self._secret_service.set_provider_secret(
                            payload.workspace_id,
                            provider_update.provider,
                            field.key,
                            value,
                        )
                if existing is None:
                    session.add(
                        ProviderConfigORM(
                            id=f"{payload.workspace_id}:{provider_update.provider}",
                            workspace_id=payload.workspace_id,
                            provider=provider_update.provider,
                            enabled=provider_update.enabled,
                            env_values=filtered_values,
                            created_at=utc_now(),
                            updated_at=utc_now(),
                        )
                    )
                else:
                    existing.enabled = provider_update.enabled
                    existing.env_values = filtered_values
                    existing.updated_at = utc_now()

            for assignment in payload.task_assignments:
                existing_assignment = session.scalar(
                    select(TaskModelConfigORM).where(
                        TaskModelConfigORM.workspace_id == payload.workspace_id,
                        TaskModelConfigORM.task_type == assignment.task_type,
                    )
                )
                if existing_assignment is None:
                    session.add(
                        TaskModelConfigORM(
                            id=str(uuid4()),
                            workspace_id=payload.workspace_id,
                            task_type=assignment.task_type,
                            provider=assignment.provider,
                            model=assignment.model,
                            created_at=utc_now(),
                            updated_at=utc_now(),
                        )
                    )
                else:
                    existing_assignment.provider = assignment.provider
                    existing_assignment.model = assignment.model
                    existing_assignment.updated_at = utc_now()
        return await self.get_agent_settings(payload.workspace_id)

    def is_ready(self, provider: str, model: str, workspace_id: str | None = None) -> bool:
        """
        Check if a provider/model combination is ready to use.
        This is a sync method for use in sync contexts like LLM extraction.
        Returns True if provider is enabled, configured, and has an adapter.
        """
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        provider_spec = next((spec for spec in PROVIDER_SPECS if spec.provider == provider), None)
        
        if not provider_spec:
            return False
            
        provider_config = provider_configs.get(provider)
        enabled = provider_config.enabled if provider_config is not None else True
        
        if not enabled:
            return False
            
        missing_env_fields = self._missing_env_fields(provider_spec, provider_config, workspace_id)
        if missing_env_fields:
            return False
            
        supports_runtime = self._adapter_registry.get(provider) is not None
        return supports_runtime

    def resolve_task_model(
        self,
        task_type: TaskType,
        workspace_id: str | None = None,
        agent_profile_id: str | None = None,
    ) -> tuple[str, str]:
        workspace_id = workspace_id or self._settings.default_workspace_id
        if agent_profile_id:
            profile_assignment = self._load_profile_task_assignment(agent_profile_id, task_type)
            if profile_assignment is not None:
                return profile_assignment
        task_configs = self._load_task_configs(workspace_id)
        saved = task_configs.get(task_type)
        if saved is not None:
            return saved.provider, saved.model
        return self._default_assignment(task_type)

    def resolve_runtime_model(
        self,
        task_type: TaskType,
        workspace_id: str | None = None,
        *,
        agent_profile_id: str | None = None,
        conversation_override: tuple[str, str] | None = None,
    ) -> tuple[str, str]:
        if conversation_override is not None:
            return conversation_override
        return self.resolve_task_model(task_type, workspace_id, agent_profile_id)

    @property
    def default_provider(self) -> str:
        return self._settings.default_provider

    @property
    def default_model(self) -> str:
        return self._settings.default_model

    def _load_provider_configs(self, workspace_id: str) -> dict[str, ProviderConfigORM]:
        with self._database_manager.session() as session:
            configs = session.scalars(
                select(ProviderConfigORM).where(ProviderConfigORM.workspace_id == workspace_id)
            ).all()
            return {config.provider: config for config in configs}

    def _load_task_configs(self, workspace_id: str) -> dict[str, TaskModelConfigORM]:
        with self._database_manager.session() as session:
            configs = session.scalars(
                select(TaskModelConfigORM).where(TaskModelConfigORM.workspace_id == workspace_id)
            ).all()
            return {config.task_type: config for config in configs}

    def _load_profile_task_assignment(
        self,
        agent_profile_id: str,
        task_type: TaskType,
    ) -> tuple[str, str] | None:
        with self._database_manager.session() as session:
            item = session.scalar(
                select(AgentProfileTaskModelORM).where(
                    AgentProfileTaskModelORM.agent_profile_id == agent_profile_id,
                    AgentProfileTaskModelORM.task_type == task_type,
                )
            )
            if item is None:
                return None
            return item.provider, item.model

    def _provider_model_to_option(
        self,
        provider: str,
        provider_model: ProviderModel,
        provider_spec: ProviderSpec,
        provider_configs: dict[str, ProviderConfigORM],
        workspace_id: str,
    ) -> ModelOption:
        """Convert a ProviderModel to ModelOption with readiness checks."""
        provider_config = provider_configs.get(provider)
        enabled = provider_config.enabled if provider_config is not None else True
        missing_env_fields = self._missing_env_fields(provider_spec, provider_config, workspace_id)
        supports_runtime = self._adapter_registry.get(provider) is not None
        
        if not enabled:
            ready = False
            reason = "Provider đang bị tắt trong agent settings."
        elif missing_env_fields:
            ready = False
            reason = f"Thiếu cấu hình: {', '.join(missing_env_fields)}."
        elif not supports_runtime:
            ready = False
            reason = "Đã có cấu hình nhưng adapter runtime chưa được implement trong backend."
        else:
            ready = True
            reason = "Sẵn sàng sử dụng."
        
        return ModelOption(
            provider=provider,
            model=provider_model.id,
            label=provider_model.name or provider_model.id,
            description=provider_model.description or "",
            ready=ready,
            enabled=enabled,
            supports_runtime=supports_runtime,
            supports_streaming=provider_model.supports_streaming,
            supports_structured_output=provider_model.supports_structured_output,
            context_window=provider_model.context_window,
            recommended_for=[],  # Dynamic models don't have task recommendations
            required_env_fields=[field.key for field in provider_spec.fields],
            missing_env_fields=missing_env_fields,
            reason=reason,
        )

    def _build_model_option(
        self,
        spec: ModelSpec,
        provider_configs: dict[str, ProviderConfigORM],
        workspace_id: str,
    ) -> ModelOption:
        provider_spec = next(item for item in PROVIDER_SPECS if item.provider == spec.provider)
        provider_config = provider_configs.get(spec.provider)
        enabled = provider_config.enabled if provider_config is not None else True
        missing_env_fields = self._missing_env_fields(provider_spec, provider_config, workspace_id)
        supports_runtime = self._adapter_registry.get(spec.provider) is not None
        if not enabled:
            ready = False
            reason = "Provider đang bị tắt trong agent settings."
        elif missing_env_fields:
            ready = False
            reason = f"Thiếu cấu hình: {', '.join(missing_env_fields)}."
        elif not supports_runtime:
            ready = False
            reason = "Đã có cấu hình nhưng adapter runtime chưa được implement trong backend."
        else:
            ready = True
            reason = "Sẵn sàng sử dụng."
        return ModelOption(
            provider=spec.provider,
            model=spec.model,
            label=spec.label,
            description=spec.description,
            ready=ready,
            enabled=enabled,
            supports_runtime=supports_runtime,
            supports_streaming=spec.supports_streaming,
            supports_structured_output=spec.supports_structured_output,
            context_window=spec.context_window,
            recommended_for=list(spec.recommended_for),
            required_env_fields=[field.key for field in provider_spec.fields],
            missing_env_fields=missing_env_fields,
            reason=reason,
        )

    def _build_provider_response(
        self,
        spec: ProviderSpec,
        provider_configs: dict[str, ProviderConfigORM],
        workspace_id: str,
    ) -> ProviderConfigResponse:
        provider_config = provider_configs.get(spec.provider)
        enabled = provider_config.enabled if provider_config is not None else True
        supports_runtime = self._adapter_registry.get(spec.provider) is not None
        missing_env_fields = self._missing_env_fields(spec, provider_config, workspace_id)
        if not enabled:
            ready = False
            reason = "Provider đang bị tắt."
        elif missing_env_fields:
            ready = False
            reason = f"Thiếu cấu hình: {', '.join(missing_env_fields)}."
        elif not supports_runtime:
            ready = False
            reason = "Chưa có adapter runtime."
        else:
            ready = True
            reason = "Sẵn sàng."

        values = []
        for field in spec.fields:
            configured_value = provider_config.env_values.get(field.key, "") if provider_config else ""
            runtime_value = self._runtime_env_value(field.key)
            secret_descriptor = (
                self._secret_service.describe_provider_secret(workspace_id, spec.provider, field.key)
                if field.secret
                else None
            )
            if field.secret and secret_descriptor and secret_descriptor.configured:
                source = secret_descriptor.source
                configured = True
                masked_value = secret_descriptor.masked_value
            elif configured_value:
                source = "database"
                configured = True
                masked_value = configured_value
            elif runtime_value:
                source = "runtime"
                configured = True
                masked_value = self._mask_runtime_value(field, runtime_value)
            else:
                source = "missing"
                configured = False
                masked_value = ""
            values.append(
                ProviderFieldValue(
                    key=field.key,
                    configured=configured,
                    source=source,
                    masked_value=masked_value,
                )
            )

        return ProviderConfigResponse(
            provider=spec.provider,
            label=spec.label,
            enabled=enabled,
            supports_runtime=supports_runtime,
            ready=ready,
            reason=reason,
            fields=[
                ProviderFieldDefinition(
                    key=field.key,
                    label=field.label,
                    placeholder=field.placeholder,
                    required=field.required,
                    secret=field.secret,
                    help_text=field.help_text,
                )
                for field in spec.fields
            ],
            values=values,
        )

    def _resolve_task_assignments(
        self,
        workspace_id: str,
        models: list[ModelOption],
    ) -> list[TaskAssignmentResponse]:
        task_configs = self._load_task_configs(workspace_id)
        model_lookup = {(model.provider, model.model): model for model in models}
        assignments: list[TaskAssignmentResponse] = []
        for task in TASK_DEFINITIONS:
            saved = task_configs.get(task.task_type)
            if saved is not None:
                provider = saved.provider
                model = saved.model
            else:
                provider, model = self._default_assignment(task.task_type)
            resolved = model_lookup.get((provider, model))
            assignments.append(
                TaskAssignmentResponse(
                    task_type=task.task_type,
                    provider=provider,
                    model=model,
                    ready=resolved.ready if resolved else False,
                    reason=resolved.reason if resolved else "Model chưa tồn tại trong catalog.",
                )
            )
        return assignments

    def _default_assignment(self, task_type: TaskType) -> tuple[str, str]:
        if task_type == "ontology_extraction":
            return self._settings.ontology_llm_provider, self._settings.ontology_llm_model
        return self._settings.default_provider, self._settings.default_model

    def _runtime_env_value(self, field_key: str) -> str | None:
        attr_by_env = {
            "OPENAI_API_KEY": self._settings.openai_api_key,
            "ANTHROPIC_API_KEY": self._settings.anthropic_api_key,
            "ANTHROPIC_BASE_URL": self._settings.anthropic_base_url,
            "GOOGLE_API_KEY": self._settings.google_api_key,
            "OLLAMA_BASE_URL": self._settings.ollama_base_url,
        }
        return attr_by_env.get(field_key)

    def _missing_env_fields(
        self,
        provider_spec: ProviderSpec,
        provider_config: ProviderConfigORM | None,
        workspace_id: str,
    ) -> list[str]:
        missing: list[str] = []
        stored_values = provider_config.env_values if provider_config is not None else {}
        for field in provider_spec.fields:
            has_secret = field.secret and self._secret_service.describe_provider_secret(
                workspace_id,
                provider_spec.provider,
                field.key,
            ).configured
            if stored_values.get(field.key) or self._runtime_env_value(field.key) or has_secret:
                continue
            if field.required:
                missing.append(field.key)
        return missing

    @staticmethod
    def _mask_runtime_value(field: ProviderFieldSpec, value: str) -> str:
        if field.secret:
            if len(value) <= 4:
                return "*" * len(value)
            return f"{value[:2]}{'*' * max(4, len(value) - 4)}{value[-2:]}"
        return value
