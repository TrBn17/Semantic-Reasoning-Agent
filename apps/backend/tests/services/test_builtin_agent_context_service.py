"""Tests for packaged SKILLS/MEMORY defaults and BuiltinAgentContextService."""

from __future__ import annotations

import json
from contextlib import contextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from semantic_reasoning_agent.domain.builtin_agent_roles import BUILTIN_AGENT_ROLES
from semantic_reasoning_agent.persistence.models.builtin_agent_context import BuiltinAgentContextORM
from semantic_reasoning_agent.services.builtin_agent_context_service import (
    BuiltinAgentContextService,
    read_packaged_file,
)


def test_packaged_skills_nonempty() -> None:
    for role in BUILTIN_AGENT_ROLES:
        skills = read_packaged_file(role, "SKILLS.md")
        assert len(skills.strip()) > 20


def test_record_episodic_note_rejects_invalid_role() -> None:
    svc = BuiltinAgentContextService(_fake_db_that_never_runs_sessions())
    out = json.loads(svc.record_episodic_note(workspace_id="w1", target_role="invalid", note="x"))
    assert out["status"] == "rejected"


def test_record_episodic_note_append_persists() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    BuiltinAgentContextORM.__table__.create(bind=engine, checkfirst=True)

    @contextmanager
    def session_ctx():
        s = Session(bind=engine)
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    class _Dm:
        def session(self):
            return session_ctx()

    svc = BuiltinAgentContextService(_Dm())
    svc.record_episodic_note(
        workspace_id="ws-1",
        target_role="docs",
        note="Remember: user prefers summaries.",
        mode="append",
    )
    sess = Session(bind=engine)
    row = sess.scalars(select(BuiltinAgentContextORM)).one()
    assert row.workspace_id == "ws-1"
    assert "prefers summaries" in (row.memory_body or "")
    sess.close()


def _fake_db_that_never_runs_sessions():
    class _F:
        def session(self):
            raise AssertionError("should not touch DB for rejected role")

    return _F()
