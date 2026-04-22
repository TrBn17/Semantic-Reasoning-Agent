"""add task runtime audit tables

Revision ID: 20260422_add_task_runtime_audit_tables
Revises: 20260422_add_knowledge_pack_tables
Create Date: 2026-04-22 12:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260422_add_task_runtime_audit_tables"
down_revision: str | Sequence[str] | None = "20260422_add_knowledge_pack_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "task_runs" not in existing_tables:
        op.create_table(
            "task_runs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("workflow_id", sa.String(length=128), nullable=False),
            sa.Column("task_type", sa.String(length=64), nullable=False, server_default="chat.answer"),
            sa.Column("output_type", sa.String(length=64), nullable=False, server_default="answer"),
            sa.Column("stop_reason", sa.String(length=64), nullable=False, server_default="completed"),
            sa.Column("grounded", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("content", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    task_run_indexes = {index["name"] for index in inspector.get_indexes("task_runs")}
    task_runs_workspace_index = op.f("ix_task_runs_workspace_id")
    if task_runs_workspace_index not in task_run_indexes:
        op.create_index(task_runs_workspace_index, "task_runs", ["workspace_id"], unique=False)

    task_runs_workflow_index = op.f("ix_task_runs_workflow_id")
    if task_runs_workflow_index not in task_run_indexes:
        op.create_index(task_runs_workflow_index, "task_runs", ["workflow_id"], unique=False)

    if "task_run_steps" not in existing_tables:
        op.create_table(
            "task_run_steps",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_run_id", sa.String(length=64), nullable=False),
            sa.Column("stage", sa.String(length=64), nullable=False),
            sa.Column("detail", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    task_run_step_indexes = {index["name"] for index in inspector.get_indexes("task_run_steps")}
    task_run_steps_task_run_index = op.f("ix_task_run_steps_task_run_id")
    if task_run_steps_task_run_index not in task_run_step_indexes:
        op.create_index(task_run_steps_task_run_index, "task_run_steps", ["task_run_id"], unique=False)

    task_run_steps_stage_index = op.f("ix_task_run_steps_stage")
    if task_run_steps_stage_index not in task_run_step_indexes:
        op.create_index(task_run_steps_stage_index, "task_run_steps", ["stage"], unique=False)

    if "tool_calls" not in existing_tables:
        op.create_table(
            "tool_calls",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_run_id", sa.String(length=64), nullable=False),
            sa.Column("tool_name", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    tool_call_indexes = {index["name"] for index in inspector.get_indexes("tool_calls")}
    tool_calls_task_run_index = op.f("ix_tool_calls_task_run_id")
    if tool_calls_task_run_index not in tool_call_indexes:
        op.create_index(tool_calls_task_run_index, "tool_calls", ["task_run_id"], unique=False)

    tool_calls_tool_name_index = op.f("ix_tool_calls_tool_name")
    if tool_calls_tool_name_index not in tool_call_indexes:
        op.create_index(tool_calls_tool_name_index, "tool_calls", ["tool_name"], unique=False)

    if "evidence_bundles" not in existing_tables:
        op.create_table(
            "evidence_bundles",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_run_id", sa.String(length=64), nullable=False),
            sa.Column("summary", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    evidence_bundle_indexes = {index["name"] for index in inspector.get_indexes("evidence_bundles")}
    evidence_bundles_task_run_index = op.f("ix_evidence_bundles_task_run_id")
    if evidence_bundles_task_run_index not in evidence_bundle_indexes:
        op.create_index(evidence_bundles_task_run_index, "evidence_bundles", ["task_run_id"], unique=False)

    if "evidence_conflicts" not in existing_tables:
        op.create_table(
            "evidence_conflicts",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_run_id", sa.String(length=64), nullable=False),
            sa.Column("conflict_type", sa.String(length=64), nullable=False),
            sa.Column("severity", sa.String(length=32), nullable=False),
            sa.Column("detail", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    evidence_conflict_indexes = {index["name"] for index in inspector.get_indexes("evidence_conflicts")}
    evidence_conflicts_task_run_index = op.f("ix_evidence_conflicts_task_run_id")
    if evidence_conflicts_task_run_index not in evidence_conflict_indexes:
        op.create_index(evidence_conflicts_task_run_index, "evidence_conflicts", ["task_run_id"], unique=False)

    evidence_conflicts_type_index = op.f("ix_evidence_conflicts_conflict_type")
    if evidence_conflicts_type_index not in evidence_conflict_indexes:
        op.create_index(evidence_conflicts_type_index, "evidence_conflicts", ["conflict_type"], unique=False)

    if "output_routes" not in existing_tables:
        op.create_table(
            "output_routes",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_run_id", sa.String(length=64), nullable=False),
            sa.Column("output_type", sa.String(length=64), nullable=False),
            sa.Column("reason", sa.String(length=128), nullable=False),
            sa.Column("grounded", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    output_route_indexes = {index["name"] for index in inspector.get_indexes("output_routes")}
    output_routes_task_run_index = op.f("ix_output_routes_task_run_id")
    if output_routes_task_run_index not in output_route_indexes:
        op.create_index(output_routes_task_run_index, "output_routes", ["task_run_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "output_routes" in existing_tables:
        output_route_indexes = {index["name"] for index in inspector.get_indexes("output_routes")}
        output_routes_task_run_index = op.f("ix_output_routes_task_run_id")
        if output_routes_task_run_index in output_route_indexes:
            op.drop_index(output_routes_task_run_index, table_name="output_routes")
        op.drop_table("output_routes")

    if "evidence_conflicts" in existing_tables:
        evidence_conflict_indexes = {index["name"] for index in inspector.get_indexes("evidence_conflicts")}
        evidence_conflicts_type_index = op.f("ix_evidence_conflicts_conflict_type")
        if evidence_conflicts_type_index in evidence_conflict_indexes:
            op.drop_index(evidence_conflicts_type_index, table_name="evidence_conflicts")

        evidence_conflicts_task_run_index = op.f("ix_evidence_conflicts_task_run_id")
        if evidence_conflicts_task_run_index in evidence_conflict_indexes:
            op.drop_index(evidence_conflicts_task_run_index, table_name="evidence_conflicts")

        op.drop_table("evidence_conflicts")

    if "evidence_bundles" in existing_tables:
        evidence_bundle_indexes = {index["name"] for index in inspector.get_indexes("evidence_bundles")}
        evidence_bundles_task_run_index = op.f("ix_evidence_bundles_task_run_id")
        if evidence_bundles_task_run_index in evidence_bundle_indexes:
            op.drop_index(evidence_bundles_task_run_index, table_name="evidence_bundles")
        op.drop_table("evidence_bundles")

    if "tool_calls" in existing_tables:
        tool_call_indexes = {index["name"] for index in inspector.get_indexes("tool_calls")}
        tool_calls_tool_name_index = op.f("ix_tool_calls_tool_name")
        if tool_calls_tool_name_index in tool_call_indexes:
            op.drop_index(tool_calls_tool_name_index, table_name="tool_calls")

        tool_calls_task_run_index = op.f("ix_tool_calls_task_run_id")
        if tool_calls_task_run_index in tool_call_indexes:
            op.drop_index(tool_calls_task_run_index, table_name="tool_calls")

        op.drop_table("tool_calls")

    if "task_run_steps" in existing_tables:
        task_run_step_indexes = {index["name"] for index in inspector.get_indexes("task_run_steps")}
        task_run_steps_stage_index = op.f("ix_task_run_steps_stage")
        if task_run_steps_stage_index in task_run_step_indexes:
            op.drop_index(task_run_steps_stage_index, table_name="task_run_steps")

        task_run_steps_task_run_index = op.f("ix_task_run_steps_task_run_id")
        if task_run_steps_task_run_index in task_run_step_indexes:
            op.drop_index(task_run_steps_task_run_index, table_name="task_run_steps")

        op.drop_table("task_run_steps")

    if "task_runs" in existing_tables:
        task_run_indexes = {index["name"] for index in inspector.get_indexes("task_runs")}
        task_runs_workflow_index = op.f("ix_task_runs_workflow_id")
        if task_runs_workflow_index in task_run_indexes:
            op.drop_index(task_runs_workflow_index, table_name="task_runs")

        task_runs_workspace_index = op.f("ix_task_runs_workspace_id")
        if task_runs_workspace_index in task_run_indexes:
            op.drop_index(task_runs_workspace_index, table_name="task_runs")

        op.drop_table("task_runs")
