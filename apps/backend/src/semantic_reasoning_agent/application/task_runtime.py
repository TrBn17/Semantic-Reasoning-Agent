from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.core.runtime_constants import (
    GRAPH_KEYWORDS,
    NO_CONTEXT_MESSAGE,
    ONTOLOGY_DOMAIN_WORKSPACE,
    ONTOLOGY_KEYWORDS,
    WORKFLOW_TASK_RESOLVE_CHAT,
)
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_envelope import OntologyContextRef, ToolConstraints, ToolEnvelope
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.schemas.agent_profiles import AgentProfileResponse
from semantic_reasoning_agent.schemas.chat import SendMessageRequest
from semantic_reasoning_agent.schemas.orchestration import (
    OrchestrationMode,
    OrchestrationConfigSchema,
)
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.schemas.tools import EvidenceSchema
from semantic_reasoning_agent.agents.builtin_context import BuiltinAgentContextService
from semantic_reasoning_agent.application.agentic_loop_service import AgenticLoopService
from semantic_reasoning_agent.application.llama_react_orchestrator_service import (
    LlamaReActOrchestratorService,
)
from semantic_reasoning_agent.application.workflow_selector import WorkflowSelector
from semantic_reasoning_agent.services.agent_capability_service import (
    get_capability_preset,
    has_explicit_capability_config,
)
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileService
from semantic_reasoning_agent.services.conflict_engine import ConflictEngine
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.context_assembler_service import ContextAssemblerService
from semantic_reasoning_agent.services.evidence_judge import EvidenceJudge
from semantic_reasoning_agent.services.evidence_normalization import citation_from_evidence, evidence_to_schema
from semantic_reasoning_agent.services.knowledge_pack_service import KnowledgePackService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_grounding_service import OntologyGroundingService
from semantic_reasoning_agent.services.output_router import OutputRouter
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.search_tool_service import SearchToolConfigService
from semantic_reasoning_agent.services.task_interpreter import TaskInterpreter
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime


@dataclass(frozen=True)
class TaskRuntimeResult:
    orchestration_mode: OrchestrationMode
    workflow_id: str
    content: str
    citations: list[Citation]
    evidence: list[EvidenceSchema]
    next_action_hints: list[str]
    tool_calls: list[dict[str, str | int | None]] = field(default_factory=list)


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
    knowledge_pack_ids: tuple[str, ...]
    derived_document_ids: tuple[str, ...]
    evidence_sources: tuple[str, ...]
    allow_model_only_fallback: bool
    capability_preset: str
    capability_configured: bool
    slot_bindings: tuple["SlotToolBinding", ...]


@dataclass(frozen=True)
class SlotToolBinding:
    slot: str
    tool_name: str
    config_id: str
    label: str
    position: int


class TaskRuntimeService:
    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        tool_runtime: ToolRuntime,
        conversation_service: ConversationService | None = None,
        agent_profile_service: AgentProfileService | None = None,
        knowledge_pack_service: KnowledgePackService | None = None,
        runtime_audit_service: RuntimeAuditService | None = None,
        search_tool_service: SearchToolConfigService | None = None,
        builtin_agent_context_service: BuiltinAgentContextService | None = None,
        graphiti_gateway: GraphitiGateway | None = None,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._tool_runtime = tool_runtime
        self._conversation_service = conversation_service
        self._agent_profile_service = agent_profile_service
        self._knowledge_pack_service = knowledge_pack_service
        self._runtime_audit_service = runtime_audit_service
        self._task_interpreter = TaskInterpreter()
        self._grounding_service = OntologyGroundingService()
        self._context_assembler = ContextAssemblerService()
        self._evidence_judge = EvidenceJudge()
        self._conflict_engine = ConflictEngine()
        self._output_router = OutputRouter()
        self._workflow_selector = WorkflowSelector()
        self._agentic_loop = AgenticLoopService()
        if (
            builtin_agent_context_service is not None
            and search_tool_service is not None
            and graphiti_gateway is not None
        ):
            self._react_orchestrator = LlamaReActOrchestratorService(
                settings,
                tool_runtime,
                builtin_context=builtin_agent_context_service,
                search_tool_service=search_tool_service,
                graphiti_gateway=graphiti_gateway,
                agent_profile_service=agent_profile_service,
                knowledge_pack_service=knowledge_pack_service,
            )
        else:
            self._react_orchestrator = None

    def resolve_request(
        self,
        request: TaskResolveRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> TaskRuntimeResult:
        workspace_id, profile = self._resolve_workspace_and_agent_profile(request)
        orchestration_mode = self._resolve_orchestration_mode(request, profile)
        scope = self._build_execution_scope(
            profile,
            workspace_id=workspace_id,
            request_document_ids=request.document_ids,
        )
        task_id = str(uuid4())
        workflow_id = WORKFLOW_TASK_RESOLVE_CHAT
        evidence: list[EvidenceSchema] = []
        citations: list[Citation] = []
        next_action_hints: list[str] = []
        plan = self._build_tool_plan(request, scope=scope)
        interpretation = self._task_interpreter.interpret(request)
        grounding = self._grounding_service.ground(request.content, interpretation)
        selection = self._workflow_selector.select(interpretation=interpretation, grounding=grounding)
        workflow_id = selection.workflow_id
        trace: list[dict[str, str | int | None]] = [
            {"stage": "orchestration", "mode": orchestration_mode},
            {"stage": "interpret", "intent": interpretation.intent},
            {"stage": "grounding", "status": grounding.grounding_status},
            {"stage": "workflow", "workflow_id": workflow_id, "reason": selection.reason},
        ]
        rag_binding = next((item for item in scope.slot_bindings if item.slot == "rag"), None)
        ontology_binding = next(
            (item for item in scope.slot_bindings if item.slot == "ontology_search"),
            None,
        )

        react_content: str | None = None
        used_react = False
        if orchestration_mode == "react_two_agent":
            orch = self._react_orchestrator
            if orch is not None:
                react_result = orch.run(
                    request=request,
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    provider=provider,
                    model=model,
                    rag_binding=rag_binding,
                    ontology_binding=ontology_binding,
                )
                if react_result is not None:
                    used_react = True
                    react_content = react_result.content
                    next_action_hints.extend(react_result.next_action_hints)
                    for result in react_result.tool_results:
                        self._collect_tool_result(
                            result,
                            scope=scope,
                            evidence=evidence,
                            citations=citations,
                            next_action_hints=next_action_hints,
                        )
                    trace.extend(
                        {
                            "stage": "tool_call",
                            "tool_name": str(item.get("tool_name", "")),
                            "status": str(item.get("status", "")),
                            "latency_ms": str(item.get("latency_ms", "")),
                        }
                        for item in react_result.tool_calls
                    )
                else:
                    trace.append(
                        {
                            "stage": "orchestration_fallback",
                            "reason": "react_unavailable",
                        }
                    )
            else:
                trace.append(
                    {
                        "stage": "orchestration_fallback",
                        "reason": "react_orchestrator_unwired",
                    }
                )

        if not used_react:
            validated_plan = self._agentic_loop.validate_plan(plan, scope)
            for step in validated_plan[: self._agentic_loop.max_steps_for(request)]:
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
                trace.append(
                    {
                        "stage": "tool_call",
                        "tool_name": step.tool_name,
                        "status": result.status,
                        "latency_ms": str(result.latency_ms),
                    }
                )
                self._collect_tool_result(
                    result,
                    scope=scope,
                    evidence=evidence,
                    citations=citations,
                    next_action_hints=next_action_hints,
                )

        bundle = self._context_assembler.assemble(citations=citations, evidence=evidence)
        sufficiency = self._evidence_judge.evaluate(bundle)
        conflict_report = self._conflict_engine.analyze(bundle)
        route = self._output_router.route(sufficiency, conflict_report)
        trace.append({"stage": "route", "output_type": route.output_type, "reason": route.reason})

        content = self._compose_answer(
            request.content,
            citations=list(bundle.citations),
            evidence=list(bundle.evidence),
        )
        if react_content:
            content = react_content
        if (
            route.output_type == "fallback_answer"
            and scope.allow_model_only_fallback
            and not react_content
        ):
            content = self._fallback_answer(
                prompt=request.content,
                workspace_id=workspace_id,
                provider=provider,
                model=model,
                system_prompt=system_prompt,
            )
        elif route.output_type == "needs_review":
            content = "Conflicting evidence detected. Review is required before final answer."

        if self._runtime_audit_service is not None:
            self._runtime_audit_service.record_task_run(
                task_id=task_id,
                workspace_id=workspace_id,
                workflow_id=workflow_id,
                output_type=route.output_type,
                stop_reason=route.reason,
                grounded=route.grounded,
                content=content,
                trace=trace,
                tool_calls=[item for item in trace if item.get("stage") == "tool_call"],
                conflict_details=[
                    {"conflict_type": item.conflict_type, "severity": item.severity, "detail": item.detail}
                    for item in conflict_report.conflicts
                ],
            )

        return TaskRuntimeResult(
            orchestration_mode=orchestration_mode,
            workflow_id=workflow_id,
            content=content,
            citations=list(bundle.citations),
            evidence=list(bundle.evidence),
            next_action_hints=sorted(set(next_action_hints + list(bundle.trace_notes))),
            tool_calls=[
                {
                    "step": item.get("stage"),
                    "tool_name": item.get("tool_name"),
                    "status": item.get("status"),
                    "latency_ms": item.get("latency_ms"),
                }
                for item in trace
                if item.get("stage") == "tool_call"
            ],
        )

    def resolve_api_request(self, request: TaskResolveRequest) -> TaskResolveResponse:
        result = self.resolve_request(
            request,
            provider=request.provider,
            model=request.model,
        )
        return TaskResolveResponse(
            task_id=str(uuid4()),
            output_type="answer",
            workflow_id=result.workflow_id,
            orchestration_mode=result.orchestration_mode,
            stop_reason="completed",
            grounded=bool(result.citations or result.evidence),
            content=result.content,
            citations=result.citations,
            evidence=[item.model_dump(mode="json") for item in result.evidence],
            next_action_hints=result.next_action_hints,
            trace=result.tool_calls,
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
                orchestration_mode=payload.orchestration_mode,
            ),
            provider=provider,
            model=model,
            system_prompt=system_prompt,
        )

    def _resolve_orchestration_mode(
        self,
        request: TaskResolveRequest,
        profile: AgentProfileResponse | None,
    ) -> OrchestrationMode:
        if request.orchestration_mode is not None:
            return request.orchestration_mode

        if profile is not None:
            try:
                config = OrchestrationConfigSchema.model_validate(profile.orchestration_config)
            except Exception:  # noqa: BLE001 - keep runtime resilient
                config = OrchestrationConfigSchema()
            if config.orchestrator.enabled:
                return config.mode

        if self._settings.task_runtime_orchestration_mode == "react_two_agent":
            return "react_two_agent"
        return "legacy_static_plan"

    @staticmethod
    def _collect_tool_result(
        result,
        *,
        scope: AgentExecutionScope,
        evidence: list[EvidenceSchema],
        citations: list[Citation],
        next_action_hints: list[str],
    ) -> None:
        for item in result.evidence:
            if item.source_type not in scope.evidence_sources:
                continue
            evidence.append(evidence_to_schema(item))
            if item.source_type == "internal_chunk":
                citations.append(citation_from_evidence(item))
        next_action_hints.extend(result.next_action_hints)

    def _resolve_workspace_and_agent_profile(
        self,
        request: TaskResolveRequest,
    ) -> tuple[str, AgentProfileResponse | None]:
        workspace_id = request.workspace_id or self._settings.default_workspace_id
        profile_id = request.agent_profile_id
        if profile_id is None and request.conversation_id and self._conversation_service is not None:
            conversation = self._conversation_service.get_conversation(request.conversation_id)
            workspace_id = request.workspace_id or conversation.workspace_id
            profile_id = conversation.agent_profile_id
        if profile_id and self._agent_profile_service is not None:
            return workspace_id, self._agent_profile_service.get_profile(profile_id)
        if self._agent_profile_service is None:
            return workspace_id, None
        return workspace_id, self._agent_profile_service.get_default_profile(workspace_id)

    def _build_execution_scope(
        self,
        profile: AgentProfileResponse | None,
        *,
        workspace_id: str,
        request_document_ids: list[str],
    ) -> AgentExecutionScope:
        if profile is None:
            return AgentExecutionScope(
                allowed_tool_names=(),
                knowledge_pack_ids=(),
                derived_document_ids=tuple(request_document_ids),
                evidence_sources=("internal_chunk", "graph_node", "graph_edge"),
                allow_model_only_fallback=True,
                capability_preset="internal_qa",
                capability_configured=False,
                slot_bindings=(),
            )

        preset = get_capability_preset(profile.capability_preset)
        capability_configured = has_explicit_capability_config(profile.policy_config)
        blocked = set(profile.tool_policy.blocked_tools)
        allow_mode = profile.tool_policy.mode == "allowlist"
        allow_set = set(profile.tool_policy.allowed_tools)
        slot_bindings: list[SlotToolBinding] = []
        for index, assignment in enumerate(profile.tool_assignments):
            if not assignment.enabled or not assignment.config_id:
                continue
            if assignment.tool_name in blocked:
                continue
            if allow_mode and allow_set and assignment.tool_name not in allow_set:
                continue
            if assignment.slot not in {"rag", "ontology_search"}:
                continue
            slot_bindings.append(
                SlotToolBinding(
                    slot=assignment.slot,
                    tool_name=assignment.tool_name,
                    config_id=assignment.config_id,
                    label=assignment.tool_name,
                    position=assignment.position if assignment.position is not None else index,
                )
            )

        pack_document_ids = self._knowledge_pack_service.resolve_document_scope(
            workspace_id,
            profile.knowledge_pack_ids,
        ) if self._knowledge_pack_service is not None else []
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
            allowed_tool_names=tuple(binding.tool_name for binding in slot_bindings),
            knowledge_pack_ids=tuple(profile.knowledge_pack_ids),
            derived_document_ids=derived_document_ids,
            evidence_sources=tuple(profile.evidence_policy.allowed_sources),
            allow_model_only_fallback=profile.evidence_policy.allow_model_only_fallback,
            capability_preset=preset.preset,
            capability_configured=capability_configured,
            slot_bindings=tuple(sorted(slot_bindings, key=lambda item: item.position)),
        )

    def _build_tool_plan(
        self,
        request: TaskResolveRequest,
        *,
        scope: AgentExecutionScope,
    ) -> list[ToolPlanStep]:
        plan: list[ToolPlanStep] = []
        enabled_tool_names = set(request.enabled_tool_names or [])
        rag_binding = next((item for item in scope.slot_bindings if item.slot == "rag"), None)
        ontology_binding = next(
            (item for item in scope.slot_bindings if item.slot == "ontology_search"),
            None,
        )

        retrieval_should_run = (
            rag_binding is not None
            and rag_binding.tool_name == "supersearch.docs"
            and (not enabled_tool_names or rag_binding.tool_name in enabled_tool_names)
            and (
                request.use_retrieval
                or bool(scope.derived_document_ids)
                or not scope.capability_configured
            )
        )
        if retrieval_should_run and rag_binding is not None:
            plan.append(
                ToolPlanStep(
                    tool_name=rag_binding.tool_name,
                    arguments={
                        "config_ref": rag_binding.config_id,
                        "query": request.content,
                        "document_ids": list(scope.derived_document_ids),
                        "top_k": request.top_k,
                    },
                    reason="Ground answer in internal knowledge scope.",
                    required=False,
                    can_fallback=True,
                )
            )
        if (
            ontology_binding is not None
            and ontology_binding.tool_name == "supersearch.graph"
            and (not enabled_tool_names or ontology_binding.tool_name in enabled_tool_names)
            and (_should_use_ontology(request.content) or _should_use_graph(request.content))
        ):
            plan.append(
                ToolPlanStep(
                    tool_name=ontology_binding.tool_name,
                    arguments={
                        "config_ref": ontology_binding.config_id,
                        "query": request.content,
                        "top_k": request.top_k,
                    },
                    reason="Use ontology search for entity and relationship grounding.",
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
                ontology_context=OntologyContextRef(domain=ONTOLOGY_DOMAIN_WORKSPACE)
                if step.tool_name == "supersearch.graph"
                else None,
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
            return NO_CONTEXT_MESSAGE
        if not self._model_config_service.is_ready(provider, model, workspace_id):
            return NO_CONTEXT_MESSAGE
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return NO_CONTEXT_MESSAGE
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
        return NO_CONTEXT_MESSAGE


def _should_use_ontology(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in ONTOLOGY_KEYWORDS)


def _should_use_graph(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in GRAPH_KEYWORDS)
