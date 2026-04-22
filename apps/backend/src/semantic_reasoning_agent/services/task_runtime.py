from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_envelope import OntologyContextRef, ToolConstraints, ToolEnvelope
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.agent_profiles import AgentProfileResponse
from semantic_reasoning_agent.schemas.chat import SendMessageRequest
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.schemas.tools import CitationAnchorSchema, EvidenceSchema, ProvenanceSchema
from semantic_reasoning_agent.services.agent_capability_service import (
    get_capability_preset,
    has_explicit_capability_config,
)
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.knowledge_pack_service import KnowledgePackService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime


@dataclass(frozen=True)
class TaskRuntimeResult:
    workflow_id: str
    content: str
    citations: list[Citation]
    evidence: list[EvidenceSchema]
    next_action_hints: list[str]


@dataclass(frozen=True)
class ToolPlanStep:
    tool_name: str
    arguments: dict[str, object]
    reason: str
    required: bool = False
    can_fallback: bool = True


@dataclass(frozen=True)
class AgentExecutionScope:
    allowed_tool_names: tuple[str, ...]
    allowed_tool_families: tuple[str, ...]
    knowledge_pack_ids: tuple[str, ...]
    derived_document_ids: tuple[str, ...]
    evidence_sources: tuple[str, ...]
    allow_model_only_fallback: bool
    capability_preset: str
    capability_configured: bool


class TaskRuntimeService:
    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        tool_runtime: ToolRuntime,
        conversation_service: ConversationService,
        agent_profile_service: AgentProfileService,
        knowledge_pack_service: KnowledgePackService,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._tool_runtime = tool_runtime
        self._conversation_service = conversation_service
        self._agent_profile_service = agent_profile_service
        self._knowledge_pack_service = knowledge_pack_service

    def resolve_request(
        self,
        request: TaskResolveRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> TaskRuntimeResult:
        workspace_id, profile = self._resolve_workspace_and_agent_profile(request)
        scope = self._build_execution_scope(
            profile,
            workspace_id=workspace_id,
            request_document_ids=request.document_ids,
        )
        task_id = str(uuid4())
        workflow_id = "task.resolve.chat"
        evidence: list[EvidenceSchema] = []
        citations: list[Citation] = []
        next_action_hints: list[str] = []
        plan = self._build_tool_plan(request, scope=scope)
        for step in plan:
            if step.tool_name not in scope.allowed_tool_names:
                if step.required:
                    next_action_hints.append(f"blocked:{step.tool_name}")
                continue
            result = self._invoke_step(
                step,
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                request=request,
            )
            for item in result.evidence:
                if item.source_type not in scope.evidence_sources:
                    continue
                evidence.append(_to_evidence_schema(item))
                if item.source_type == "internal_chunk":
                    citations.append(_citation_from_evidence(item))
            next_action_hints.extend(result.next_action_hints)

        content = self._compose_answer(request.content, citations=citations, evidence=evidence)
        if not citations and not evidence and scope.allow_model_only_fallback:
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

    def _resolve_workspace_and_agent_profile(
        self,
        request: TaskResolveRequest,
    ) -> tuple[str, AgentProfileResponse | None]:
        workspace_id = request.workspace_id or self._settings.default_workspace_id
        profile_id = request.agent_profile_id
        if profile_id is None and request.conversation_id:
            conversation = self._conversation_service.get_conversation(request.conversation_id)
            workspace_id = request.workspace_id or conversation.workspace_id
            profile_id = conversation.agent_profile_id
        if profile_id:
            return workspace_id, self._agent_profile_service.get_profile(profile_id)
        return workspace_id, self._agent_profile_service.get_default_profile(workspace_id)

    def _build_execution_scope(
        self,
        profile: AgentProfileResponse | None,
        *,
        workspace_id: str,
        request_document_ids: list[str],
    ) -> AgentExecutionScope:
        if profile is None:
            preset = get_capability_preset("internal_qa")
            derived_document_ids = tuple(request_document_ids)
            return AgentExecutionScope(
                allowed_tool_names=preset.default_tool_order,
                allowed_tool_families=preset.allowed_tool_families,
                knowledge_pack_ids=(),
                derived_document_ids=derived_document_ids,
                evidence_sources=("internal_chunk", "graph_node", "graph_edge"),
                allow_model_only_fallback=True,
                capability_preset=preset.preset,
                capability_configured=False,
            )

        preset = get_capability_preset(profile.capability_preset)
        capability_configured = has_explicit_capability_config(profile.policy_config)
        allowed_tools = list(preset.default_tool_order)
        if profile.tool_policy.allowed_tools:
            allowed_set = set(profile.tool_policy.allowed_tools)
            allowed_tools = [tool_name for tool_name in allowed_tools if tool_name in allowed_set]
        blocked = set(profile.tool_policy.blocked_tools)
        allowed_tools = [tool_name for tool_name in allowed_tools if tool_name not in blocked]

        pack_document_ids = self._knowledge_pack_service.resolve_document_scope(
            workspace_id,
            profile.knowledge_pack_ids,
        )
        if capability_configured:
            allowed_document_ids = set(pack_document_ids)
            if request_document_ids:
                allowed_document_ids &= set(request_document_ids)
            derived_document_ids = tuple(sorted(allowed_document_ids))
        else:
            if request_document_ids:
                derived_document_ids = tuple(sorted(set(request_document_ids)))
            else:
                derived_document_ids = tuple(sorted(set(pack_document_ids)))

        return AgentExecutionScope(
            allowed_tool_names=tuple(allowed_tools),
            allowed_tool_families=preset.allowed_tool_families,
            knowledge_pack_ids=tuple(profile.knowledge_pack_ids),
            derived_document_ids=derived_document_ids,
            evidence_sources=tuple(profile.evidence_policy.allowed_sources),
            allow_model_only_fallback=profile.evidence_policy.allow_model_only_fallback,
            capability_preset=preset.preset,
            capability_configured=capability_configured,
        )

    def _build_tool_plan(
        self,
        request: TaskResolveRequest,
        *,
        scope: AgentExecutionScope,
    ) -> list[ToolPlanStep]:
        preset = get_capability_preset(scope.capability_preset)
        plan: list[ToolPlanStep] = []
        retrieval_should_run = "retrieval.internal" in scope.allowed_tool_names and (
            bool(scope.derived_document_ids)
            or request.use_retrieval and not scope.capability_configured
        )
        if retrieval_should_run:
            plan.append(
                ToolPlanStep(
                    tool_name="retrieval.internal",
                    arguments={
                        "query": request.content,
                        "document_ids": list(scope.derived_document_ids),
                        "top_k": request.top_k,
                    },
                    reason="Ground answer in internal knowledge scope.",
                    required=False,
                    can_fallback=True,
                )
            )
        if preset.ontology_enabled and "ontology.lookup" in scope.allowed_tool_names and _should_use_ontology(request.content):
            plan.append(
                ToolPlanStep(
                    tool_name="ontology.lookup",
                    arguments={"mode": "entity_lookup", "query": request.content},
                    reason="Use ontology context for entity/type grounding.",
                )
            )
        if preset.graph_enabled and "graphiti.search" in scope.allowed_tool_names and _should_use_graph(request.content):
            plan.append(
                ToolPlanStep(
                    tool_name="graphiti.search",
                    arguments={"query": request.content, "max_results": request.top_k},
                    reason="Use graph context for relationship-oriented questions.",
                )
            )
        return plan

    def _invoke_step(
        self,
        step: ToolPlanStep,
        *,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        request: TaskResolveRequest,
    ):
        ontology_context = None
        if step.tool_name == "ontology.lookup":
            ontology_context = OntologyContextRef(domain="workspace_ontology")
        elif step.tool_name == "graphiti.search":
            ontology_context = OntologyContextRef(domain="workspace_runtime_graph")
        return self._tool_runtime.invoke(
            ToolEnvelope(
                call_id=uuid4(),
                tool_name=step.tool_name,
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                task_type="chat.answer",
                task_payload={"content": request.content, "reason": step.reason},
                arguments=step.arguments,
                ontology_context=ontology_context,
                constraints=ToolConstraints(max_results=request.top_k),
            )
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
            workspace_id=workspace_id,
            model_config_service=self._model_config_service,
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


def _should_use_ontology(prompt: str) -> bool:
    lowered = prompt.lower()
    keywords = ("ontology", "entity", "entities", "type", "taxonomy", "schema")
    return any(keyword in lowered for keyword in keywords)


def _should_use_graph(prompt: str) -> bool:
    lowered = prompt.lower()
    keywords = ("graph", "relationship", "related", "connected", "dependency", "depends on")
    return any(keyword in lowered for keyword in keywords)


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
