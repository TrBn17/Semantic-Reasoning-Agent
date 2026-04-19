import { Skeleton } from "@/components/ui/skeleton";

export function PageSkeleton({
  variant = "default",
}: {
  variant?: "default" | "detail" | "canvas" | "split";
}) {
  if (variant === "canvas") {
    return (
      <div className="flex h-full w-full flex-col">
        <div className="flex items-start justify-between border-b bg-muted/20 px-6 py-4">
          <div className="space-y-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-3 w-56" />
          </div>
          <Skeleton className="h-5 w-40" />
        </div>
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 p-6">
            <Skeleton className="h-full w-full min-h-[400px]" />
          </div>
          <aside className="hidden w-80 shrink-0 border-l bg-muted/10 p-4 lg:block">
            <Skeleton className="h-40 w-full" />
          </aside>
        </div>
      </div>
    );
  }

  if (variant === "split") {
    return (
      <div className="flex h-full">
        <div className="w-72 shrink-0 space-y-2 border-r bg-muted/20 p-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
        <div className="flex flex-1 flex-col gap-4 p-6">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-72" />
          <div className="flex-1 space-y-3 pt-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (variant === "detail") {
    return (
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <div className="space-y-2">
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-3 w-72" />
        </div>
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
      <div className="space-y-2">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-3 w-80" />
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    </div>
  );
}
