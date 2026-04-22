import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonList({ count, className = "h-12 w-full" }: { count: number; className?: string }) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} className={className} />
      ))}
    </>
  );
}
