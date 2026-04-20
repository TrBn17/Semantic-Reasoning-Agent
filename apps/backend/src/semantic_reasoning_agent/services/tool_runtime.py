from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import Evidence, Provenance
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.tool_registry import ToolRegistry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ToolRuntime:
    """Execution wrapper around a ``ToolRegistry``."""

    def __init__(
        self,
        registry: ToolRegistry,
        audit_service: RuntimeAuditService | None = None,
    ) -> None:
        self._registry = registry
        self._audit_service = audit_service

    def invoke(
        self,
        envelope: ToolEnvelope,
        *,
        task_id: str | None = None,
        workflow_run_id: str | None = None,
    ) -> ToolResult:
        spec = self._registry.spec(envelope.tool_name)
        if spec is None:
            result = self._failed(
                envelope,
                error_code="unknown_tool",
                error_message=f"Tool '{envelope.tool_name}' is not registered.",
            )
            self._record(task_id, workflow_run_id, envelope, result)
            return result

        if spec.requires_confirmation:
            result = self._failed(
                envelope,
                error_code="confirmation_required",
                error_message=(
                    f"Tool '{spec.tool_name}' requires explicit confirmation; "
                    "the runtime cannot invoke it without an approved confirmation token."
                ),
            )
            self._record(task_id, workflow_run_id, envelope, result)
            return result

        tool = self._registry.get(envelope.tool_name)
        if tool is None:
            result = self._failed(
                envelope,
                error_code="unknown_tool",
                error_message=f"Tool '{envelope.tool_name}' is not registered.",
            )
            self._record(task_id, workflow_run_id, envelope, result)
            return result

        trace_id = str(uuid4())
        started_at = _utc_now()
        timeout_s = min(spec.timeout_ms, envelope.constraints.timeout_ms) / 1000.0

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.run, envelope)
                tool_result = future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            result = self._failed(
                envelope,
                error_code="timeout",
                error_message=f"Tool '{envelope.tool_name}' exceeded timeout of {timeout_s:.2f}s.",
                trace_id=trace_id,
                started_at=started_at,
            )
            self._record(task_id, workflow_run_id, envelope, result)
            return result
        except Exception as exc:  # noqa: BLE001
            result = self._failed(
                envelope,
                error_code="tool_exception",
                error_message=str(exc) or exc.__class__.__name__,
                trace_id=trace_id,
                started_at=started_at,
            )
            self._record(task_id, workflow_run_id, envelope, result)
            return result

        finished_at = _utc_now()
        latency_ms = int((finished_at - started_at).total_seconds() * 1000)
        normalized_evidence = tuple(
            self._normalize_evidence(evidence, envelope.call_id) for evidence in tool_result.evidence
        )
        final_result = ToolResult(
            call_id=envelope.call_id,
            tool_name=envelope.tool_name,
            status=tool_result.status,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=latency_ms,
            evidence=normalized_evidence,
            artifacts=tuple(tool_result.artifacts),
            state_patch=dict(tool_result.state_patch),
            next_action_hints=tuple(tool_result.next_action_hints),
            error_code=tool_result.error_code,
            error_message=tool_result.error_message,
            meta=ToolMeta(
                provider=tool_result.meta.provider,
                provider_version=tool_result.meta.provider_version,
                trace_id=trace_id,
            ),
        )
        self._record(task_id, workflow_run_id, envelope, final_result)
        return final_result

    def invoke_parallel(self, envelopes: Sequence[ToolEnvelope]) -> list[ToolResult]:
        parallelizable = [
            envelope
            for envelope in envelopes
            if (spec := self._registry.spec(envelope.tool_name)) is not None
            and spec.side_effect_level == "read_only"
            and spec.supports_parallel
        ]
        if len(parallelizable) != len(envelopes):
            return [self.invoke(envelope) for envelope in envelopes]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(envelopes))) as executor:
            futures = [executor.submit(self.invoke, envelope) for envelope in envelopes]
            return [future.result() for future in futures]

    @staticmethod
    def _normalize_evidence(evidence: Evidence, tool_call_id) -> Evidence:  # noqa: ANN001
        return Evidence(
            evidence_id=evidence.evidence_id,
            source_type=evidence.source_type,
            title=evidence.title,
            content=evidence.content,
            citation_anchor=evidence.citation_anchor,
            provenance=Provenance(
                workspace_id=evidence.provenance.workspace_id,
                captured_at=evidence.provenance.captured_at,
                source_id=evidence.provenance.source_id,
                tool_call_id=tool_call_id,
                parser_version=evidence.provenance.parser_version,
                extractor_version=evidence.provenance.extractor_version,
                model=evidence.provenance.model,
            ),
            summary=evidence.summary,
            uri=evidence.uri,
            document_id=evidence.document_id,
            chunk_id=evidence.chunk_id,
            page=evidence.page,
            section=evidence.section,
            sheet_name=evidence.sheet_name,
            row_range=evidence.row_range,
            entity_ids=evidence.entity_ids,
            relation_ids=evidence.relation_ids,
            score=evidence.score,
            trust_score=evidence.trust_score,
            freshness_ts=evidence.freshness_ts,
        )

    def _record(
        self,
        task_id: str | None,
        workflow_run_id: str | None,
        envelope: ToolEnvelope,
        result: ToolResult,
    ) -> None:
        if self._audit_service is None:
            return
        self._audit_service.record_tool_call(
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            envelope=envelope,
            result=result,
        )

    @staticmethod
    def _failed(
        envelope: ToolEnvelope,
        *,
        error_code: str,
        error_message: str,
        trace_id: str | None = None,
        started_at: datetime | None = None,
    ) -> ToolResult:
        started = started_at or _utc_now()
        finished = _utc_now()
        latency_ms = int((finished - started).total_seconds() * 1000)
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=envelope.tool_name,
            status="failed",
            started_at=started,
            finished_at=finished,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
            meta=ToolMeta(trace_id=trace_id),
        )
