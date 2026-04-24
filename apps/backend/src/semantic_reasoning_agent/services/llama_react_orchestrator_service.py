from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from uuid import uuid4

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.core.runtime_constants import ONTOLOGY_DOMAIN_WORKSPACE
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    OntologyContextRef,
    ToolConstraints,
    ToolEnvelope,
    ToolResult,
)
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime

try:
    from llama_index.core.agent.workflow import ReActAgent
    from llama_index.core.tools import FunctionTool
    from llama_index.core.workflow import Context
    from llama_index.llms.openai import OpenAI as LlamaOpenAI
except Exception:  # pragma: no cover - optional dependency path
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
    """Thin ReAct adapter around existing ToolRuntime.

    The service delegates business execution to existing tools and uses LlamaIndex
    for tool-choice orchestration only.
    """

    def __init__(self, settings: Settings, tool_runtime: ToolRuntime) -> None:
        self._settings = settings
        self._tool_runtime = tool_runtime

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
        if ReActAgent is None or FunctionTool is None or Context is None or LlamaOpenAI is None:
            return None
        llm = self._build_llm(provider=provider, model=model)
        if llm is None:
            return None

        tool_results: list[ToolResult] = []
        tool_calls: list[dict[str, str | int | None]] = []
        next_action_hints: list[str] = []
        tools = []

        if rag_binding is not None:
            tools.append(
                FunctionTool.from_defaults(
                    fn=lambda query, top_k=request.top_k: self._invoke_docs_tool(  # noqa: B023
                        query=query,
                        top_k=top_k,
                        request=request,
                        workspace_id=workspace_id,
                        task_id=task_id,
                        workflow_id=workflow_id,
                        rag_binding=rag_binding,
                        tool_results=tool_results,
                        next_action_hints=next_action_hints,
                        tool_calls=tool_calls,
                    ),
                    name="docs_agent_tool",
                    description="Search workspace documents and return grounded evidence.",
                )
            )

        if ontology_binding is not None:
            tools.append(
                FunctionTool.from_defaults(
                    fn=lambda query, top_k=request.top_k: self._invoke_graph_tool(  # noqa: B023
                        query=query,
                        top_k=top_k,
                        request=request,
                        workspace_id=workspace_id,
                        task_id=task_id,
                        workflow_id=workflow_id,
                        ontology_binding=ontology_binding,
                        tool_results=tool_results,
                        next_action_hints=next_action_hints,
                        tool_calls=tool_calls,
                    ),
                    name="graph_agent_tool",
                    description="Search ontology graph context for entity and relationship grounding.",
                )
            )

        if not tools:
            return None

        agent = ReActAgent(tools=tools, llm=llm)
        prompt = self._react_prompt(request.content)
        content = self._run_agent(agent, prompt)
        return ReActRunResult(
            content=content.strip(),
            tool_results=tool_results,
            next_action_hints=next_action_hints,
            tool_calls=tool_calls,
        )

    def _build_llm(self, *, provider: str | None, model: str | None):
        if provider is None or model is None:
            return None
        if provider == "openai":
            if not self._settings.openai_api_key:
                return None
            return LlamaOpenAI(
                model=model,
                api_key=self._settings.openai_api_key,
                api_base=self._settings.openai_base_url,
            )
        if provider == "openrouter":
            if not self._settings.openrouter_api_key:
                return None
            return LlamaOpenAI(
                model=model,
                api_key=self._settings.openrouter_api_key,
                api_base=self._settings.openrouter_base_url,
            )
        return None

    def _run_agent(self, agent, prompt: str) -> str:
        async def _run_once() -> str:
            ctx = Context(agent)
            handler = agent.run(prompt, ctx=ctx)
            response = await handler
            return str(response)

        try:
            return asyncio.run(_run_once())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_run_once())
            finally:
                loop.close()

    @staticmethod
    def _react_prompt(user_prompt: str) -> str:
        return (
            "Answer the user query using available tools when needed. "
            "Prefer concise grounded output and do not fabricate citations.\n\n"
            f"User query: {user_prompt}"
        )

    def _invoke_docs_tool(
        self,
        *,
        query: str,
        top_k: int,
        request: TaskResolveRequest,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        rag_binding,
        tool_results: list[ToolResult],
        next_action_hints: list[str],
        tool_calls: list[dict[str, str | int | None]],
    ) -> str:
        result = self._tool_runtime.invoke(
            ToolEnvelope(
                call_id=uuid4(),
                tool_name="supersearch.docs",
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                task_type="chat.answer",
                task_payload={"content": request.content, "reason": "react.docs"},
                arguments={
                    "config_ref": getattr(rag_binding, "config_id"),
                    "query": query,
                    "document_ids": list(request.document_ids),
                    "top_k": int(top_k),
                },
                constraints=ToolConstraints(max_results=int(top_k)),
            )
        )
        tool_results.append(result)
        next_action_hints.extend(result.next_action_hints)
        tool_calls.append(
            {
                "step": "tool_call",
                "tool_name": result.tool_name,
                "status": result.status,
                "latency_ms": result.latency_ms,
                "trace_id": result.meta.trace_id,
            }
        )
        return self._tool_result_json(result)

    def _invoke_graph_tool(
        self,
        *,
        query: str,
        top_k: int,
        request: TaskResolveRequest,
        workspace_id: str,
        task_id: str,
        workflow_id: str,
        ontology_binding,
        tool_results: list[ToolResult],
        next_action_hints: list[str],
        tool_calls: list[dict[str, str | int | None]],
    ) -> str:
        result = self._tool_runtime.invoke(
            ToolEnvelope(
                call_id=uuid4(),
                tool_name="supersearch.graph",
                workspace_id=workspace_id,
                task_id=task_id,
                workflow_id=workflow_id,
                task_type="chat.answer",
                task_payload={"content": request.content, "reason": "react.graph"},
                arguments={
                    "config_ref": getattr(ontology_binding, "config_id"),
                    "query": query,
                    "top_k": int(top_k),
                },
                ontology_context=OntologyContextRef(domain=ONTOLOGY_DOMAIN_WORKSPACE),
                constraints=ToolConstraints(max_results=int(top_k)),
            )
        )
        tool_results.append(result)
        next_action_hints.extend(result.next_action_hints)
        tool_calls.append(
            {
                "step": "tool_call",
                "tool_name": result.tool_name,
                "status": result.status,
                "latency_ms": result.latency_ms,
                "trace_id": result.meta.trace_id,
            }
        )
        return self._tool_result_json(result)

    @staticmethod
    def _tool_result_json(result: ToolResult) -> str:
        payload = {
            "status": result.status,
            "error": result.error_message,
            "evidence_count": len(result.evidence),
            "top_evidence": [item.title for item in result.evidence[:3]],
        }
        return json.dumps(payload)

