from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, utc_now


class BuiltinAgentContextORM(Base):
    """Workspace-scoped overrides for packaged SKILLS.md / MEMORY.md (built-in agents)."""

    __tablename__ = "builtin_agent_context"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_role: Mapped[str] = mapped_column(String(32))
    skills_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
