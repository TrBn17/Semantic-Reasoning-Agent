from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolConstraints, ToolEnvelope
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.chat import SendMessageRequest
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.schemas.tools import CitationAnchorSchema, EvidenceSchema, ProvenanceSchema
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime


@dataclass(frozen=True)
class TaskRuntimeResult:
    workflow_id: str
    content: str
    citations: list[Citation]
    evidence: list[EvidenceSchema]
    next_action_hints: list[str]
    tool_calls: list[dict[str, str | int | None]]


class TaskRuntimeService:
    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        tool_runtime: ToolRuntime,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._tool_runtime = tool_runtime
        self._tool_registry = tool_registry

    def resolve_request(
        self,
        request: TaskResolveRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> TaskRuntimeResult:
        workspace_id = request.workspace_id or self._settings.default_workspace_id
        task_id = str(uuid4())
        workflow_id = "task.resolve.chat"
        evidence: list[EvidenceSchema] = []
        citations: list[Citation] = []
        tool_calls: list[dict[str, str | int | None]] = []

        if request.use_retrieval and self._tool_enabled("retrieval.internal", request.enabled_tool_names):
            retrieval_result = self._tool_runtime.invoke(
                ToolEnvelope(
                    call_id=uuid4(),
                    tool_name="retrieval.internal",
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    task_type="chat.answer",
                    task_payload={"content": request.content},
                    arguments={
                        "query": request.content,
                        "document_ids": request.document_ids,
                        "top_k": request.top_k,
                    },
                    constraints=ToolConstraints(max_results=request.top_k),
                )
            )
            evidence.extend(_to_evidence_schema(item) for item in retrieval_result.evidence)
            tool_calls.append(
                {
                    "tool_name": retrieval_result.tool_name,
                    "status": retrieval_result.status,
                    "latency_ms": retrieval_result.latency_ms,
                    "trace_id": retrieval_result.meta.trace_id,
                }
            )
            citations.extend(
                _citation_from_evidence(item)
                for item in retrieval_result.evidence
                if item.source_type == "internal_chunk"
            )

        content = self._compose_answer(request.content, citations=citations)
        if not citations:
            content = self._fallback_answer(
                prompt=request.content,
                workspace_id=workspace_id,
                provider=provider,
                model=model,
                system_prompt=system_prompt,
            )

        return TaskRuntimeResult(
            workflow_id=workflow_id,
            content=content,
            citations=citations,
            evidence=evidence,
            next_action_hints=[],
            tool_calls=tool_calls,
        )

    def resolve_api_request(self, request: TaskResolveRequest) -> TaskResolveResponse:
        result = self.resolve_request(
            request,
            provider=request.provider,
            model=request.model,
        )
        return TaskResolveResponse(
            task_id=str(uuid4()),
            content=result.content,
            citations=result.citations,
        )

    def resolve_chat_request(
        self,
        payload: SendMessageRequest,
        *,
        provider: str,
        model: str,
        system_prompt: str | None = None,
    ) -> TaskRuntimeResult:
        return self.resolve_request(
            TaskResolveRequest(
                content=payload.content,
                workspace_id=payload.workspace_id,
                conversation_id=payload.conversation_id,
                provider=provider,
                model=model,
                use_retrieval=payload.use_retrieval,
                document_ids=payload.document_ids,
                top_k=payload.top_k,
                enabled_tool_names=payload.enabled_tool_names,
            ),
            provider=provider,
            model=model,
            system_prompt=system_prompt,
        )

    def _fallback_answer(
        self,
        *,
        prompt: str,
        workspace_id: str,
        provider: str | None,
        model: str | None,
        system_prompt: str | None,
    ) -> str:
        if not provider or not model:
            return "No indexed document matched that question."
        if not self._model_config_service.is_ready(provider, model, workspace_id):
            return "No indexed document matched that question."
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return "No indexed document matched that question."
        response = adapter.run(
            messages=[LLMMessage(role="user", content=prompt)],
            tools=(),
            tool_choice="none",
            system=system_prompt,
            model=model,
        )
        return response.content or ""

    @staticmethod
    def _compose_answer(
        prompt: str,
        *,
        citations: list[Citation],
    ) -> str:
        if citations:
            lines = [f"Question: {prompt}", "Relevant context:"]
            for citation in citations:
                lines.append(f"- {citation.document_title} ({citation.location_label}): {citation.excerpt}")
            return "\n".join(lines)
        return "No indexed document matched that question."

    @staticmethod
    def _tool_enabled(tool_name: str, enabled_tool_names: list[str] | None) -> bool:
        if enabled_tool_names is None:
            return True
        return tool_name in enabled_tool_names


def _citation_from_evidence(evidence) -> Citation:  # noqa: ANN001
    document_type = "document"
    if evidence.page is not None:
        document_type = "pdf"
    elif evidence.sheet_name:
        document_type = "xlsx"
    elif evidence.row_range:
        document_type = "csv"
    elif evidence.section:
        document_type = "docx"
    row_start, row_end = _parse_row_range(evidence.row_range)
    return Citation(
        chunk_id=evidence.chunk_id or "",
        document_id=evidence.document_id or "",
        document_title=evidence.title,
        document_type=document_type,
        excerpt=evidence.content,
        location_label=evidence.citation_anchor.label,
        source_url=evidence.uri or "",
        page_number=evidence.page,
        heading_path=evidence.section,
        sheet_name=evidence.sheet_name,
        row_start=row_start,
        row_end=row_end,
    )


def _parse_row_range(row_range: str | None) -> tuple[int | None, int | None]:
    if not row_range or "-" not in row_range:
        return None, None
    start, end = row_range.split("-", 1)
    try:
        return int(start), int(end)
    except ValueError:
        return None, None


def _to_evidence_schema(evidence) -> EvidenceSchema:  # noqa: ANN001
    return EvidenceSchema(
        evidence_id=evidence.evidence_id,
        source_type=evidence.source_type,
        title=evidence.title,
        content=evidence.content,
        citation_anchor=CitationAnchorSchema(
            anchor_type=evidence.citation_anchor.anchor_type,
            label=evidence.citation_anchor.label,
            locator=evidence.citation_anchor.locator,
        ),
        provenance=ProvenanceSchema(
            workspace_id=evidence.provenance.workspace_id,
            captured_at=evidence.provenance.captured_at,
            source_id=evidence.provenance.source_id,
            tool_call_id=evidence.provenance.tool_call_id,
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
        entity_ids=list(evidence.entity_ids),
        relation_ids=list(evidence.relation_ids),
        score=evidence.score,
        trust_score=evidence.trust_score,
        freshness_ts=evidence.freshness_ts,
    )
