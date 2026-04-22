export type Capabilities = {
  askAvailable: boolean;
  documentsAvailable: boolean;
  evidenceAvailable: boolean;
  ontologyAvailable: boolean;
  graphAvailable: boolean;
  settingsAvailable: boolean;

  tasksAvailable: boolean;
  workflowsAvailable: boolean;
  toolsAvailable: boolean;
  artifactsAvailable: boolean;
  connectorsAvailable: boolean;

  evidencePromotionAvailable: boolean;
  mcpAvailable: boolean;
};

export const BASE_CAPABILITIES: Capabilities = {
  askAvailable: true,
  documentsAvailable: true,
  evidenceAvailable: true,
  ontologyAvailable: true,
  graphAvailable: true,
  settingsAvailable: true,

  tasksAvailable: true,
  workflowsAvailable: false,
  toolsAvailable: true,
  artifactsAvailable: false,
  connectorsAvailable: false,

  evidencePromotionAvailable: false,
  mcpAvailable: false,
};

export function mergeCapabilities(
  base: Capabilities,
  updates: Partial<Capabilities>,
): Capabilities {
  return { ...base, ...updates };
}
