from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import Evidence
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage, LLMToolCall
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    OntologyContextRef,
    ToolConstraints,
    ToolEnvelope,
)
from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.infrastructure.llm.anthropic_adapter import AnthropicAdapter
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.llm.openai_adapter import OpenAIAdapter
from semantic_reasoning_agent.schemas.chat import ChatReply, ConversationModelSelectionRequest
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tasks import (
    TaskResolutionRequest,
    TaskResolutionResponse,
    ToolCallSummary,
)
from semantic_reasoning_agent.schemas.tools import (
    CitationAnchorSchema,
    EvidenceSchema,
    ProvenanceSchema,
)
from semantic_reasoning_agent.services.conversation_service import ConversationService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_grounding_service import (
    OntologyGroundingService,
    TaskOntologyGrounding,
)
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.runtime_errors import ProviderNotReadyError
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime
from semantic_reasoning_agent.services.workflow_runtime import WorkflowRuntime


@dataclass(frozen=True)
class ResolvedRuntime:
    workspace_id: str
    provider: str
    model: str
    system_prompt: str | None


class TaskRuntime:
    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        model_config_service: ModelConfigService,
        adapter_registry: AdapterRegistry,
        ontology_grounding_service: OntologyGroundingService,
        tool_registry: ToolRegistry,
        tool_runtime: ToolRuntime,
        workflow_runtime: WorkflowRuntime,
        audit_service: RuntimeAuditService,
    ) -> None:
        self._conversation_service = conversation_service
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry
        self._ontology_grounding_service = ontology_grounding_service
        self._tool_registry = tool_registry
        self._tool_runtime = tool_runtime
        self._workflow_runtime = workflow_runtime
        self._audit_service = audit_service

    def resolve(self, payload: TaskResolutionRequest) -> TaskResolutionResponse:
        runtime = self._resolve_runtime(payload)
        grounding = self._ontology_grounding_service.ground_workspace(runtime.workspace_id)
        task_id = self._audit_service.create_task_run(
            workspace_id=runtime.workspace_id,
            entrypoint=payload.entrypoint,
            task_type=payload.task_type,
            requested_output=payload.requested_output,
            conversation_id=payload.conversation_id,
            provider=runtime.provider,
            model=runtime.model,
            input_payload={
                **payload.model_dump(mode="json"),
                "ontology_grounding": self._grounding_payload(grounding),
            },
        )
        workflow_id = self._select_workflow(payload, runtime, grounding)
        workflow_run_id, workflow_spec = self._workflow_runtime.start_run(
            task_id=task_id,
            workflow_id=workflow_id,
            input_payload={
                **payload.model_dump(mode="json"),
                "ontology_grounding": self._grounding_payload(grounding),
            },
        )
        try:
            if payload.conversation_id:
                self._conversation_service.append_message(
                    conversation_id=payload.conversation_id,
                    role="user",
                    content=payload.content,
                )
            response = self._execute_answer_workflow(
                task_id=task_id,
                workflow_run_id=workflow_run_id,
                workflow_id=workflow_spec.workflow_id,
                payload=payload,
                runtime=runtime,
                workflow_mode=workflow_spec.mode,
                grounding=grounding,
            )
            output_payload = response.model_dump(mode="json")
            self._workflow_runtime.complete_run(
                workflow_run_id,
                status="completed",
                output_payload=output_payload,
            )
            self._audit_service.complete_task_run(
                task_id,
                status="completed",
                output_payload=output_payload,
                provider=runtime.provider,
                model=runtime.model,
            )
            return response
        except Exception as exc:
            self._workflow_runtime.complete_run(
                workflow_run_id,
                status="failed",
                output_payload={},
                error_message=str(exc),
            )
            self._audit_service.complete_task_run(
                task_id,
                status="failed",
                output_payload={},
                provider=runtime.provider,
                model=runtime.model,
                error_message=str(exc),
            )
            raise

    def resolve_chat_message(self, payload) -> ChatReply:  # noqa: ANN001
        response = self.resolve(
            TaskResolutionRequest(
                conversation_id=payload.conversation_id,
                entrypoint="chat",
                content=payload.content,
                workspace_id=payload.workspace_id,
                task_type="chat",
                requested_output="answer",
                provider=payload.provider,
                model=payload.model,
                use_retrieval=payload.use_retrieval,
                document_ids=list(payload.document_ids),
                top_k=payload.top_k,
            )
        )
        if payload.conversation_id:
            updated = self._conversation_service.append_message(
                conversation_id=payload.conversation_id,
                role="assistant",
                content=response.reply or "",
            )
        else:
            updated = None
        if updated is None:
            raise ValueError("Chat message resolution requires a conversation_id.")
        return ChatReply(
            conversation=updated,
            reply=updated.messages[-1],
            citations=response.citations,
        )

    def _resolve_runtime(self, payload: TaskResolutionRequest) -> ResolvedRuntime:
        if payload.conversation_id:
            conversation = self._conversation_service.get_conversation(payload.conversation_id)
            runtime_provider = conversation.provider
            runtime_model = conversation.model
            workspace_id = payload.workspace_id or conversation.workspace_id
            if payload.provider and payload.model:
                if conversation.provider != payload.provider or conversation.model != payload.model:
                    updated = self._conversation_service.update_runtime_selection(
                        payload.conversation_id,
                        ConversationModelSelectionRequest(
                            provider=payload.provider,
                            model=payload.model,
                            workspace_id=workspace_id,
                        ),
                    )
                    runtime_provider = updated.provider
                    runtime_model = updated.model
                else:
                    runtime_provider = payload.provider
                    runtime_model = payload.model
            system_prompt = self._conversation_service.get_system_prompt(payload.conversation_id)
        else:
            workspace_id = payload.workspace_id or get_settings().default_workspace_id
            runtime_provider, runtime_model = self._model_config_service.resolve_runtime_model(
                "chat",
                workspace_id,
            )
            if payload.provider and payload.model:
                runtime_provider, runtime_model = payload.provider, payload.model
            system_prompt = None
        if not self._model_config_service.is_ready(runtime_provider, runtime_model, workspace_id):
            raise ProviderNotReadyError(
                f"Provider '{runtime_provider}' with model '{runtime_model}' is not ready yet."
            )
        return ResolvedRuntime(
            workspace_id=workspace_id,
            provider=runtime_provider,
            model=runtime_model,
            system_prompt=system_prompt,
        )

    @staticmethod
    def _select_workflow(
        payload: TaskResolutionRequest,
        runtime: ResolvedRuntime,
        grounding: TaskOntologyGrounding,
    ) -> str:
        if payload.requested_output != "answer":
            return "review_publish"
        if payload.task_type in {"ontology", "ontology_build"} or payload.requested_output == "ontology_candidates":
            return "ontology_build"
        if "ontology_build" in grounding.architecture.workflow_hints and "ontology" in payload.content.lower():
            return "ontology_build"
        if runtime.provider == "echo" and payload.use_retrieval:
            return "answer_resolution"
        return "answer_resolution"

    def _execute_answer_workflow(
        self,
        *,
        task_id: str,
        workflow_run_id: str,
        workflow_id: str,
        payload: TaskResolutionRequest,
        runtime: ResolvedRuntime,
        workflow_mode: str,
        grounding: TaskOntologyGrounding,
    ) -> TaskResolutionResponse:
        if payload.requested_output != "answer":
            return TaskResolutionResponse(
                task_id=task_id,
                workflow_run_id=workflow_run_id,
                workflow_id=workflow_id,
                workflow_mode=workflow_mode,
                status="completed",
                output_type=payload.requested_output,
                reply=None,
                citations=[],
                evidence=[],
                tool_calls=[],
                trace_id=None,
                provider=runtime.provider,
                model=runtime.model,
            )
        adapter = self._build_runtime_adapter(runtime)
        assert adapter is not None
        ontology_context = grounding.as_context_ref()
        tools = self._select_tools(payload, grounding)
        messages = [LLMMessage(role="user", content=payload.content)]
        tool_summaries: list[ToolCallSummary] = []
        collected_evidence: list[Evidence] = []
        trace_id: str | None = None

        for _ in range(4):
            llm_response = adapter.run(
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else "none",
                system=self._tool_system_prompt(payload, runtime.system_prompt),
                model=runtime.model,
            )
            if llm_response.tool_calls:
                tool_results = []
                for tool_call in llm_response.tool_calls:
                    result = self._invoke_llm_tool_call(
                        task_id=task_id,
                        workflow_run_id=workflow_run_id,
                        workflow_id=workflow_id,
                        runtime=runtime,
                        payload=payload,
                        ontology_context=ontology_context,
                        tool_call=tool_call,
                    )
                    collected_evidence.extend(result.evidence)
                    if trace_id is None:
                        trace_id = result.meta.trace_id
                    tool_summaries.append(
                        ToolCallSummary(
                            tool_name=result.tool_name,
                            status=result.status,
                            trace_id=result.meta.trace_id,
                            latency_ms=result.latency_ms,
                            next_action_hints=list(result.next_action_hints),
                        )
                    )
                    tool_results.append((tool_call, result))
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=llm_response.content,
                        tool_calls=tuple(llm_response.tool_calls),
                    )
                )
                messages.extend(
                    LLMMessage(
                        role="tool",
                        tool_call_id=tool_call.call_id,
                        content=self._tool_result_json(result),
                    )
                    for tool_call, result in tool_results
                )
                continue

            reply = llm_response.content or None
            break
        else:
            reply = None

        citations = [self._evidence_to_citation(item) for item in collected_evidence if item.source_type == "internal_chunk"]
        citations = [item for item in citations if item is not None]
        if payload.use_retrieval and not citations:
            fallback = self._invoke_fallback_retrieval(
                task_id=task_id,
                workflow_run_id=workflow_run_id,
                workflow_id=workflow_id,
                runtime=runtime,
                payload=payload,
                ontology_context=ontology_context,
            )
            if fallback is not None:
                tool_summaries.append(
                    ToolCallSummary(
                        tool_name=fallback.tool_name,
                        status=fallback.status,
                        trace_id=fallback.meta.trace_id,
                        latency_ms=fallback.latency_ms,
                        next_action_hints=list(fallback.next_action_hints),
                    )
                )
                collected_evidence.extend(fallback.evidence)
                if trace_id is None:
                    trace_id = fallback.meta.trace_id
                citations = [
                    self._evidence_to_citation(item)
                    for item in collected_evidence
                    if item.source_type == "internal_chunk"
                ]
                citations = [item for item in citations if item is not None]

        if payload.use_retrieval:
            reply = self._compose_grounded_reply(payload.content, citations)
        elif not reply:
            reply = "No answer was produced for this task."

        return TaskResolutionResponse(
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            workflow_id=workflow_id,
            workflow_mode=workflow_mode,
            status="completed",
            output_type=payload.requested_output,
            reply=reply,
            citations=citations,
            evidence=[self._evidence_to_schema(item) for item in collected_evidence],
            tool_calls=tool_summaries,
            trace_id=trace_id,
            provider=runtime.provider,
            model=runtime.model,
        )

    def _invoke_llm_tool_call(
        self,
        *,
        task_id: str,
        workflow_run_id: str,
        workflow_id: str,
        runtime: ResolvedRuntime,
        payload: TaskResolutionRequest,
        ontology_context: OntologyContextRef,
        tool_call: LLMToolCall,
    ):
        envelope = ToolEnvelope(
            call_id=uuid4(),
            tool_name=tool_call.tool_name,
            workspace_id=runtime.workspace_id,
            task_id=task_id,
            workflow_id=workflow_id,
            task_type=payload.task_type,
            task_payload={
                "entrypoint": payload.entrypoint,
                "conversation_id": payload.conversation_id,
                "llm_tool_call_id": tool_call.call_id,
            },
            ontology_context=ontology_context,
            arguments=dict(tool_call.arguments),
            constraints=ToolConstraints(
                web_enabled=payload.web_enabled,
                freshness_required=payload.freshness_required,
                max_results=payload.top_k,
                timeout_ms=15000,
            ),
        )
        return self._tool_runtime.invoke(
            envelope,
            task_id=task_id,
            workflow_run_id=workflow_run_id,
        )

    def _invoke_fallback_retrieval(
        self,
        *,
        task_id: str,
        workflow_run_id: str,
        workflow_id: str,
        runtime: ResolvedRuntime,
        payload: TaskResolutionRequest,
        ontology_context: OntologyContextRef,
    ):
        if self._tool_registry.spec("retrieval.internal") is None:
            return None
        envelope = ToolEnvelope(
            call_id=uuid4(),
            tool_name="retrieval.internal",
            workspace_id=runtime.workspace_id,
            task_id=task_id,
            workflow_id=workflow_id,
            task_type=payload.task_type,
            task_payload={"entrypoint": payload.entrypoint, "conversation_id": payload.conversation_id},
            ontology_context=ontology_context,
            arguments={
                "query": payload.content,
                "document_ids": list(payload.document_ids),
                "top_k": payload.top_k,
            },
            constraints=ToolConstraints(
                web_enabled=payload.web_enabled,
                freshness_required=payload.freshness_required,
                max_results=payload.top_k,
                timeout_ms=15000,
            ),
        )
        return self._tool_runtime.invoke(
            envelope,
            task_id=task_id,
            workflow_run_id=workflow_run_id,
        )

    def _select_tools(self, payload: TaskResolutionRequest, grounding: TaskOntologyGrounding):
        max_risk = "low"
        specs = self._tool_registry.list(max_risk=max_risk)
        if not payload.use_retrieval:
            specs = [spec for spec in specs if spec.tool_family == "ontology"]
        preferred = grounding.architecture.tool_affinity_hints
        if not preferred:
            return specs
        priority = {name: index for index, name in enumerate(preferred)}
        return sorted(
            specs,
            key=lambda spec: (priority.get(spec.tool_name, 999), spec.tool_name),
        )

    def _build_runtime_adapter(self, runtime: ResolvedRuntime):
        if runtime.provider == "anthropic":
            config = self._model_config_service.get_provider_runtime_config(
                "anthropic",
                runtime.workspace_id,
            )
            api_key = config.get("api_key")
            if not api_key:
                raise ProviderNotReadyError("Anthropic API key is not configured.")
            return AnthropicAdapter(api_key=api_key, base_url=config.get("base_url"))
        if runtime.provider == "openai":
            config = self._model_config_service.get_provider_runtime_config(
                "openai",
                runtime.workspace_id,
            )
            api_key = config.get("api_key")
            if not api_key:
                raise ProviderNotReadyError("OpenAI API key is not configured.")
            return OpenAIAdapter(api_key=api_key)
        adapter = self._adapter_registry.get(runtime.provider)
        if adapter is None:
            raise ProviderNotReadyError(f"No adapter is registered for provider '{runtime.provider}'.")
        return adapter

    @staticmethod
    def _tool_system_prompt(payload: TaskResolutionRequest, base_system_prompt: str | None) -> str:
        instructions = (
            "You are operating in a tool-first runtime. Use available tools when they improve grounding, "
            "especially for workspace evidence and ontology context. Prefer internal retrieval first. "
            "If you already have enough evidence, answer directly and keep citations implicit in the tool trace."
        )
        if payload.use_retrieval:
            instructions += " Retrieval is enabled for this task."
        if base_system_prompt:
            return f"{base_system_prompt}\n\n{instructions}"
        return instructions

    @staticmethod
    def _grounding_payload(grounding: TaskOntologyGrounding) -> dict[str, Any]:
        draft = grounding.architecture.draft
        return {
            "domain": grounding.architecture.domain or grounding.published_domain,
            "entity_hints": list(dict.fromkeys(grounding.architecture.entity_hints + grounding.published_entity_hints)),
            "relation_hints": list(dict.fromkeys(grounding.architecture.relation_hints + grounding.published_relation_hints)),
            "workflow_hints": list(grounding.architecture.workflow_hints),
            "tool_affinity_hints": list(grounding.architecture.tool_affinity_hints),
            "draft_id": None if draft is None else draft.draft_id,
        }

    @staticmethod
    def _tool_result_json(result) -> str:  # noqa: ANN001
        return json.dumps(
            {
                "tool_name": result.tool_name,
                "status": result.status,
                "error_code": result.error_code,
                "error_message": result.error_message,
                "next_action_hints": list(result.next_action_hints),
                "artifacts": [dict(item) for item in result.artifacts],
                "evidence": [
                    {
                        "title": evidence.title,
                        "content": evidence.content,
                        "source_type": evidence.source_type,
                        "citation_anchor": {
                            "anchor_type": evidence.citation_anchor.anchor_type,
                            "label": evidence.citation_anchor.label,
                            "locator": evidence.citation_anchor.locator,
                        },
                    }
                    for evidence in result.evidence
                ],
            }
        )

    @staticmethod
    def _compose_grounded_reply(prompt: str, citations: list[Citation]) -> str:
        if not citations:
            return "No indexed document context matched that question."
        lines = [f"Question: {prompt}", "Relevant context:"]
        for citation in citations:
            lines.append(
                f"- {citation.document_title} ({citation.location_label}): {citation.excerpt}"
            )
        return "\n".join(lines)

    @staticmethod
    def _evidence_to_citation(evidence: Evidence) -> Citation | None:
        if evidence.source_type != "internal_chunk" or not evidence.document_id or not evidence.chunk_id:
            return None
        document_type = "pdf" if evidence.page is not None else "xlsx" if evidence.sheet_name else "docx"
        row_start = None
        row_end = None
        if evidence.row_range and "-" in evidence.row_range:
            raw_start, raw_end = evidence.row_range.split("-", 1)
            if raw_start.isdigit():
                row_start = int(raw_start)
            if raw_end.isdigit():
                row_end = int(raw_end)
        return Citation(
            chunk_id=evidence.chunk_id,
            document_id=evidence.document_id,
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

    @staticmethod
    def _evidence_to_schema(evidence: Evidence) -> EvidenceSchema:
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
