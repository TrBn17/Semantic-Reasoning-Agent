import { PageSkeleton } from "@/components/layout/page-skeleton";

/** Single source for App Router `loading.tsx` segments — avoids 15× duplicate files. */
export function RouteLoadingDefault() {
  return <PageSkeleton />;
}

export function RouteLoadingDetail() {
  return <PageSkeleton variant="detail" />;
}

export function RouteLoadingCanvas() {
  return <PageSkeleton variant="canvas" />;
}

export function RouteLoadingSplit() {
  return <PageSkeleton variant="split" />;
}
