from __future__ import annotations

import asyncio
import concurrent.futures
import json
from dataclasses import dataclass, field
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.core.runtime_constants import (
    TOOL_GRAPHITI_SEARCH,
    TOOL_RETRIEVAL_INTERNAL,
)
from semantic_reasoning_agent.domain.builtin_agent_roles import BuiltinAgentRole, builtin_agent_profile_id
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolConstraints,
    ToolEnvelope,
    ToolResult,
)
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.schemas.agent_profiles import AgentProfileResponse
from semantic_reasoning_agent.schemas.llm_inference import (
    LlmInferenceOverrides,
    llm_inference_from_policy,
)
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest
from semantic_reasoning_agent.agents.builtin_context import BuiltinAgentContextService
from semantic_reasoning_agent.services.agent_profile_service import (
    AgentProfileNotFoundError,
    AgentProfileService,
)
from semantic_reasoning_agent.services.knowledge_pack_service import KnowledgePackService
from semantic_reasoning_agent.services.search_tool_service import SearchToolConfigService
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime

try:
    from llama_index.core.agent.workflow import FunctionAgent, ReActAgent
    from llama_index.core.tools import FunctionTool
    from llama_index.core.workflow import Context
    from llama_index.llms.openai import OpenAI as LlamaOpenAI
except Exception:  # pragma: no cover - optional dependency path
    FunctionAgent = None  # type: ignore[assignment]
    ReActAgent = None  # type: ignore[assignment]
    FunctionTool = None  # type: ignore[assignment]
    Context = None  # type: ignore[assignment]
    LlamaOpenAI = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ReActRunResult:
    content: str
    tool_results: list[ToolResult] = field(default_factory=list)
    next_action_hints: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, str | int | None]] = field(default_factory=list)


class LlamaReActOrchestratorService:
    """ReAct orchestrator delegating only to ``graph`` and ``docs`` builtins (LlamaIndex tools).

    Per-role LLMs and subgraph retrieval scope load from seeded built-in profiles for the workspace
    (``builtin_agent_role`` orchestrator/graph/docs): ``policy_config.llm_inference`` overrides and
    tool assignments/knowledge_pack_ids define graph vs vector backends.
    """

    def __init__(
        self,
        settings: Settings,
        tool_runtime: ToolRuntime,
        *,
        builtin_context: BuiltinAgentContextService,
        search_tool_service: SearchToolConfigService,
        graphiti_gateway: GraphitiGateway | None,
        agent_profile_service: AgentProfileService | None = None,
        knowledge_pack_service: KnowledgePackService | None = None,
    ) -> None:
        self._settings = settings
        self._tool_runtime = tool_runtime
        self._builtin_context = builtin_context
        self._search_tool_service = search_tool_service
        self._graphiti_gateway = graphiti_gateway
        self._profiles = agent_profile_service
        self._knowledge_pack_service = knowledge_pack_service

    def _builtin_profile(self, workspace_id: str, role: BuiltinAgentRole) -> AgentProfileResponse | None:
        if self._profiles is None:
            return None
        try:
            return self._profiles.get_profile(builtin_agent_profile_id(workspace_id, role))
        except AgentProfileNotFoundError:
            return None

    @staticmethod
    def _first_slot_assignment(
        profile: AgentProfileResponse | None,
        *,
        slot: str,
    ) -> object | None:
        if profile is None:
            return None
        for assignment in profile.tool_assignments:
            if assignment.enabled and assignment.slot == slot and assignment.config_id:
                return assignment
        return None

    def _system_prompt(self, workspace_id: str, role: BuiltinAgentRole, profile: AgentProfileResponse | None) -> str:
        addon = self._builtin_context.format_system_addendum(workspace_id, role)
        if profile and profile.system_prompt.strip():
            return f"{profile.system_prompt.strip()}\n\n{addon}"
        return addon

    def _resolve_docs_config_id(
        self,
        workspace_id: str,
        rag_binding_fallback,
        docs_profile: AgentProfileResponse | None,
    ) -> str:
        from_docs = self._first_slot_assignment(docs_profile, slot="rag")
        cand = getattr(from_docs, "config_id", None) if from_docs else None
        if cand:
            return str(cand)
        if rag_binding_fallback is not None and getattr(rag_binding_fallback, "config_id", None):
            return str(rag_binding_fallback.config_id)
        return self._search_tool_service.resolve_default_docs_config_id(workspace_id)

    def _merged_doc_ids(
        self,
        workspace_id: str,
        request: TaskResolveRequest,
        docs_profile: AgentProfileResponse | None,
    ) -> list[str]:
        base = list(request.document_ids or [])
        if docs_profile is None or self._knowledge_pack_service is None:
            return sorted(set(base))
        pack_ids = list(docs_profile.knowledge_pack_ids or [])
        if not pack_ids:
            return sorted(set(base))
        try:
            from_pack = self._knowledge_pack_service.resolve_document_scope(workspace_id, pack_ids)
        except Exception:
            from_pack = []
        return sorted(set(base) | set(from_pack))

    def run(
        self,
        *,
        request: TaskResolveRequest,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        provider: str | None,
        model: str | None,
        rag_binding,
        ontology_binding,
    ) -> ReActRunResult | None:
        if not self._settings.task_runtime_react_enabled:
            return None
        if (
            ReActAgent is None
            or FunctionAgent is None
            or FunctionTool is None
            or Context is None
            or LlamaOpenAI is None
        ):
            return None

        orch_prof = self._builtin_profile(workspace_id, "orchestrator")
        graph_prof = self._builtin_profile(workspace_id, "graph")
        docs_prof = self._builtin_profile(workspace_id, "docs")

        orch_llm_inf = llm_inference_from_policy(orch_prof.policy_config if orch_prof else None)
        graph_llm_inf = llm_inference_from_policy(graph_prof.policy_config if graph_prof else None)
        docs_llm_inf = llm_inference_from_policy(docs_prof.policy_config if docs_prof else None)

        orch_llm = self._build_llm(provider=provider, model=model, inference=orch_llm_inf)
        if orch_llm is None:
            return None
        graph_llm = self._build_llm(provider=provider, model=model, inference=graph_llm_inf) or orch_llm
        docs_llm = self._build_llm(provider=provider, model=model, inference=docs_llm_inf) or orch_llm

        merged_doc_ids = self._merged_doc_ids(workspace_id, request, docs_prof)

        tool_results: list[ToolResult] = []
        tool_calls: list[dict[str, str | int | None]] = []
        next_action_hints: list[str] = []

        graph_specialist = self._build_graph_specialist(
            request=request,
            workspace_id=workspace_id,
            task_id=task_id,
            workflow_id=workflow_id,
            llm=graph_llm,
            tool_results=tool_results,
            next_action_hints=next_action_hints,
            tool_calls=tool_calls,
            graph_profile=graph_prof,
            ontology_fallback_binding=ontology_binding,
        )
        docs_specialist = self._build_docs_specialist(
            request=request,
            workspace_id=workspace_id,
            task_id=task_id,
            workflow_id=workflow_id,
            llm=docs_llm,
            docs_config_id=docs_config_id,
            merged_document_ids=merged_doc_ids,
            tool_results=tool_results,
            next_action_hints=next_action_hints,
            tool_calls=tool_calls,
            docs_profile=docs_prof,
        )

        def delegate_to_graph_specialist(task: str, top_k: int = 8) -> str:
            return self._run_subagent(
                graph_specialist,
                task=task,
                top_k=top_k,
            )

        def delegate_to_docs_specialist(task: str, top_k: int = 8) -> str:
            return self._run_subagent(
                docs_specialist,
                task=task,
                top_k=top_k,
            )

        def record_episodic_note(target_role: str, note: str, mode: str = "append") -> str:
            return self._builtin_context.record_episodic_note(
                workspace_id=workspace_id,
                target_role=target_role,
                note=note,
                mode=mode,
            )

        orch_sys = self._system_prompt(workspace_id, "orchestrator", orch_prof)

        tools = [
            FunctionTool.from_defaults(
                fn=delegate_to_graph_specialist,
                name="delegate_to_graph_specialist",
                description=(
                    "Delegate a focused sub-question to the graph-database specialist "
                    "(Graphiti / ontology scope). Choose when structure, entities, or relations matter."
                ),
            ),
            FunctionTool.from_defaults(
                fn=delegate_to_docs_specialist,
                name="delegate_to_docs_specialist",
                description=(
                    "Delegate to the vector / document-grounding specialist "
                    "(chunk + supersearch.docs within this agent's knowledge scope)."
                ),
            ),
            FunctionTool.from_defaults(
                fn=record_episodic_note,
                name="record_episodic_note",
                description=(
                    "Rarely record a short episodic note for orchestrator, graph, or docs "
                    "builtin agent (target_role: orchestrator|graph|docs). "
                    "mode is 'append' (default) or 'replace'."
                ),
            ),
        ]

        agent = ReActAgent(tools=tools, llm=orch_llm, system_prompt=orch_sys)
        prompt = self._react_prompt(request.content)
        content = self._run_main_agent(agent, prompt)
        return ReActRunResult(
            content=content.strip(),
            tool_results=tool_results,
            next_action_hints=next_action_hints,
            tool_calls=tool_calls,
        )

    def _build_graph_specialist(
        self,
        *,
        request: TaskResolveRequest,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        llm,
        tool_results: list[ToolResult],
        next_action_hints: list[str],
        tool_calls: list[dict[str, str | int | None]],
        graph_profile: AgentProfileResponse | None,
        ontology_fallback_binding,
    ):
        gw = self._graphiti_gateway
        ontology_from_graph = self._first_slot_assignment(graph_profile, slot="ontology_search")

        def graphiti_search(query: str, max_results: int = 8) -> str:
            if gw is None or not gw.is_enabled():
                return json.dumps(
                    {
                        "status": "unavailable",
                        "message": "Graphiti is disabled or not configured for this deployment.",
                    }
                )
            result = self._tool_runtime.invoke(
                ToolEnvelope(
                    call_id=uuid4(),
                    tool_name=TOOL_GRAPHITI_SEARCH,
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    task_type="chat.answer",
                    task_payload={"content": request.content, "reason": "react.graph_subagent"},
                    arguments={
                        "query": query,
                        "max_results": int(max_results),
                        "search_type": "combined",
                    },
                    constraints=ToolConstraints(max_results=int(max_results)),
                )
            )
            tool_results.append(result)
            next_action_hints.extend(result.next_action_hints)
            tool_calls.append(self._trace_row(result))
            return self._tool_result_json(result)

        def supersearch_graph(query: str, top_k: int = 8) -> str:
            binding = ontology_from_graph or ontology_fallback_binding
            config_ref = str(getattr(binding, "config_id", "") or "")
            if not config_ref.strip():
                return json.dumps({"status": "unconfigured", "message": "No supersearch.graph preset on graph agent profile."})
            result = self._tool_runtime.invoke(
                ToolEnvelope(
                    call_id=uuid4(),
                    tool_name="supersearch.graph",
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    task_type="chat.answer",
                    task_payload={"content": request.content, "reason": "react.graph.supersearch"},
                    arguments={
                        "config_ref": config_ref.strip(),
                        "query": query,
                        "top_k": int(top_k),
                    },
                    constraints=ToolConstraints(max_results=int(top_k)),
                )
            )
            tool_results.append(result)
            next_action_hints.extend(result.next_action_hints)
            tool_calls.append(self._trace_row(result))
            return self._tool_result_json(result)

        graph_tools = [
            FunctionTool.from_defaults(
                fn=graphiti_search,
                name="graphiti_search",
                description="Low-level Graphiti graph search over the runtime Graph DB (indices + embeddings).",
            ),
            FunctionTool.from_defaults(
                fn=supersearch_graph,
                name="supersearch_graph",
                description=(
                    "Workspace-configured ontology/graph retrieval (supersearch.graph) when a graph "
                    "search preset is bound to this agent profile."
                ),
            ),
        ]
        system = self._system_prompt(workspace_id, "graph", graph_profile)
        return FunctionAgent(tools=graph_tools, llm=llm, system_prompt=system)

    def _build_docs_specialist(
        self,
        *,
        request: TaskResolveRequest,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        llm,
        docs_config_id: str,
        merged_document_ids: list[str],
        tool_results: list[ToolResult],
        next_action_hints: list[str],
        tool_calls: list[dict[str, str | int | None]],
        docs_profile: AgentProfileResponse | None,
    ):
        doc_ids = merged_document_ids

        def workspace_chunk_search(query: str, top_k: int = 8) -> str:
            result = self._tool_runtime.invoke(
                ToolEnvelope(
                    call_id=uuid4(),
                    tool_name=TOOL_RETRIEVAL_INTERNAL,
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    task_type="chat.answer",
                    task_payload={"content": request.content, "reason": "react.docs_subagent"},
                    arguments={
                        "query": query,
                        "top_k": int(top_k),
                        "mode": "chunks",
                        "document_ids": doc_ids,
                    },
                    constraints=ToolConstraints(max_results=int(top_k)),
                )
            )
            tool_results.append(result)
            next_action_hints.extend(result.next_action_hints)
            tool_calls.append(self._trace_row(result))
            return self._tool_result_json(result)

        def supersearch_docs(query: str, top_k: int = 8) -> str:
            result = self._tool_runtime.invoke(
                ToolEnvelope(
                    call_id=uuid4(),
                    tool_name="supersearch.docs",
                    workspace_id=workspace_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    task_type="chat.answer",
                    task_payload={"content": request.content, "reason": "react.docs_subagent.supersearch"},
                    arguments={
                        "config_ref": docs_config_id,
                        "query": query,
                        "document_ids": doc_ids,
                        "top_k": int(top_k),
                    },
                    constraints=ToolConstraints(max_results=int(top_k)),
                )
            )
            tool_results.append(result)
            next_action_hints.extend(result.next_action_hints)
            tool_calls.append(self._trace_row(result))
            return self._tool_result_json(result)

        doc_tools = [
            FunctionTool.from_defaults(
                fn=workspace_chunk_search,
                name="workspace_chunk_search",
                description=(
                    "Dense retrieval over indexed workspace chunks (vector store) constrained to "
                    "this docs agent document scope."
                ),
            ),
            FunctionTool.from_defaults(
                fn=supersearch_docs,
                name="supersearch_docs",
                description=(
                    "Semantic (+BM25) document search via supersearch.docs using this agent profile's "
                    "docs search preset."
                ),
            ),
        ]
        system = self._system_prompt(workspace_id, "docs", docs_profile)
        return FunctionAgent(tools=doc_tools, llm=llm, system_prompt=system)

    def _run_subagent(
        self,
        agent,
        *,
        task: str,
        top_k: int,
    ) -> str:
        prompt = f"Sub-task (top_k={top_k}):\n{task.strip()}"

        async def _runner() -> str:
            assert Context is not None
            ctx = Context(agent)
            handler = agent.run(prompt, ctx=ctx)
            response = await handler
            return str(response)

        return self._run_coro_compatible(_runner())

    def _run_main_agent(self, agent, prompt: str) -> str:
        async def _once() -> str:
            assert Context is not None
            ctx = Context(agent)
            handler = agent.run(prompt, ctx=ctx)
            response = await handler
            return str(response)

        return self._run_coro_compatible(_once())

    @staticmethod
    def _run_coro_compatible(coroutine) -> str:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        def _runner() -> str:
            return asyncio.run(coroutine)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_runner).result()

    def _build_llm(
        self,
        *,
        provider: str | None,
        model: str | None,
        inference: LlmInferenceOverrides | None,
    ):
        rp = inference.provider if inference and inference.provider else provider
        rm = inference.model if inference and inference.model else model
        if rp is None or rm is None:
            return None
        kwargs: dict = {}
        if inference is not None:
            if inference.temperature is not None:
                kwargs["temperature"] = inference.temperature
            if inference.max_tokens is not None:
                kwargs["max_tokens"] = inference.max_tokens

        if rp == "openai":
            if not self._settings.openai_api_key:
                return None
            return LlamaOpenAI(
                model=rm,
                api_key=self._settings.openai_api_key,
                api_base=self._settings.openai_base_url,
                **kwargs,
            )
        if rp == "openrouter":
            if not self._settings.openrouter_api_key:
                return None
            return LlamaOpenAI(
                model=rm,
                api_key=self._settings.openrouter_api_key,
                api_base=self._settings.openrouter_base_url,
                **kwargs,
            )
        return None

    @staticmethod
    def _react_prompt(user_prompt: str) -> str:
        return (
            "Answer using delegate tools when retrieval is needed; synthesize concise output.\n\n"
            f"User query: {user_prompt}"
        )

    def _trace_row(self, result: ToolResult) -> dict[str, str | int | None]:
        return {
            "stage": "tool_call",
            "tool_name": result.tool_name,
            "status": result.status,
            "latency_ms": result.latency_ms,
            "trace_id": result.meta.trace_id,
        }

    @staticmethod
    def _tool_result_json(result: ToolResult) -> str:
        payload = {
            "status": result.status,
            "error": result.error_message,
            "evidence_count": len(result.evidence),
            "top_evidence": [item.title for item in result.evidence[:3]],
        }
        return json.dumps(payload)
