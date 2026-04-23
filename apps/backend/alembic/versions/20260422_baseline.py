"""Baseline schema for the backend ORM.

Revision ID: 20260422_baseline
Revises:
Create Date: 2026-04-22 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260422_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("allow_chat_model_override", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("policy_config", sa.JSON(), nullable=False),
        sa.Column("tool_assignments", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_profiles_status"), "agent_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_agent_profiles_workspace_id"), "agent_profiles", ["workspace_id"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("agent_profile_id", sa.String(length=64), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("uses_model_override", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_agent_profile_id"), "conversations", ["agent_profile_id"], unique=False)
    op.create_index(op.f("ix_conversations_workspace_id"), "conversations", ["workspace_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("parser_version", sa.String(length=128), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("ingestion_options", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_object_key", sa.Text(), nullable=True),
        sa.Column("source_content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("binary_content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_document_type"), "documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_index(op.f("ix_documents_workspace_id"), "documents", ["workspace_id"], unique=False)

    op.create_table(
        "knowledge_packs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_packs_status"), "knowledge_packs", ["status"], unique=False)
    op.create_index(op.f("ix_knowledge_packs_workspace_id"), "knowledge_packs", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_graph_drafts",
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("based_on_version_id", sa.String(length=64), nullable=True),
        sa.Column("ontology_title", sa.String(length=255), nullable=True),
        sa.Column("ontology_summary", sa.Text(), nullable=True),
        sa.Column("node_patches", sa.JSON(), nullable=False),
        sa.Column("relation_patches", sa.JSON(), nullable=False),
        sa.Column("entity_type_patches", sa.JSON(), nullable=False),
        sa.Column("relation_type_patches", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("workspace_id"),
    )

    op.create_table(
        "ontology_versions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("source_build_id", sa.String(length=64), nullable=False),
        sa.Column("ontology_title", sa.String(length=255), nullable=True),
        sa.Column("ontology_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_versions_source_build_id"), "ontology_versions", ["source_build_id"], unique=False)
    op.create_index(op.f("ix_ontology_versions_workspace_id"), "ontology_versions", ["workspace_id"], unique=False)

    op.create_table(
        "provider_configs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("env_values", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_provider_configs_provider"), "provider_configs", ["provider"], unique=False)
    op.create_index(op.f("ix_provider_configs_workspace_id"), "provider_configs", ["workspace_id"], unique=False)

    op.create_table(
        "provider_secrets",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("field_key", sa.String(length=128), nullable=False),
        sa.Column("secret_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_provider_secrets_field_key"), "provider_secrets", ["field_key"], unique=False)
    op.create_index(op.f("ix_provider_secrets_provider"), "provider_secrets", ["provider"], unique=False)
    op.create_index(op.f("ix_provider_secrets_workspace_id"), "provider_secrets", ["workspace_id"], unique=False)

    op.create_table(
        "task_model_configs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_model_configs_task_type"), "task_model_configs", ["task_type"], unique=False)
    op.create_index(op.f("ix_task_model_configs_workspace_id"), "task_model_configs", ["workspace_id"], unique=False)

    op.create_table(
        "task_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("output_type", sa.String(length=64), nullable=False),
        sa.Column("stop_reason", sa.String(length=64), nullable=False),
        sa.Column("grounded", sa.Boolean(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_runs_workflow_id"), "task_runs", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_task_runs_workspace_id"), "task_runs", ["workspace_id"], unique=False)

    op.create_table(
        "agent_profile_task_models",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("agent_profile_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_profile_id"], ["agent_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_profile_task_models_agent_profile_id"),
        "agent_profile_task_models",
        ["agent_profile_id"],
        unique=False,
    )
    op.create_index(op.f("ix_agent_profile_task_models_task_type"), "agent_profile_task_models", ["task_type"], unique=False)

    op.create_table(
        "document_artifacts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("public_url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_artifacts_artifact_type"), "document_artifacts", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_document_artifacts_document_id"), "document_artifacts", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_artifacts_workspace_id"), "document_artifacts", ["workspace_id"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("document_title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("heading_path", sa.Text(), nullable=True),
        sa.Column("table_index", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("detected_table_id", sa.String(length=255), nullable=True),
        sa.Column("row_start", sa.Integer(), nullable=True),
        sa.Column("row_end", sa.Integer(), nullable=True),
        sa.Column("column_headers", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_chunks_document_type"), "document_chunks", ["document_type"], unique=False)
    op.create_index(op.f("ix_document_chunks_workspace_id"), "document_chunks", ["workspace_id"], unique=False)

    op.create_table(
        "document_extraction_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("schema_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("parser_version", sa.String(length=128), nullable=True),
        sa.Column("use_llm", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_extraction_runs_document_id"), "document_extraction_runs", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_extraction_runs_status"), "document_extraction_runs", ["status"], unique=False)
    op.create_index(op.f("ix_document_extraction_runs_workspace_id"), "document_extraction_runs", ["workspace_id"], unique=False)

    op.create_table(
        "document_jobs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_jobs_document_id"), "document_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_jobs_status"), "document_jobs", ["status"], unique=False)

    op.create_table(
        "evidence_bundles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_run_id", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_bundles_task_run_id"), "evidence_bundles", ["task_run_id"], unique=False)

    op.create_table(
        "evidence_conflicts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_run_id", sa.String(length=64), nullable=False),
        sa.Column("conflict_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_conflicts_conflict_type"), "evidence_conflicts", ["conflict_type"], unique=False)
    op.create_index(op.f("ix_evidence_conflicts_task_run_id"), "evidence_conflicts", ["task_run_id"], unique=False)

    op.create_table(
        "knowledge_pack_documents",
        sa.Column("knowledge_pack_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_pack_id"], ["knowledge_packs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("knowledge_pack_id", "document_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)

    op.create_table(
        "ontology_builds",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=True),
        sa.Column("ontology_title", sa.String(length=255), nullable=True),
        sa.Column("ontology_summary", sa.Text(), nullable=True),
        sa.Column("merge_mode", sa.String(length=32), nullable=False),
        sa.Column("extraction_provider", sa.String(length=64), nullable=True),
        sa.Column("extraction_model", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_version_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_builds_document_id"), "ontology_builds", ["document_id"], unique=False)
    op.create_index(op.f("ix_ontology_builds_status"), "ontology_builds", ["status"], unique=False)
    op.create_index(op.f("ix_ontology_builds_workspace_id"), "ontology_builds", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_build_steps",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["build_id"], ["ontology_builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_build_steps_build_id"), "ontology_build_steps", ["build_id"], unique=False)
    op.create_index(op.f("ix_ontology_build_steps_status"), "ontology_build_steps", ["status"], unique=False)

    op.create_table(
        "ontology_candidate_entities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("resolution_key", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("merged_into_entity_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["ontology_builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_candidate_entities_build_id"), "ontology_candidate_entities", ["build_id"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_entities_document_id"), "ontology_candidate_entities", ["document_id"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_entities_resolution_key"), "ontology_candidate_entities", ["resolution_key"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_entities_status"), "ontology_candidate_entities", ["status"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_entities_workspace_id"), "ontology_candidate_entities", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_candidate_relations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.String(length=64), nullable=True),
        sa.Column("target_entity_id", sa.String(length=64), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("target_name", sa.String(length=255), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["ontology_builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_candidate_relations_build_id"), "ontology_candidate_relations", ["build_id"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_relations_document_id"), "ontology_candidate_relations", ["document_id"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_relations_status"), "ontology_candidate_relations", ["status"], unique=False)
    op.create_index(op.f("ix_ontology_candidate_relations_workspace_id"), "ontology_candidate_relations", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_entities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("resolution_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("source_build_id", sa.String(length=64), nullable=False),
        sa.Column("source_document_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["ontology_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_entities_resolution_key"), "ontology_entities", ["resolution_key"], unique=False)
    op.create_index(op.f("ix_ontology_entities_source_build_id"), "ontology_entities", ["source_build_id"], unique=False)
    op.create_index(op.f("ix_ontology_entities_source_document_id"), "ontology_entities", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_ontology_entities_version_id"), "ontology_entities", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_entities_workspace_id"), "ontology_entities", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_entity_type_definitions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("examples", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["ontology_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_entity_type_definitions_name"), "ontology_entity_type_definitions", ["name"], unique=False)
    op.create_index(op.f("ix_ontology_entity_type_definitions_version_id"), "ontology_entity_type_definitions", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_entity_type_definitions_workspace_id"), "ontology_entity_type_definitions", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_relation_type_definitions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("allowed_source_targets", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["ontology_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_relation_type_definitions_name"), "ontology_relation_type_definitions", ["name"], unique=False)
    op.create_index(op.f("ix_ontology_relation_type_definitions_version_id"), "ontology_relation_type_definitions", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_relation_type_definitions_workspace_id"), "ontology_relation_type_definitions", ["workspace_id"], unique=False)

    op.create_table(
        "ontology_relations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.String(length=64), nullable=False),
        sa.Column("target_entity_id", sa.String(length=64), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_build_id", sa.String(length=64), nullable=False),
        sa.Column("source_document_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["ontology_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ontology_relations_source_build_id"), "ontology_relations", ["source_build_id"], unique=False)
    op.create_index(op.f("ix_ontology_relations_source_document_id"), "ontology_relations", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_ontology_relations_source_entity_id"), "ontology_relations", ["source_entity_id"], unique=False)
    op.create_index(op.f("ix_ontology_relations_target_entity_id"), "ontology_relations", ["target_entity_id"], unique=False)
    op.create_index(op.f("ix_ontology_relations_version_id"), "ontology_relations", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_relations_workspace_id"), "ontology_relations", ["workspace_id"], unique=False)

    op.create_table(
        "output_routes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_run_id", sa.String(length=64), nullable=False),
        sa.Column("output_type", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=False),
        sa.Column("grounded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_output_routes_task_run_id"), "output_routes", ["task_run_id"], unique=False)

    op.create_table(
        "task_run_steps",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_run_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_run_steps_stage"), "task_run_steps", ["stage"], unique=False)
    op.create_index(op.f("ix_task_run_steps_task_run_id"), "task_run_steps", ["task_run_id"], unique=False)

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_run_id", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_calls_task_run_id"), "tool_calls", ["task_run_id"], unique=False)
    op.create_index(op.f("ix_tool_calls_tool_name"), "tool_calls", ["tool_name"], unique=False)

    op.create_table(
        "search_tool_configs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("tool_type", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("default_top_k", sa.Integer(), nullable=False),
        sa.Column("collection_target", sa.String(length=64), nullable=False),
        sa.Column("document_ids", sa.JSON(), nullable=False),
        sa.Column("bm25_enabled", sa.Boolean(), nullable=False),
        sa.Column("fusion_strategy", sa.String(length=32), nullable=False),
        sa.Column("ontology_scope", sa.String(length=32), nullable=False),
        sa.Column("ontology_version_id", sa.String(length=64), nullable=True),
        sa.Column("graph_search_type", sa.String(length=16), nullable=False),
        sa.Column("reranker", sa.String(length=32), nullable=False),
        sa.Column("config_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", "tool_type", "name", name="uq_search_tool_configs_name"
        ),
    )
    op.create_index(
        op.f("ix_search_tool_configs_workspace_id"),
        "search_tool_configs",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_tool_configs_tool_type"),
        "search_tool_configs",
        ["tool_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_search_tool_configs_tool_type"), table_name="search_tool_configs")
    op.drop_index(op.f("ix_search_tool_configs_workspace_id"), table_name="search_tool_configs")
    op.drop_table("search_tool_configs")

    op.drop_index(op.f("ix_tool_calls_tool_name"), table_name="tool_calls")
    op.drop_index(op.f("ix_tool_calls_task_run_id"), table_name="tool_calls")
    op.drop_table("tool_calls")

    op.drop_index(op.f("ix_task_run_steps_task_run_id"), table_name="task_run_steps")
    op.drop_index(op.f("ix_task_run_steps_stage"), table_name="task_run_steps")
    op.drop_table("task_run_steps")

    op.drop_index(op.f("ix_output_routes_task_run_id"), table_name="output_routes")
    op.drop_table("output_routes")

    op.drop_index(op.f("ix_ontology_relations_workspace_id"), table_name="ontology_relations")
    op.drop_index(op.f("ix_ontology_relations_version_id"), table_name="ontology_relations")
    op.drop_index(op.f("ix_ontology_relations_target_entity_id"), table_name="ontology_relations")
    op.drop_index(op.f("ix_ontology_relations_source_entity_id"), table_name="ontology_relations")
    op.drop_index(op.f("ix_ontology_relations_source_document_id"), table_name="ontology_relations")
    op.drop_index(op.f("ix_ontology_relations_source_build_id"), table_name="ontology_relations")
    op.drop_table("ontology_relations")

    op.drop_index(
        op.f("ix_ontology_relation_type_definitions_workspace_id"),
        table_name="ontology_relation_type_definitions",
    )
    op.drop_index(
        op.f("ix_ontology_relation_type_definitions_version_id"),
        table_name="ontology_relation_type_definitions",
    )
    op.drop_index(
        op.f("ix_ontology_relation_type_definitions_name"),
        table_name="ontology_relation_type_definitions",
    )
    op.drop_table("ontology_relation_type_definitions")

    op.drop_index(
        op.f("ix_ontology_entity_type_definitions_workspace_id"),
        table_name="ontology_entity_type_definitions",
    )
    op.drop_index(
        op.f("ix_ontology_entity_type_definitions_version_id"),
        table_name="ontology_entity_type_definitions",
    )
    op.drop_index(
        op.f("ix_ontology_entity_type_definitions_name"),
        table_name="ontology_entity_type_definitions",
    )
    op.drop_table("ontology_entity_type_definitions")

    op.drop_index(op.f("ix_ontology_entities_workspace_id"), table_name="ontology_entities")
    op.drop_index(op.f("ix_ontology_entities_version_id"), table_name="ontology_entities")
    op.drop_index(op.f("ix_ontology_entities_source_document_id"), table_name="ontology_entities")
    op.drop_index(op.f("ix_ontology_entities_source_build_id"), table_name="ontology_entities")
    op.drop_index(op.f("ix_ontology_entities_resolution_key"), table_name="ontology_entities")
    op.drop_table("ontology_entities")

    op.drop_index(op.f("ix_ontology_candidate_relations_workspace_id"), table_name="ontology_candidate_relations")
    op.drop_index(op.f("ix_ontology_candidate_relations_status"), table_name="ontology_candidate_relations")
    op.drop_index(op.f("ix_ontology_candidate_relations_document_id"), table_name="ontology_candidate_relations")
    op.drop_index(op.f("ix_ontology_candidate_relations_build_id"), table_name="ontology_candidate_relations")
    op.drop_table("ontology_candidate_relations")

    op.drop_index(op.f("ix_ontology_candidate_entities_workspace_id"), table_name="ontology_candidate_entities")
    op.drop_index(op.f("ix_ontology_candidate_entities_status"), table_name="ontology_candidate_entities")
    op.drop_index(op.f("ix_ontology_candidate_entities_resolution_key"), table_name="ontology_candidate_entities")
    op.drop_index(op.f("ix_ontology_candidate_entities_document_id"), table_name="ontology_candidate_entities")
    op.drop_index(op.f("ix_ontology_candidate_entities_build_id"), table_name="ontology_candidate_entities")
    op.drop_table("ontology_candidate_entities")

    op.drop_index(op.f("ix_ontology_build_steps_status"), table_name="ontology_build_steps")
    op.drop_index(op.f("ix_ontology_build_steps_build_id"), table_name="ontology_build_steps")
    op.drop_table("ontology_build_steps")

    op.drop_index(op.f("ix_ontology_builds_workspace_id"), table_name="ontology_builds")
    op.drop_index(op.f("ix_ontology_builds_status"), table_name="ontology_builds")
    op.drop_index(op.f("ix_ontology_builds_document_id"), table_name="ontology_builds")
    op.drop_table("ontology_builds")

    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_table("knowledge_pack_documents")

    op.drop_index(op.f("ix_evidence_conflicts_task_run_id"), table_name="evidence_conflicts")
    op.drop_index(op.f("ix_evidence_conflicts_conflict_type"), table_name="evidence_conflicts")
    op.drop_table("evidence_conflicts")

    op.drop_index(op.f("ix_evidence_bundles_task_run_id"), table_name="evidence_bundles")
    op.drop_table("evidence_bundles")

    op.drop_index(op.f("ix_document_jobs_status"), table_name="document_jobs")
    op.drop_index(op.f("ix_document_jobs_document_id"), table_name="document_jobs")
    op.drop_table("document_jobs")

    op.drop_index(op.f("ix_document_extraction_runs_workspace_id"), table_name="document_extraction_runs")
    op.drop_index(op.f("ix_document_extraction_runs_status"), table_name="document_extraction_runs")
    op.drop_index(op.f("ix_document_extraction_runs_document_id"), table_name="document_extraction_runs")
    op.drop_table("document_extraction_runs")

    op.drop_index(op.f("ix_document_chunks_workspace_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_type"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index(op.f("ix_document_artifacts_workspace_id"), table_name="document_artifacts")
    op.drop_index(op.f("ix_document_artifacts_document_id"), table_name="document_artifacts")
    op.drop_index(op.f("ix_document_artifacts_artifact_type"), table_name="document_artifacts")
    op.drop_table("document_artifacts")

    op.drop_index(op.f("ix_agent_profile_task_models_task_type"), table_name="agent_profile_task_models")
    op.drop_index(op.f("ix_agent_profile_task_models_agent_profile_id"), table_name="agent_profile_task_models")
    op.drop_table("agent_profile_task_models")

    op.drop_index(op.f("ix_task_runs_workspace_id"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_workflow_id"), table_name="task_runs")
    op.drop_table("task_runs")

    op.drop_index(op.f("ix_task_model_configs_workspace_id"), table_name="task_model_configs")
    op.drop_index(op.f("ix_task_model_configs_task_type"), table_name="task_model_configs")
    op.drop_table("task_model_configs")

    op.drop_index(op.f("ix_provider_secrets_workspace_id"), table_name="provider_secrets")
    op.drop_index(op.f("ix_provider_secrets_provider"), table_name="provider_secrets")
    op.drop_index(op.f("ix_provider_secrets_field_key"), table_name="provider_secrets")
    op.drop_table("provider_secrets")

    op.drop_index(op.f("ix_provider_configs_workspace_id"), table_name="provider_configs")
    op.drop_index(op.f("ix_provider_configs_provider"), table_name="provider_configs")
    op.drop_table("provider_configs")

    op.drop_index(op.f("ix_ontology_versions_workspace_id"), table_name="ontology_versions")
    op.drop_index(op.f("ix_ontology_versions_source_build_id"), table_name="ontology_versions")
    op.drop_table("ontology_versions")

    op.drop_table("ontology_graph_drafts")

    op.drop_index(op.f("ix_knowledge_packs_workspace_id"), table_name="knowledge_packs")
    op.drop_index(op.f("ix_knowledge_packs_status"), table_name="knowledge_packs")
    op.drop_table("knowledge_packs")

    op.drop_index(op.f("ix_documents_workspace_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_type"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_conversations_workspace_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_agent_profile_id"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index(op.f("ix_agent_profiles_workspace_id"), table_name="agent_profiles")
    op.drop_index(op.f("ix_agent_profiles_status"), table_name="agent_profiles")
    op.drop_table("agent_profiles")
