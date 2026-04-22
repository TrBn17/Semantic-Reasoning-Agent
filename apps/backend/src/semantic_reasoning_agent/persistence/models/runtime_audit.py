from __future__ import annotations

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, utc_now


class TaskRunORM(Base):
    __tablename__ = "task_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    workflow_id: Mapped[str] = mapped_column(String(128), index=True)
    task_type: Mapped[str] = mapped_column(String(64), default="chat.answer")
    output_type: Mapped[str] = mapped_column(String(64), default="answer")
    stop_reason: Mapped[str] = mapped_column(String(64), default="completed")
    grounded: Mapped[bool] = mapped_column(default=True)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TaskRunStepORM(Base):
    __tablename__ = "task_run_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ToolCallAuditORM(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EvidenceBundleORM(Base):
    __tablename__ = "evidence_bundles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EvidenceConflictORM(Base):
    __tablename__ = "evidence_conflicts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    conflict_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OutputRouteORM(Base):
    __tablename__ = "output_routes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    output_type: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(128))
    grounded: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utc_now)
