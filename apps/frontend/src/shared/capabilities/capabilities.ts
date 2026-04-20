export type Capabilities = {
  askAvailable: boolean;
  documentsAvailable: boolean;
  evidenceAvailable: boolean;
  ontologyAvailable: boolean;
  graphAvailable: boolean;
  settingsAvailable: boolean;
  agentsAvailable: boolean;

  tasksAvailable: boolean;
  workflowsAvailable: boolean;
  toolsAvailable: boolean;
  artifactsAvailable: boolean;
  connectorsAvailable: boolean;

  evidencePromotionAvailable: boolean;
  mcpAvailable: boolean;
};

const DEFAULT_CAPABILITIES: Capabilities = {
  askAvailable: true,
  documentsAvailable: true,
  evidenceAvailable: true,
  ontologyAvailable: true,
  graphAvailable: true,
  settingsAvailable: true,
  agentsAvailable: true,

  tasksAvailable: true,
  workflowsAvailable: true,
  toolsAvailable: true,
  artifactsAvailable: false,
  connectorsAvailable: false,

  evidencePromotionAvailable: false,
  mcpAvailable: false,
};

export function getCapabilities(): Capabilities {
  return DEFAULT_CAPABILITIES;
}
