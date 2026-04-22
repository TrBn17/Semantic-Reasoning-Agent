// TypeScript mirrors of backend Pydantic schemas.
// Source: apps/backend/src/semantic_reasoning_agent/schemas/

export type DocumentStatus = "uploaded" | "parsed" | "indexed" | "failed";
export type JobStatus = "pending" | "running" | "completed" | "failed";
export type OntologyBuildStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "published";
export type OntologyReviewStatus = "pending_review" | "approved" | "rejected";
export type OntologyStepStatus = "pending" | "running" | "completed" | "failed";
export type OntologyReviewAction = "approve" | "reject";
export type MessageRole = "user" | "assistant" | "system";
export type TaskOutputClass =
  | "answer"
  | "ontology_candidates"
  | "review_task"
  | "graph_update_request"
  | "promoted_evidence"
  | "artifact";
export type TaskRunStatus = "pending" | "running" | "completed" | "failed";
export type WorkflowMode = "deterministic" | "agentic";

export interface WorkspaceSummary {
  id: string;
  name: string;
}

export interface AuthMeResponse {
  id: string;
  email: string;
  display_name: string;
  active_workspace: WorkspaceSummary;
}

export interface Message {
  id: string;
  role: MessageRole | string;
  content: string;
  created_at: string;
}

export interface ConversationCreateRequest {
  title: string;
  workspace_id?: string | null;
  agent_profile_id?: string | null;
  provider?: string;
  model?: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
  workspace_id: string;
  agent_profile_id?: string | null;
  provider: string;
  model: string;
  uses_model_override: boolean;
  effective_agent_name?: string | null;
  effective_tool_names: string[];
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationModelSelectionRequest {
  provider: string;
  model: string;
  workspace_id?: string | null;
}

export interface ConversationAgentProfileRequest {
  agent_profile_id?: string | null;
  workspace_id?: string | null;
  clear_model_override?: boolean;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  provider?: string;
  model?: string;
  use_retrieval?: boolean;
  workspace_id?: string | null;
  document_ids?: string[];
  top_k?: number;
  enabled_tool_names?: string[] | null;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_title: string;
  document_type: string;
  excerpt: string;
  location_label: string;
  source_url: string;
  page_number?: number | null;
  heading_path?: string | null;
  sheet_name?: string | null;
  row_start?: number | null;
  row_end?: number | null;
}

export interface ChatReply {
  conversation_id: string;
  reply: Message;
  citations: Citation[];
  tool_calls: ChatToolCallSummary[];
}

export interface ChatToolCallSummary {
  tool_name: string;
  status: string;
  trace_id?: string | null;
  latency_ms: number;
}

export type ChatStreamEventType =
  | "message_start"
  | "content_delta"
  | "citations"
  | "tool_call_start"
  | "tool_call_end"
  | "message_complete"
  | "error";

export interface ChatStreamEvent {
  event: ChatStreamEventType;
  data: Record<string, unknown>;
}

export interface ModelOption {
  provider: string;
  model: string;
  label: string;
  description: string;
  ready: boolean;
  enabled: boolean;
  supports_runtime: boolean;
  supports_streaming: boolean;
  supports_structured_output: boolean;
  context_window?: number | null;
  recommended_for: string[];
  required_env_fields: string[];
  missing_env_fields: string[];
  reason: string;
}

export interface ProviderFieldDefinition {
  key: string;
  label: string;
  placeholder: string;
  required: boolean;
  secret: boolean;
  help_text: string;
  input_type: "text" | "select";
  options: string[];
}

export interface ProviderFieldValue {
  key: string;
  configured: boolean;
  source: "database" | "runtime" | "missing";
  masked_value: string;
}

export interface ProviderConfigResponse {
  provider: string;
  label: string;
  enabled: boolean;
  supports_runtime: boolean;
  ready: boolean;
  reason: string;
  fields: ProviderFieldDefinition[];
  values: ProviderFieldValue[];
}

export interface TaskDefinition {
  task_type: string;
  label: string;
  description: string;
}

export interface TaskAssignmentResponse {
  task_type: string;
  provider: string;
  model: string;
  ready: boolean;
  reason: string;
}

export interface ProviderConfigUpdate {
  provider: string;
  enabled: boolean;
  values: Record<string, string>;
}

export interface TaskAssignmentUpdate {
  task_type: string;
  provider: string;
  model: string;
}

export interface AgentSettingsResponse {
  workspace_id: string;
  models: ModelOption[];
  providers: ProviderConfigResponse[];
  tasks: TaskDefinition[];
  task_assignments: TaskAssignmentResponse[];
}

export interface AgentSettingsUpdateRequest {
  workspace_id: string;
  providers: ProviderConfigUpdate[];
  task_assignments: TaskAssignmentUpdate[];
}

export interface AgentProfileTaskModelAssignment {
  task_type: string;
  provider: string;
  model: string;
}

export interface AgentProfileToolAssignment {
  tool_name: string;
  enabled: boolean;
}

export interface ToolPolicySchema {
  mode: string;
  allowed_tools: string[];
  blocked_tools: string[];
}

export interface EvidencePolicySchema {
  allowed_sources: string[];
  allow_model_only_fallback: boolean;
}

export interface AgentCapabilityConfigSchema {
  capability_preset: string;
  tool_policy: ToolPolicySchema;
  knowledge_pack_ids: string[];
  evidence_policy: EvidencePolicySchema;
}

export interface AgentCapabilityPresetSchema {
  preset: string;
  label: string;
  description: string;
  allowed_tool_families: string[];
  default_tool_order: string[];
  ontology_enabled: boolean;
  graph_enabled: boolean;
  external_tools_allowed: boolean;
}

export interface AgentCapabilityCatalogResponse {
  presets: AgentCapabilityPresetSchema[];
  tool_families: Record<string, Array<Record<string, string>>>;
}

export interface AgentCapabilityToolSchema {
  tool_name: string;
  label: string;
  family: string;
  description: string;
  risk_level: string;
  requires_confirmation: boolean;
}

export interface AgentProfileResponse {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  system_prompt: string;
  allow_chat_model_override: boolean;
  is_default: boolean;
  status: string;
  policy_config: Record<string, unknown>;
  capability_preset: string;
  tool_policy: ToolPolicySchema;
  knowledge_pack_ids: string[];
  evidence_policy: EvidencePolicySchema;
  task_models: AgentProfileTaskModelAssignment[];
  tool_assignments: AgentProfileToolAssignment[];
  created_at: string;
  updated_at: string;
}

export interface AgentProfileCreateRequest {
  workspace_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  allow_chat_model_override?: boolean;
  is_default?: boolean;
  status?: string;
  policy_config?: Record<string, unknown>;
  capability_preset?: string;
  tool_policy?: ToolPolicySchema;
  knowledge_pack_ids?: string[];
  evidence_policy?: EvidencePolicySchema;
  task_models?: AgentProfileTaskModelAssignment[];
  tool_assignments?: AgentProfileToolAssignment[];
}

export interface AgentProfileUpdateRequest {
  name?: string;
  description?: string;
  system_prompt?: string;
  allow_chat_model_override?: boolean;
  status?: string;
  policy_config?: Record<string, unknown>;
  capability_preset?: string;
  tool_policy?: ToolPolicySchema;
  knowledge_pack_ids?: string[];
  evidence_policy?: EvidencePolicySchema;
  task_models?: AgentProfileTaskModelAssignment[];
  tool_assignments?: AgentProfileToolAssignment[];
}

export interface SettingsModelOption {
  provider: string;
  model: string;
  label: string;
  description: string;
  ready: boolean;
  reason: string;
  supports_streaming: boolean;
  supports_structured_output: boolean;
  context_window?: number | null;
}

export interface SettingsProviderFieldValue {
  key: string;
  configured: boolean;
  source: "database" | "runtime" | "missing";
  display_value: string;
}

export interface SettingsProviderResponse {
  provider: string;
  label: string;
  enabled: boolean;
  ready: boolean;
  status_text: string;
  fields: ProviderFieldDefinition[];
  values: SettingsProviderFieldValue[];
}

export type SettingsUseCase =
  | "chat_default"
  | "retrieval_answer_default"
  | "ontology_extraction_default"
  | "narrative_default"
  | "dashboard_default";

export interface SettingsTaskDefaultResponse {
  use_case: SettingsUseCase;
  task_type: string;
  label: string;
  description: string;
  provider: string;
  model: string;
  ready: boolean;
  reason: string;
}

export interface SettingsTaskDefaultUpdate {
  use_case: SettingsUseCase;
  provider: string;
  model: string;
}

export interface SettingsProviderUpdate {
  provider: string;
  enabled: boolean;
  values: Record<string, string>;
}

export interface SettingsResponse {
  workspace: WorkspaceSummary;
  providers: SettingsProviderResponse[];
  model_catalog: SettingsModelOption[];
  task_defaults: SettingsTaskDefaultResponse[];
  preferred_default_chat_model?: SettingsModelOption | null;
}

export interface SettingsUpdateRequest {
  workspace_id: string;
  providers: SettingsProviderUpdate[];
  task_defaults: SettingsTaskDefaultUpdate[];
}

export interface KnowledgePackResponse {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  document_ids: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgePackCreateRequest {
  workspace_id: string;
  name: string;
  description?: string;
  document_ids?: string[];
  status?: string;
}

export interface KnowledgePackUpdateRequest {
  name?: string;
  description?: string;
  document_ids?: string[];
  status?: string;
}

export interface DocumentResponse {
  id: string;
  title: string;
  filename: string;
  workspace_id: string;
  document_type: string;
  status: DocumentStatus;
  parser_version: string;
  chunk_count: number;
  tags: string[];
  ingestion_options: Record<string, unknown>;
  source_url: string;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
}

export interface DocumentJobResponse {
  id: string;
  name: string;
  status: JobStatus;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
}

export interface DocumentReprocessResponse {
  document: DocumentResponse;
  jobs: DocumentJobResponse[];
}

export interface DocumentUploadFailure {
  filename: string;
  reason: string;
}

export interface DocumentBatchUploadResponse {
  uploaded: DocumentResponse[];
  failed: DocumentUploadFailure[];
}

export interface DocumentOptionChoice {
  value: string;
  label: string;
  description?: string | null;
}

export interface DocumentIngestionOptionsResponse {
  pdf_mode: string;
  output_format: string;
  use_llm: boolean;
  force_ocr: boolean;
  strip_existing_ocr: boolean;
  extract_images: boolean;
}

export interface DocumentIngestionCapabilitiesResponse {
  supported_types: string[];
  marker_supported_types: string[];
  csv_supported_types: string[];
  default_options: DocumentIngestionOptionsResponse;
  pdf_mode_options: DocumentOptionChoice[];
  output_format_options: DocumentOptionChoice[];
  supports_extract_images: boolean;
}

export interface RetrievalResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  document_type: string;
  score: number;
  excerpt: string;
  citation: Citation;
}

export interface RetrievalSearchRequest {
  query: string;
  workspace_id?: string | null;
  document_ids?: string[];
  top_k?: number;
}

export interface RetrievalSearchResponse {
  query: string;
  results: RetrievalResult[];
}

export interface RetrievalReindexRequest {
  document_ids: string[];
}

export interface RetrievalReindexResponse {
  reindexed_document_ids: string[];
}

export interface OntologyBuildCreateRequest {
  document_id: string;
  workspace_id?: string | null;
  provider?: string | null;
  model?: string | null;
}

export interface OntologyBuildStepResponse {
  id: string;
  name: string;
  status: OntologyStepStatus;
  detail?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface OntologyCandidateEntityResponse {
  id: string;
  build_id: string;
  document_id: string;
  workspace_id: string;
  name: string;
  canonical_name: string;
  resolution_key: string;
  entity_type: string;
  confidence: number;
  status: OntologyReviewStatus;
  source_chunk_id?: string | null;
  evidence_text: string;
  provenance: Record<string, unknown>;
  aliases: string[];
  merged_into_entity_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OntologyCandidateRelationResponse {
  id: string;
  build_id: string;
  document_id: string;
  workspace_id: string;
  source_entity_id?: string | null;
  target_entity_id?: string | null;
  source_name: string;
  target_name: string;
  relation_type: string;
  confidence: number;
  status: OntologyReviewStatus;
  source_chunk_id?: string | null;
  evidence_text: string;
  provenance: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OntologyBuildResponse {
  id: string;
  document_id: string;
  workspace_id: string;
  status: OntologyBuildStatus;
  domain?: string | null;
  ontology_title?: string | null;
  provider?: string | null;
  model?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  updated_at: string;
  error_message?: string | null;
  published_version_id?: string | null;
  entity_count: number;
  relation_count: number;
  pending_entity_count: number;
  pending_relation_count: number;
  steps: OntologyBuildStepResponse[];
}

export interface OntologyReviewRequest {
  action: OntologyReviewAction;
}

export interface OntologyCandidateEntityUpdateRequest {
  name?: string | null;
  canonical_name?: string | null;
  resolution_key?: string | null;
  entity_type?: string | null;
  aliases?: string[] | null;
  evidence_text?: string | null;
  confidence?: number | null;
  status?: OntologyReviewStatus | null;
}

export interface OntologyCandidateRelationUpdateRequest {
  source_entity_id?: string | null;
  target_entity_id?: string | null;
  source_name?: string | null;
  target_name?: string | null;
  relation_type?: string | null;
  evidence_text?: string | null;
  confidence?: number | null;
  status?: OntologyReviewStatus | null;
}

export interface OntologyVersionResponse {
  id: string;
  workspace_id: string;
  version_number: number;
  source_build_id: string;
  created_at: string;
  entity_count: number;
  relation_count: number;
}

export interface OntologyEntityResponse {
  id: string;
  version_id: string;
  workspace_id: string;
  resolution_key: string;
  name: string;
  entity_type: string;
  aliases: string[];
  source_build_id: string;
  source_document_id: string;
  created_at: string;
}

export interface OntologyRelationResponse {
  id: string;
  version_id: string;
  workspace_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relation_type: string;
  confidence: number;
  source_build_id: string;
  source_document_id: string;
  evidence_text: string;
  provenance: Record<string, unknown>;
  created_at: string;
}

export interface OntologyPublishResponse {
  build: OntologyBuildResponse;
  version: OntologyVersionResponse;
}

export interface OntologyGraphResponse {
  workspace_id: string;
  version?: OntologyVersionResponse | null;
  entities: OntologyEntityResponse[];
  relations: OntologyRelationResponse[];
}

/** POST /knowledge-graph/extract */
export interface KnowledgeGraphExtractRequest {
  document_id: string;
  workspace_id?: string | null;
}

/** PATCH /knowledge-graph/relations/{id} */
export interface KnowledgeGraphRelationPatch {
  relation_type?: string | null;
  confidence?: number | null;
  evidence_text?: string | null;
}

/** POST /knowledge-graph/ingest */
export interface KnowledgeGraphIngestResponse {
  workspace_id: string;
  document_ids: string[];
  build_ids: string[];
  publish: OntologyPublishResponse;
}

export type ToolFamily =
  | "document"
  | "retrieval"
  | "ontology"
  | "graph"
  | "web"
  | "mcp"
  | "artifact"
  | "admin";

export type ToolType = "internal_service" | "external_adapter" | "worker_job";
export type RiskLevel = "low" | "medium" | "high";
export type SideEffectLevel = "read_only" | "write_internal" | "write_external";
export type WorkspaceScope = "workspace" | "global";
export type ToolStatus = "success" | "partial" | "failed";
export type SourceType =
  | "internal_chunk"
  | "web_page"
  | "graph_node"
  | "graph_edge"
  | "mcp_result"
  | "generated_artifact";
export type AnchorType = "page" | "section" | "sheet_row" | "url_fragment" | "graph_ref" | "artifact_ref";

export interface ToolSpec {
  tool_name: string;
  tool_family: ToolFamily;
  tool_type: ToolType;
  version: string;
  description: string;
  input_schema: Record<string, unknown>;
  input_schema_ref: string;
  output_schema_ref: string;
  capabilities: string[];
  risk_level: RiskLevel;
  side_effect_level: SideEffectLevel;
  supports_parallel: boolean;
  supports_streaming: boolean;
  requires_confirmation: boolean;
  timeout_ms: number;
  workspace_scope: WorkspaceScope;
}

export interface OntologyContextRef {
  domain?: string | null;
  entity_hints: string[];
  relation_hints: string[];
  normalization_rules: Array<Record<string, unknown>>;
}

export interface ToolConstraints {
  web_enabled: boolean;
  freshness_required: boolean;
  max_results: number;
  timeout_ms: number;
}

export interface StandardToolInput {
  call_id: string;
  tool_name: string;
  workspace_id: string;
  task_id: string;
  task_type: string;
  task_payload?: Record<string, unknown>;
  ontology_context?: OntologyContextRef;
  arguments: Record<string, unknown>;
  constraints?: ToolConstraints;
  workflow_id?: string | null;
}

export interface CitationAnchor {
  anchor_type: AnchorType;
  label: string;
  locator: string;
}

export interface Provenance {
  workspace_id: string;
  captured_at: string;
  source_id?: string | null;
  tool_call_id?: string | null;
  parser_version?: string | null;
  extractor_version?: string | null;
  model?: string | null;
}

export interface Evidence {
  evidence_id: string;
  source_type: SourceType;
  title: string;
  content: string;
  citation_anchor: CitationAnchor;
  provenance: Provenance;
  summary?: string | null;
  uri?: string | null;
  document_id?: string | null;
  chunk_id?: string | null;
  page?: number | null;
  section?: string | null;
  sheet_name?: string | null;
  row_range?: string | null;
  entity_ids: string[];
  relation_ids: string[];
  score: number;
  trust_score: number;
  freshness_ts?: string | null;
}

export interface ToolMeta {
  provider?: string | null;
  provider_version?: string | null;
  trace_id?: string | null;
}

export interface StandardToolOutput {
  call_id: string;
  tool_name: string;
  status: ToolStatus;
  started_at: string;
  finished_at: string;
  latency_ms: number;
  evidence: Evidence[];
  artifacts: Array<Record<string, unknown>>;
  state_patch: Record<string, unknown>;
  next_action_hints: string[];
  error_code?: string | null;
  error_message?: string | null;
  meta: ToolMeta;
}

export interface ToolCallSummary {
  tool_name: string;
  status: string;
  trace_id?: string | null;
  latency_ms: number;
  next_action_hints: string[];
}

export interface TaskResolutionRequest {
  conversation_id?: string | null;
  entrypoint?: string;
  content: string;
  workspace_id?: string | null;
  task_type?: string;
  requested_output?: TaskOutputClass;
  provider?: string;
  model?: string;
  use_retrieval?: boolean;
  document_ids?: string[];
  top_k?: number;
  web_enabled?: boolean;
  freshness_required?: boolean;
}

export interface TaskResolutionResponse {
  task_id: string;
  workflow_run_id: string;
  workflow_id: string;
  workflow_mode: WorkflowMode;
  status: TaskRunStatus;
  output_type: TaskOutputClass;
  reply?: string | null;
  citations: Citation[];
  evidence: Evidence[];
  tool_calls: ToolCallSummary[];
  trace_id?: string | null;
  provider?: string | null;
  model?: string | null;
}

export interface TaskRunRecord {
  id: string;
  workspace_id: string;
  entrypoint: string;
  task_type: string;
  requested_output: TaskOutputClass;
  status: TaskRunStatus;
  workflow_id?: string | null;
  conversation_id?: string | null;
  provider?: string | null;
  model?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  updated_at: string;
  output_payload: Record<string, unknown>;
}

export interface WorkflowSpec {
  workflow_id: string;
  version: string;
  mode: WorkflowMode;
  description: string;
}

export interface WorkflowRunRecord {
  id: string;
  task_id: string;
  workflow_id: string;
  workflow_version: string;
  status: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  output_payload: Record<string, unknown>;
}

export interface ToolCallRecord {
  id: string;
  task_id: string;
  workflow_run_id?: string | null;
  call_id: string;
  tool_name: string;
  status: string;
  trace_id?: string | null;
  provider?: string | null;
  provider_version?: string | null;
  latency_ms: number;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
}
