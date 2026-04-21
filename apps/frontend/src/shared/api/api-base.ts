export function getApiBaseUrl(): string {
  const fromEnv =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.INTERNAL_API_BASE_URL ??
    "http://localhost:8000/api/v1";
  return fromEnv.replace(/\/$/, "");
}
