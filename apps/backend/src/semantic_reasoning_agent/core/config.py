from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Semantic Reasoning Agent", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOW_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    database_url: str = Field(
        default="postgresql+psycopg://semantic:semantic@localhost:5432/semantic_reasoning",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        alias="CELERY_RESULT_BACKEND",
    )
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    celery_task_eager_propagates: bool = Field(
        default=False,
        alias="CELERY_TASK_EAGER_PROPAGATES",
    )
    neo4j_enabled: bool = Field(default=False, alias="NEO4J_ENABLED")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="semantic-neo4j", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    graphiti_enabled: bool = Field(default=False, alias="GRAPHITI_ENABLED")
    graphiti_database: str = Field(default="graphiti", alias="GRAPHITI_DATABASE")

    default_workspace_id: str = Field(default="workspace-demo", alias="DEFAULT_WORKSPACE_ID")
    default_workspace_name: str = Field(default="Demo Workspace", alias="DEFAULT_WORKSPACE_NAME")
    default_user_id: str = Field(default="user-demo", alias="DEFAULT_USER_ID")
    default_user_email: str = Field(default="demo@example.com", alias="DEFAULT_USER_EMAIL")
    default_user_name: str = Field(default="Demo User", alias="DEFAULT_USER_NAME")
    default_provider: str = Field(default="openai", alias="DEFAULT_PROVIDER")
    default_model: str = Field(default="gpt-5-mini", alias="DEFAULT_MODEL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str | None = Field(default=None, alias="ANTHROPIC_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    cloudflare_api_key: str | None = Field(default=None, alias="CLOUDFLARE_API_KEY")
    cloudflare_account_id: str | None = Field(default=None, alias="CLOUDFLARE_ACCOUNT_ID")
    default_embedding_provider: str = Field(
        default="cloudflare",
        alias="DEFAULT_EMBEDDING_PROVIDER",
    )
    default_embedding_model: str = Field(
        default="bge-m3",
        alias="DEFAULT_EMBEDDING_MODEL",
    )
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ontology_llm_provider: str | None = Field(default=None, alias="ONTOLOGY_LLM_PROVIDER")
    ontology_llm_model: str | None = Field(default=None, alias="ONTOLOGY_LLM_MODEL")
    ontology_prompt_version: str = Field(default="v2", alias="ONTOLOGY_PROMPT_VERSION")
    ontology_chunk_limit: int = Field(default=24, alias="ONTOLOGY_CHUNK_LIMIT")
    ontology_markdown_char_limit: int = Field(default=50000, alias="ONTOLOGY_MARKDOWN_CHAR_LIMIT")
    ontology_llm_enabled: bool = Field(default=True, alias="ONTOLOGY_LLM_ENABLED")
    ontology_extraction_max_tokens: int = Field(default=6000, alias="ONTOLOGY_EXTRACTION_MAX_TOKENS")
    ontology_extraction_reasoning_effort: str = Field(
        default="low",
        alias="ONTOLOGY_EXTRACTION_REASONING_EFFORT",
    )
    ontology_extraction_max_chunks: int = Field(default=8, alias="ONTOLOGY_EXTRACTION_MAX_CHUNKS")
    # 0 = one pass over the bounded markdown (see ontology_markdown_char_limit). >0 = sliding window.
    ontology_extraction_window: int = Field(default=0, alias="ONTOLOGY_EXTRACTION_WINDOW")
    ontology_extraction_overlap: int = Field(default=500, alias="ONTOLOGY_EXTRACTION_OVERLAP")
    ontology_extraction_entity_count_min: int = Field(
        default=3,
        alias="ONTOLOGY_EXTRACTION_ENTITY_COUNT_MIN",
    )
    ontology_extraction_entity_count_max: int = Field(
        default=50,
        alias="ONTOLOGY_EXTRACTION_ENTITY_COUNT_MAX",
    )
    ontology_classify_deferred_token: str = Field(
        default="pending",
        alias="ONTOLOGY_CLASSIFY_DEFERRED_TOKEN",
    )
    task_runtime_orchestration_mode: str = Field(
        default="legacy_static_plan",
        alias="TASK_RUNTIME_ORCHESTRATION_MODE",
    )
    task_runtime_react_enabled: bool = Field(
        default=True,
        alias="TASK_RUNTIME_REACT_ENABLED",
    )
    object_store_backend: str = Field(default="postgres", alias="OBJECT_STORE_BACKEND")
    object_store_bucket: str = Field(default="semantic-artifacts", alias="OBJECT_STORE_BUCKET")
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_public_base_url: str = Field(
        default="http://localhost:9000",
        alias="MINIO_PUBLIC_BASE_URL",
    )

    vector_store_backend: str = Field(default="qdrant", alias="VECTOR_STORE_BACKEND")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
