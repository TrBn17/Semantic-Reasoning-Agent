# Query Runtime Improvement Spec

## Purpose

This document defines the technical capabilities that must be added to make query resolution stronger across:

- semantic resolution
- ontology grounding
- context assembly
- controlled tool-calling
- evidence sufficiency and conflict handling
- runtime traceability

This is an implementation-oriented checklist for the current repository state. It assumes the existing backend baseline remains in place:

- `retrieval.internal` is available
- `ontology.lookup` is available
- `graphiti.search` is available when `Graphiti` is enabled
- chat currently resolves through `TaskRuntimeService`
- published ontology graph remains the stable workspace ontology source

This document does not split work by phase. It lists the target technical features and the required boundaries.

---

## Current Gaps

The current runtime can retrieve document chunks and read ontology graph data, but query resolution is still shallow:

- ontology lookup is mostly substring-based for query-time matching
- chat does not run a true tool-calling loop
- there is no explicit task interpretation or workflow selection layer
- evidence from retrieval, ontology, and runtime graph is not merged by a formal ranking policy
- there is no sufficiency gate before fallback or finish
- there is no conflict engine that can route to review instead of answer
- task runs and tool decisions are not durably persisted for audit/debugging

---

## Architectural Boundaries

### Published Ontology Graph

Use the published ontology graph as the stable semantic source for:

- entity identity
- aliases
- resolution keys
- entity types
- relation types
- approved workspace ontology facts

Source of truth:

- Postgres-backed published ontology version
- exposed through `OntologyService.get_graph()`
- consumed by `ontology.lookup`

Do not treat draft graph state as runtime knowledge.

### Graphiti Runtime Graph

Use `Graphiti` only for runtime graph search and temporal/contextual graph retrieval when enabled.

Use `Graphiti` for:

- graph search over runtime graph memory
- graph neighborhood retrieval
- temporal context if the runtime graph stores episodes/events
- optional enrichment when ontology lookup and internal retrieval are insufficient

Do not use `Graphiti` as the canonical ontology source.

Notes:

- if `Graphiti` is disabled, query resolution must still work through internal retrieval and published ontology lookup
- publish should never depend on `Graphiti` availability for correctness of the ontology record
- if full ontology-to-Graphiti ingestion is added later, that ingestion must still be derived from published state, not draft state

### Internal Retrieval

Use `retrieval.internal` for document-grounded evidence:

- chunk retrieval
- citation-bearing internal evidence
- high-priority support for grounded answers

Internal retrieval should remain the default first retrieval path for internal questions unless policy or task grounding says otherwise.

---

## Required Technical Features

## 1. Task Interpretation Layer

Add a dedicated `TaskInterpreter` before tool selection.

Required outputs:

- `intent`
- `requested_output_type`
- `domain_guess`
- `freshness_required`
- `sensitivity_level`
- `use_internal_only`
- `candidate_workflow_type`

Minimum supported intents:

- answer a question
- inspect an entity or relation
- compare internal facts
- request missing knowledge
- propose graph update
- create review task

This layer must not call tools directly. It only classifies the task and passes structured intent downstream.

## 2. Ontology Grounding Service

Add an `OntologyGroundingService` that maps the interpreted request to workspace ontology structures.

Required outputs:

- `domain`
- `entity_candidates`
- `relation_candidates`
- `entity_type_hints`
- `relation_type_hints`
- `grounding_confidence`
- `grounding_status`

Required `grounding_status` values:

- `matched`
- `ambiguous`
- `unmatched`

Matching strategy must be multi-stage, not substring-only:

- exact `resolution_key` match
- exact or normalized alias match
- normalized token overlap
- type-aware candidate filtering
- embedding similarity against entity names, aliases, and type descriptions
- rerank by local context and query intent

Optional but recommended:

- lightweight LLM reranker for top-N candidates only
- synonym/taxonomy support from ontology assets

Hard rule:

- query-time grounding must always return scored candidates, not a single unqualified best guess

## 3. Entity and Relation Resolution Indexes

Add dedicated query-time resolution indexes for ontology search.

Recommended storage:

- Postgres tables remain source of truth
- add derived lookup/index tables or materialized views for normalized search
- optionally add vector embeddings for entities, aliases, type definitions, and relation phrases

Required indexed fields:

- entity id
- entity name
- aliases
- resolution key
- entity type
- relation type
- source build id
- source document id
- publish version id

If vector search is added, note clearly:

- use Qdrant only as a derived index, never as ontology source of truth
- runtime must degrade cleanly when vector search is unavailable

## 4. Context Assembly Service

Add a `ContextAssemblerService` that merges evidence from multiple sources into one normalized bundle.

Input sources:

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search` when enabled
- optional later sources such as web or MCP

Required output structure:

- `document_evidence`
- `ontology_evidence`
- `runtime_graph_evidence`
- `merged_facts`
- `conflicts`
- `coverage_gaps`
- `trace`

Required behavior:

- deduplicate overlapping evidence
- group related evidence by entity or relation
- preserve provenance and citation anchors
- rank evidence by trust policy
- label whether a fact is approved ontology fact, document evidence, runtime graph hint, or generated inference

Default ranking policy:

1. approved published ontology facts
2. internal document evidence with strong citations
3. Graphiti runtime graph evidence
4. lower-confidence inferred summaries

Hard rule:

- `Graphiti` matches must never silently override approved ontology facts

## 5. Evidence Normalization Rules

Every query-time source must normalize to one evidence bundle contract.

Required normalized fields:

- source class
- trust score
- confidence score
- freshness timestamp
- entity ids
- relation ids
- citation anchor
- provenance

Add explicit source classes:

- `published_ontology_fact`
- `internal_chunk`
- `runtime_graph_match`
- `inferred_summary`
- `external_web_evidence`
- `mcp_result`

The runtime must distinguish:

- fact directly approved in ontology
- fact only seen in document text
- fact only seen in `Graphiti`

## 6. Workflow Selection Policy

Add a `WorkflowSelector` that chooses deterministic resolution behavior before any dynamic loop starts.

Inputs:

- interpreted task
- ontology grounding result
- freshness need
- sensitivity flags
- current evidence sufficiency

Required workflow decisions:

- `retrieval_first`
- `ontology_first`
- `hybrid_grounded_answer`
- `graph_enrichment`
- `review_required`
- `fallback_generation`

Examples:

- if entity grounding is high-confidence and ontology already contains direct facts, use `ontology_first`
- if query asks for cited internal answer, use `retrieval_first`
- if retrieval is thin but entity grounding is strong, use `hybrid_grounded_answer`
- if ontology and retrieval disagree, use `review_required`

## 7. Controlled Tool-Calling Loop

Add an `AgenticLoopService` or equivalent runtime loop that orchestrates tool calls.

Allowed initial tool set:

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search`

Loop steps:

1. interpret task
2. ground against ontology
3. select workflow
4. choose candidate tools
5. execute tool call or parallel read-only calls
6. normalize and merge evidence
7. run sufficiency/conflict checks
8. continue, reroute, or stop

Required loop controls:

- max step count
- max repeated calls to same tool with equivalent args
- total timeout budget
- per-tool timeout budget
- stop reasons
- loop audit trace

Hard rules:

- no uncontrolled recursive tool calling
- no repeated `ontology.lookup` or `graphiti.search` with near-identical arguments unless the prior result changed the plan
- high-risk tools must remain outside the default loop until confirmation policy exists

## 8. Parallel Tool Policy

Support parallel calls only for read-only, independent sources.

Allowed parallel combinations:

- `retrieval.internal` + `ontology.lookup`
- `retrieval.internal` + `graphiti.search`
- `ontology.lookup` + `graphiti.search`

Do not parallelize when:

- later calls depend on resolved entity ids from earlier calls
- ambiguity must be reduced before tool arguments are safe
- a sufficiency gate should decide whether fallback is even needed

Required merge metadata:

- which calls ran in parallel
- which evidence won during rerank
- why lower-ranked evidence was retained or suppressed

## 9. Sufficiency Engine

Add an `EvidenceJudge` or `SufficiencyEngine`.

Required outputs:

- `sufficient`
- `insufficient`
- `conflicted`
- `needs_review`

Minimum deterministic checks:

- enough evidence count
- enough source diversity
- citation presence for grounded answers
- entity grounding confidence above threshold
- no unresolved critical contradictions

Recommended checks:

- direct ontology fact exists for requested entity/relation
- document evidence supports or refutes graph fact
- Graphiti result is only used as supporting context unless corroborated

Hard rule:

- if evidence is insufficient, the runtime must not produce a confident grounded answer template

## 10. Conflict Engine

Add explicit conflict detection before output assembly.

Conflict types to detect:

- ontology says X, document evidence says Y
- two documents say incompatible facts
- grounded entity is ambiguous across multiple ontology entities
- Graphiti match conflicts with published ontology

Required conflict outputs:

- conflict type
- impacted entity ids
- impacted relation ids
- severity
- recommended action

Recommended actions:

- answer with uncertainty
- ask for clarification
- route to review task
- propose ontology update candidate

## 11. Output Router

Add an output router after evidence judgment.

Supported output classes:

- `grounded_answer`
- `clarification_request`
- `review_task`
- `ontology_candidate_patch`
- `no_match`

Rules:

- if evidence is sufficient and unconflicted, return `grounded_answer`
- if grounding is ambiguous, return `clarification_request`
- if evidence reveals likely missing ontology fact, return `ontology_candidate_patch`
- if evidence is high-value but conflicting, return `review_task`

Do not force every query into plain answer generation.

## 12. Fallback Generation Rules

Fallback LLM generation must remain bounded.

Allowed only when:

- no sufficient grounded result exists
- policy allows non-grounded generation
- user is not asking for strict internal citations

Required fallback labeling:

- generated answer must be marked as non-grounded or weakly grounded
- the runtime should surface why grounded evidence was insufficient

Do not present fallback text as ontology-backed truth.

## 13. Graphiti Integration Notes

If `Graphiti` remains enabled, document its role explicitly in code and APIs.

Required behavior:

- `Graphiti` is optional runtime graph enrichment
- `Graphiti` search failures must degrade to partial results, not break the query pipeline
- `Graphiti` evidence must carry separate source labeling

Recommended future additions if `Graphiti` is kept:

- explicit published-ontology-to-Graphiti ingestion adapter
- runtime graph neighborhood expansion by grounded entity id
- temporal reasoning hooks for event-oriented queries

Do not assume `Graphiti` can replace ontology approval, ontology publishing, or document citations.

## 14. Persistence and Audit

Add durable tables for runtime traceability.

Recommended records:

- `task_runs`
- `task_run_steps`
- `tool_calls`
- `evidence_bundles`
- `evidence_conflicts`
- `output_routes`

Persist at minimum:

- task id
- workflow id
- interpreted intent
- grounding result
- tool inputs and outputs
- sufficiency result
- conflict result
- final output type
- stop reason

This is required for debugging low-quality query behavior and tuning thresholds.

## 15. Metrics and Evaluation

Add query quality evaluation for the new runtime.

Track:

- grounding accuracy
- ambiguous grounding rate
- answer sufficiency rate
- review routing rate
- no-match rate
- Graphiti contribution rate
- retrieval-only vs ontology-only vs hybrid win rate

Create a fixed regression set with:

- entity lookup queries
- alias-heavy queries
- relation lookup queries
- conflicting evidence queries
- no-match queries
- Graphiti-disabled queries

## 16. API and Contract Additions

Recommended internal service outputs should map to typed schemas.

Add or extend contracts for:

- `TaskInterpretation`
- `OntologyGroundingResult`
- `ContextBundle`
- `SufficiencyResult`
- `ConflictReport`
- `OutputRouteDecision`

Recommended API support:

- `POST /api/v1/tasks/resolve`
- optional debug flag to return reasoning trace metadata
- optional admin endpoint to inspect query grounding and evidence bundles

Do not expose raw chain-of-thought. Expose structured runtime trace only.

---

## Suggested Module Additions

Likely backend modules to add:

- `services/task_interpreter.py`
- `services/ontology_grounding_service.py`
- `services/context_assembler_service.py`
- `services/evidence_judge.py`
- `services/conflict_engine.py`
- `services/output_router.py`
- `services/agentic_loop_service.py`

Likely schema additions:

- `schemas/tasks.py`
- `schemas/runtime_trace.py`

Likely persistence additions:

- runtime/audit ORM models and migrations for task runs and tool calls

---

## Non-Goals

The following are not required for the first implementation of stronger query resolution:

- full semantic web or OWL reasoning
- unconstrained autonomous agent behavior
- making `Graphiti` mandatory
- replacing Postgres ontology state with a graph database
- allowing draft graph edits to affect query runtime before publish

---

## Implementation Rules

- published ontology remains the semantic authority
- `Graphiti` is optional enrichment, not authority
- internal retrieval remains citation authority for document-grounded answers
- draft graph stays outside runtime knowledge until publish
- every tool result must normalize into evidence with provenance
- every final answer must be traceable to evidence class and route decision
