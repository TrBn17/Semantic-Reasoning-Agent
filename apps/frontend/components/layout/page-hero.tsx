import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageHeroProps = {
  badge?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  /** Right column (stats, actions) */
  aside?: ReactNode;
  className?: string;
};

/**
 * Shared hero block for console pages (replaces duplicated hero-panel + eyebrow + h1 stacks).
 */
export function PageHero({
  badge,
  title,
  description,
  aside,
  className,
}: PageHeroProps) {
  return (
    <div
      className={cn(
        "surface-panel-strong hero-panel flex flex-col gap-6 border p-6 md:flex-row md:items-start md:justify-between",
        className,
      )}
    >
      <div className="min-w-0 space-y-3">
        {badge != null ? (
          <div className="text-overline text-primary">{badge}</div>
        ) : null}
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
            {title}
          </h1>
          {description != null ? (
            <p className="max-w-2xl text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
      </div>
      {aside != null ? (
        <div className="w-full shrink-0 md:w-auto md:max-w-md">{aside}</div>
      ) : null}
    </div>
  );
}
