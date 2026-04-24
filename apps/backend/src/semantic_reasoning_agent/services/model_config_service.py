from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    AgentProfileTaskModelORM,
    ProviderConfigORM,
    TaskModelConfigORM,
    WorkspaceSearchSettingsORM,
)
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry, build_adapter_registry
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
from semantic_reasoning_agent.schemas.auth import WorkspaceSummary
from semantic_reasoning_agent.schemas.settings import (
    PublicSettingsResponse,
    PublicSettingsUpdateRequest,
    SettingsModelOption,
    SettingsProviderFieldValue,
    SettingsProviderResponse,
    WorkspaceSearchDefaultsResponse,
    WorkspaceSearchDefaultsUpdateRequest,
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
            ProviderFieldSpec(
                key="OPENAI_BASE_URL",
                label="OpenAI Base URL",
                placeholder="https://api.openai.com/v1",
                help_text="Endpoint tùy chỉnh cho OpenAI-compatible gateway.",
                required=False,
                secret=False,
            ),
        ),
    ),
    ProviderSpec(
        provider="openrouter",
        label="OpenRouter",
        description="OpenAI-compatible router cho nhiều model bên thứ ba.",
        fields=(
            ProviderFieldSpec(
                key="OPENROUTER_API_KEY",
                label="OpenRouter API Key",
                placeholder="sk-or-...",
                help_text="API key để gọi OpenRouter.",
                secret=True,
            ),
            ProviderFieldSpec(
                key="OPENROUTER_BASE_URL",
                label="OpenRouter Base URL",
                placeholder="https://openrouter.ai/api/v1",
                help_text="Endpoint OpenRouter-compatible. Mặc định là OpenRouter public API.",
                required=False,
                secret=False,
            ),
        ),
    ),
    ProviderSpec(
        provider="cloudflare",
        label="Cloudflare Workers AI",
        description="OpenAI-compatible endpoint qua Cloudflare Workers AI.",
        fields=(
            ProviderFieldSpec(
                key="CLOUDFLARE_API_KEY",
                label="Cloudflare API Key",
                placeholder="cfut_...",
                help_text="API key/token để gọi Workers AI qua OpenAI SDK.",
                secret=True,
            ),
            ProviderFieldSpec(
                key="CLOUDFLARE_ACCOUNT_ID",
                label="Cloudflare Account ID",
                placeholder="184e67c1ca6539acb8c6ec7eff68cb50",
                help_text="Account ID dùng để build base URL cho Workers AI.",
                secret=False,
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
        List available models from providers explicitly enabled in workspace settings.
        Fetches models dynamically from provider APIs.
        """
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        credentials = self._provider_credentials(workspace_id, provider_configs)

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

    async def list_provider_models(
        self,
        provider: str,
        workspace_id: str | None = None,
    ) -> list[ProviderModel]:
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        credentials = self._provider_credentials(workspace_id, provider_configs)
        provider_credential = credentials.get(provider, {})
        return await self._provider_models_service.get_provider_models(
            provider,
            api_key=provider_credential.get("api_key"),
            base_url=provider_credential.get("base_url"),
        )

    async def list_all_provider_models(
        self,
        workspace_id: str | None = None,
    ) -> dict[str, list[ProviderModel]]:
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        credentials = self._provider_credentials(workspace_id, provider_configs)
        return await self._provider_models_service.get_all_provider_models(credentials)

    def get_provider_credentials(
        self,
        workspace_id: str | None = None,
    ) -> dict[str, dict[str, str | None]]:
        workspace_id = workspace_id or self._settings.default_workspace_id
        provider_configs = self._load_provider_configs(workspace_id)
        return self._provider_credentials(workspace_id, provider_configs)

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

    def _provider_credentials(
        self,
        workspace_id: str,
        provider_configs: dict[str, ProviderConfigORM],
    ) -> dict[str, dict[str, str | None]]:
        return {
            "openai": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "openai",
                    "OPENAI_API_KEY",
                    provider_configs,
                    secret=True,
                ),
                "base_url": self._resolve_provider_field_value(
                    workspace_id,
                    "openai",
                    "OPENAI_BASE_URL",
                    provider_configs,
                    secret=False,
                ),
            },
            "openrouter": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "openrouter",
                    "OPENROUTER_API_KEY",
                    provider_configs,
                    secret=True,
                ),
                "base_url": self._resolve_provider_field_value(
                    workspace_id,
                    "openrouter",
                    "OPENROUTER_BASE_URL",
                    provider_configs,
                    secret=False,
                ),
            },
            "cloudflare": {
                "api_key": self._resolve_provider_field_value(
                    workspace_id,
                    "cloudflare",
                    "CLOUDFLARE_API_KEY",
                    provider_configs,
                    secret=True,
                ),
                "base_url": self._cloudflare_base_url(
                    self._resolve_provider_field_value(
                        workspace_id,
                        "cloudflare",
                        "CLOUDFLARE_ACCOUNT_ID",
                        provider_configs,
                        secret=False,
                    )
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

    async def list_public_models(self, workspace_id: str | None = None) -> list[SettingsModelOption]:
        return [self._to_public_model_option(model) for model in await self.list_models(workspace_id)]

    async def get_public_settings(self, workspace_id: str | None = None) -> PublicSettingsResponse:
        settings = await self.get_agent_settings(workspace_id)
        return PublicSettingsResponse(
            workspace=WorkspaceSummary(
                id=settings.workspace_id,
                name=self._workspace_name(settings.workspace_id),
            ),
            providers=[self._to_public_provider(provider) for provider in settings.providers],
            search_defaults=self.get_workspace_search_defaults(settings.workspace_id),
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
                existing_values = existing.env_values if existing is not None else {}
                filtered_values = {
                    field.key: provider_update.values.get(field.key, "").strip()
                    for field in spec.fields
                    if not field.secret and provider_update.values.get(field.key, "").strip()
                }
                # Keep existing non-secret values when a client omits keys
                # (for example, saving before local drafts finish hydrating).
                for field in spec.fields:
                    if field.secret or field.key in provider_update.values:
                        continue
                    existing_value = (existing_values or {}).get(field.key, "").strip()
                    if existing_value:
                        filtered_values[field.key] = existing_value
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
        self._refresh_adapter_registry(payload.workspace_id)
        return await self.get_agent_settings(payload.workspace_id)

    async def update_public_settings(
        self,
        payload: PublicSettingsUpdateRequest,
    ) -> PublicSettingsResponse:
        if payload.search_defaults is not None:
            self.update_workspace_search_defaults(
                payload.workspace_id,
                payload.search_defaults,
            )
        updated = await self.update_agent_settings(
            AgentSettingsUpdateRequest(
                workspace_id=payload.workspace_id,
                providers=payload.providers,
                task_assignments=[],
            )
        )
        return PublicSettingsResponse(
            workspace=WorkspaceSummary(
                id=updated.workspace_id,
                name=self._workspace_name(updated.workspace_id),
            ),
            providers=[self._to_public_provider(provider) for provider in updated.providers],
            search_defaults=self.get_workspace_search_defaults(updated.workspace_id),
        )

    def get_workspace_search_defaults(
        self,
        workspace_id: str | None = None,
    ) -> WorkspaceSearchDefaultsResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        record = self._load_workspace_search_settings(resolved_workspace_id)
        provider = (
            record.embedding_provider
            if record is not None and record.embedding_provider
            else self._settings.default_embedding_provider
        )
        model = (
            record.embedding_model
            if record is not None and record.embedding_model
            else self._settings.default_embedding_model
        )
        ready, reason = self.embedding_backend_status(
            provider,
            model,
            resolved_workspace_id,
        )
        return WorkspaceSearchDefaultsResponse(
            embedding_provider=provider,
            embedding_model=model,
            ready=ready,
            reason=reason,
        )

    def update_workspace_search_defaults(
        self,
        workspace_id: str,
        payload: WorkspaceSearchDefaultsUpdateRequest,
    ) -> WorkspaceSearchDefaultsResponse:
        now = utc_now()
        with self._database_manager.session() as session:
            existing = session.get(WorkspaceSearchSettingsORM, workspace_id)
            if existing is None:
                session.add(
                    WorkspaceSearchSettingsORM(
                        workspace_id=workspace_id,
                        embedding_provider=payload.embedding_provider.strip(),
                        embedding_model=payload.embedding_model.strip(),
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                existing.embedding_provider = payload.embedding_provider.strip()
                existing.embedding_model = payload.embedding_model.strip()
                existing.updated_at = now
        return self.get_workspace_search_defaults(workspace_id)

    def embedding_backend_status(
        self,
        provider: str,
        model: str,
        workspace_id: str | None = None,
    ) -> tuple[bool, str]:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        provider_key = (provider or "").strip().lower()
        if not provider_key:
            return False, "Embedding provider is not configured."
        if not (model or "").strip():
            return False, "Embedding model is not configured."
        if provider_key == "cloudflare":
            credentials = self.get_provider_credentials(resolved_workspace_id).get("cloudflare", {})
            if not credentials.get("api_key"):
                return False, "Cloudflare API key is not configured."
            if not credentials.get("base_url"):
                return False, "Cloudflare account id is not configured."
            return True, "Ready to run."
        return False, f"Embedding provider '{provider}' is not supported."

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

        if provider not in provider_configs:
            return False

        provider_config = provider_configs.get(provider)
        enabled = provider_config.enabled if provider_config is not None else False
        
        if not enabled:
            return False
            
        missing_env_fields = self._missing_env_fields(provider_spec, provider_config, workspace_id)
        if missing_env_fields:
            return False
            
        supports_runtime = self._adapter_registry.get(provider) is not None
        return supports_runtime

    def _refresh_adapter_registry(self, workspace_id: str) -> None:
        refreshed = build_adapter_registry(
            self._settings,
            model_config_service=self,
            workspace_id=workspace_id,
        )
        self._adapter_registry.refresh(refreshed.adapters)

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

    def resolve_ready_task_model(
        self,
        task_type: TaskType,
        workspace_id: str | None = None,
        agent_profile_id: str | None = None,
    ) -> tuple[str, str]:
        workspace_id = workspace_id or self._settings.default_workspace_id

        candidates: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def add_candidate(provider: str, model: str) -> None:
            pair = (provider, model)
            if pair not in seen:
                seen.add(pair)
                candidates.append(pair)

        if agent_profile_id:
            profile_assignment = self._load_profile_task_assignment(agent_profile_id, task_type)
            if profile_assignment is not None:
                add_candidate(*profile_assignment)

        task_configs = self._load_task_configs(workspace_id)
        saved = task_configs.get(task_type)
        if saved is not None:
            add_candidate(saved.provider, saved.model)

        add_candidate(*self._default_assignment(task_type))

        for provider, model in candidates:
            if self.is_ready(provider, model, workspace_id):
                return provider, model

        return candidates[0]

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

    def _load_workspace_search_settings(
        self,
        workspace_id: str,
    ) -> WorkspaceSearchSettingsORM | None:
        with self._database_manager.session() as session:
            return session.get(WorkspaceSearchSettingsORM, workspace_id)

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
        enabled = provider_config.enabled if provider_config is not None else False
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
            model_type=provider_model.model_type,
            input_type=provider_model.input_type,
            output_type=provider_model.output_type,
        )

    def _build_provider_response(
        self,
        spec: ProviderSpec,
        provider_configs: dict[str, ProviderConfigORM],
        workspace_id: str,
    ) -> ProviderConfigResponse:
        provider_config = provider_configs.get(spec.provider)
        enabled = provider_config.enabled if provider_config is not None else False
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
            elif task.task_type != "ontology_extraction":
                provider, model = self._default_assignment(task.task_type)
            else:
                continue
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

    def _to_public_model_option(self, model: ModelOption) -> SettingsModelOption:
        return SettingsModelOption(
            provider=model.provider,
            model=model.model,
            label=model.label,
            description=model.description,
            ready=model.ready,
            reason=self._translate_reason(model.reason),
            supports_streaming=model.supports_streaming,
            supports_structured_output=model.supports_structured_output,
            context_window=model.context_window,
            model_type=model.model_type,
            input_type=model.input_type,
            output_type=model.output_type,
        )

    def _to_public_provider(self, provider: ProviderConfigResponse) -> SettingsProviderResponse:
        return SettingsProviderResponse(
            provider=provider.provider,
            label=provider.label,
            enabled=provider.enabled,
            ready=provider.ready,
            status_text=self._translate_reason(provider.reason),
            fields=provider.fields,
            values=[
                SettingsProviderFieldValue(
                    key=value.key,
                    configured=value.configured,
                    source=value.source,
                    display_value=value.masked_value,
                )
                for value in provider.values
            ],
        )

    def _translate_reason(self, reason: str) -> str:
        normalized = reason.strip()
        translations = {
            "Provider Ä‘ang bá»‹ táº¯t trong agent settings.": "This provider is disabled in workspace settings.",
            "Provider Ä‘ang bá»‹ táº¯t.": "This provider is disabled in workspace settings.",
            "ÄÃ£ cÃ³ cáº¥u hÃ¬nh nhÆ°ng adapter runtime chÆ°a Ä‘Æ°á»£c implement trong backend.": "Configuration is saved, but the backend runtime for this provider is not enabled yet.",
            "ChÆ°a cÃ³ adapter runtime.": "This provider is configured for settings only. Runtime support is not enabled yet.",
            "Sáºµn sÃ ng sá»­ dá»¥ng.": "Ready to use.",
            "Sáºµn sÃ ng.": "Ready to use.",
            "Model chÆ°a tá»“n táº¡i trong catalog.": "The selected model is no longer present in the curated catalog.",
        }
        if normalized in translations:
            return translations[normalized]
        if normalized.startswith("Thiáº¿u cáº¥u hÃ¬nh: "):
            fields = normalized.removeprefix("Thiáº¿u cáº¥u hÃ¬nh: ").rstrip(".")
            return f"Missing required configuration: {fields}."
        if normalized.startswith("Thiếu cấu hình: "):
            fields = normalized.removeprefix("Thiếu cấu hình: ").rstrip(".")
            return f"Missing required configuration: {fields}."
        return normalized

    def _workspace_name(self, workspace_id: str) -> str:
        if workspace_id == self._settings.default_workspace_id:
            return self._settings.default_workspace_name
        return workspace_id.replace("-", " ").title()

    def _default_assignment(self, task_type: TaskType) -> tuple[str, str]:
        if task_type == "ontology_extraction":
            raise ValueError("Ontology extraction model must be selected explicitly.")
        return self._settings.default_provider, self._settings.default_model

    def _runtime_env_value(self, field_key: str) -> str | None:
        attr_by_env = {
            "OPENAI_API_KEY": self._settings.openai_api_key,
            "OPENAI_BASE_URL": self._settings.openai_base_url,
            "OPENROUTER_API_KEY": self._settings.openrouter_api_key,
            "OPENROUTER_BASE_URL": self._settings.openrouter_base_url,
            "CLOUDFLARE_API_KEY": self._settings.cloudflare_api_key,
            "CLOUDFLARE_ACCOUNT_ID": self._settings.cloudflare_account_id,
            "ANTHROPIC_API_KEY": self._settings.anthropic_api_key,
            "ANTHROPIC_BASE_URL": self._settings.anthropic_base_url,
            "GOOGLE_API_KEY": self._settings.google_api_key,
            "OLLAMA_BASE_URL": self._settings.ollama_base_url,
        }
        return attr_by_env.get(field_key)

    @staticmethod
    def _cloudflare_base_url(account_id: str | None) -> str | None:
        if not account_id:
            return None
        return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"

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
