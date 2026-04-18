from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Semantic Reasoning Agent", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

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

    default_workspace_id: str = Field(default="workspace-demo", alias="DEFAULT_WORKSPACE_ID")
    default_workspace_name: str = Field(default="Demo Workspace", alias="DEFAULT_WORKSPACE_NAME")
    default_user_id: str = Field(default="user-demo", alias="DEFAULT_USER_ID")
    default_user_email: str = Field(default="demo@example.com", alias="DEFAULT_USER_EMAIL")
    default_user_name: str = Field(default="Demo User", alias="DEFAULT_USER_NAME")
    default_provider: str = Field(default="echo", alias="DEFAULT_PROVIDER")
    default_model: str = Field(default="local-echo", alias="DEFAULT_MODEL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ontology_llm_provider: str = Field(default="anthropic", alias="ONTOLOGY_LLM_PROVIDER")
    ontology_llm_model: str = Field(default="claude-sonnet-4-5", alias="ONTOLOGY_LLM_MODEL")
    ontology_prompt_version: str = Field(default="v1", alias="ONTOLOGY_PROMPT_VERSION")
    ontology_chunk_limit: int = Field(default=24, alias="ONTOLOGY_CHUNK_LIMIT")
    ontology_llm_enabled: bool = Field(default=True, alias="ONTOLOGY_LLM_ENABLED")

    object_store_backend: str = Field(default="postgres", alias="OBJECT_STORE_BACKEND")
    object_store_bucket: str = Field(default="semantic-artifacts", alias="OBJECT_STORE_BUCKET")
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    vector_store_backend: str = Field(default="postgres", alias="VECTOR_STORE_BACKEND")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection_name: str = Field(default="document_chunks", alias="QDRANT_COLLECTION_NAME")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
