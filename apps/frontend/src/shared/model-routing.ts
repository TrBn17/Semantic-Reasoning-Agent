/** Encodes `provider` + `model` for selects and task routing (single delimiter). */

const SEP = "::" as const;

export function composeProviderModel(
  provider: string | null | undefined,
  model: string | null | undefined,
): string {
  if (!provider?.trim() || !model?.trim()) return "";
  return `${provider}${SEP}${model}`;
}

export function parseProviderModelValue(
  value?: string | null,
): { provider: string; model: string } | null {
  if (!value) return null;
  const i = value.indexOf(SEP);
  if (i < 0) return null;
  const provider = value.slice(0, i);
  const model = value.slice(i + SEP.length);
  if (!provider || !model) return null;
  return { provider, model };
}
