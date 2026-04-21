from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_envelope import OntologyContextRef, ToolConstraints, ToolEnvelope
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.chat import SendMessageRequest
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.schemas.tools import CitationAnchorSchema, EvidenceSchema, ProvenanceSchema
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime


@dataclass(frozen=True)
class TaskRuntimeResult:
    workflow_id: str
    content: str
    citations: list[Citation]
    evidence: list[EvidenceSchema]
    next_action_hints: list[str]


class TaskRuntimeService:
    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        tool_runtime: ToolRuntime,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._tool_runtime = tool_runtime

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
        next_action_hints: list[str] = []

        if request.use_retrieval:
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
            citations.extend(_citation_from_evidence(item) for item in retrieval_result.evidence if item.source_type == "internal_chunk")
            next_action_hints.extend(retrieval_result.next_action_hints)

        ontology_result = self._tool_runtime.invoke(
            ToolEnvelope(
                call_id=uuid4(),
                tool_name="ontology.lookup",
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                task_type="chat.answer",
                task_payload={"content": request.content},
                arguments={"mode": "entity_lookup", "query": request.content},
                ontology_context=OntologyContextRef(domain="workspace_ontology"),
            )
        )
        evidence.extend(_to_evidence_schema(item) for item in ontology_result.evidence)
        next_action_hints.extend(ontology_result.next_action_hints)

        graph_result = self._tool_runtime.invoke(
            ToolEnvelope(
                call_id=uuid4(),
                tool_name="graphiti.search",
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                task_type="chat.answer",
                task_payload={"content": request.content},
                arguments={"query": request.content, "max_results": request.top_k},
                ontology_context=OntologyContextRef(domain="workspace_runtime_graph"),
            )
        )
        evidence.extend(_to_evidence_schema(item) for item in graph_result.evidence)
        next_action_hints.extend(graph_result.next_action_hints)

        content = self._compose_answer(request.content, citations=citations, evidence=evidence)
        if not citations and not evidence:
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
            next_action_hints=sorted(set(next_action_hints)),
        )

    def resolve_api_request(self, request: TaskResolveRequest) -> TaskResolveResponse:
        result = self.resolve_request(request)
        return TaskResolveResponse(
            task_id=str(uuid4()),
            workflow_id=result.workflow_id,
            content=result.content,
            citations=result.citations,
            evidence=result.evidence,
            next_action_hints=result.next_action_hints,
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
            return "No indexed document or graph context matched that question."
        if not self._model_config_service.is_ready(provider, model, workspace_id):
            return "No indexed document or graph context matched that question."
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return "No indexed document or graph context matched that question."
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
        evidence: list[EvidenceSchema],
    ) -> str:
        if citations:
            lines = [f"Question: {prompt}", "Relevant context:"]
            for citation in citations:
                lines.append(f"- {citation.document_title} ({citation.location_label}): {citation.excerpt}")
            graph_lines = [
                item for item in evidence
                if item.source_type in {"graph_edge", "graph_node"}
            ]
            if graph_lines:
                lines.append("Graph context:")
                for item in graph_lines[:3]:
                    lines.append(f"- {item.title}: {item.content}")
            return "\n".join(lines)
        graph_lines = [item for item in evidence if item.source_type in {"graph_edge", "graph_node"}]
        if graph_lines:
            lines = [f"Question: {prompt}", "Graph context:"]
            for item in graph_lines[:5]:
                lines.append(f"- {item.title}: {item.content}")
            return "\n".join(lines)
        return "No indexed document or graph context matched that question."


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
