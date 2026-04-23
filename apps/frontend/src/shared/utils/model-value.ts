export function composeModelValue(provider: string, model: string) {
  return `${provider}::${model}`;
}

export function parseModelValue(value?: string | null) {
  if (!value) return null;
  const delimiterIndex = value.indexOf("::");
  if (delimiterIndex <= 0 || delimiterIndex >= value.length - 2) return null;
  const provider = value.slice(0, delimiterIndex);
  const model = value.slice(delimiterIndex + 2);
  if (!provider || !model) return null;
  return { provider, model };
}
