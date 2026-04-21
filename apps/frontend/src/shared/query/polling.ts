/**
 * React Query `refetchInterval`: poll only while status is in `activeStatuses`.
 */
export function refetchWhileStatus(
  status: string | undefined,
  activeStatuses: readonly string[],
  intervalMs: number,
): number | false {
  if (!status) return false;
  return activeStatuses.includes(status) ? intervalMs : false;
}
