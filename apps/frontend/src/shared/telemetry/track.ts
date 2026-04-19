export type TelemetryEventName =
  | "ask_started"
  | "ask_completed"
  | "evidence_panel_opened"
  | "source_opened"
  | "task_rerun"
  | "ontology_candidate_reviewed"
  | "build_published"
  | "artifact_opened"
  | "workflow_run_started"
  | "workflow_run_completed"
  | "document_uploaded"
  | "document_reprocessed"
  | "graph_node_opened";

export type TelemetryPayload = Record<string, unknown>;

type TelemetrySink = (
  event: TelemetryEventName,
  payload: TelemetryPayload,
) => void;

const consoleSink: TelemetrySink = (event, payload) => {
  if (typeof window === "undefined") return;
  // eslint-disable-next-line no-console
  console.debug("[telemetry]", event, payload);
};

let currentSink: TelemetrySink = consoleSink;

export function setTelemetrySink(sink: TelemetrySink | null) {
  currentSink = sink ?? consoleSink;
}

export function track(event: TelemetryEventName, payload: TelemetryPayload = {}) {
  currentSink(event, payload);
}
