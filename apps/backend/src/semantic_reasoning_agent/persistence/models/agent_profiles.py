from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base, utc_now


class AgentProfileORM(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    allow_chat_model_override: Mapped[bool] = mapped_column(default=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    policy_config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    task_models: Mapped[list["AgentProfileTaskModelORM"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="AgentProfileTaskModelORM.task_type",
    )


class KnowledgePackORM(Base):
    __tablename__ = "knowledge_packs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    documents: Mapped[list["KnowledgePackDocumentORM"]] = relationship(
        back_populates="knowledge_pack",
        cascade="all, delete-orphan",
        order_by="KnowledgePackDocumentORM.document_id",
    )


class KnowledgePackDocumentORM(Base):
    __tablename__ = "knowledge_pack_documents"

    knowledge_pack_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("knowledge_packs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    knowledge_pack: Mapped[KnowledgePackORM] = relationship(back_populates="documents")


class AgentProfileTaskModelORM(Base):
    __tablename__ = "agent_profile_task_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_profile_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("agent_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    profile: Mapped[AgentProfileORM] = relationship(back_populates="task_models")
