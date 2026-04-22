export function composeModelValue(provider: string, model: string) {
  return `${provider}::${model}`;
}

export function parseModelValue(value?: string | null) {
  if (!value) return null;
  const [provider, model] = value.split("::");
  if (!provider || !model) return null;
  return { provider, model };
}
