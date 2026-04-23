from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .base import Base, utc_now


class SearchToolConfigORM(Base):
    """Persisted configuration for a super-search tool instance.

    One row = one user-created tool instance (either a `supersearch.docs`
    or a `supersearch.graph` configuration). Holds enough data so the
    tool can execute a query with zero extra user input at invoke time.
    """

    __tablename__ = "search_tool_configs"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "tool_type", "name", name="uq_search_tool_configs_name"
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    tool_type: Mapped[str] = mapped_column(String(16), index=True)  # docs | graph
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")

    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    default_top_k: Mapped[int] = mapped_column(Integer, default=5)

    # docs-specific
    collection_target: Mapped[str] = mapped_column(String(64), default="workspace")
    document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    bm25_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    fusion_strategy: Mapped[str] = mapped_column(String(32), default="semantic_only")

    # graph-specific
    ontology_scope: Mapped[str] = mapped_column(String(32), default="published")
    ontology_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    graph_search_type: Mapped[str] = mapped_column(String(16), default="combined")
    reranker: Mapped[str] = mapped_column(String(32), default="rrf")

    config_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
