import type { ReactNode } from "react";
import { cn } from "@/shared/utils";

type SettingRowProps = {
  label: ReactNode;
  description?: ReactNode;
  control: ReactNode;
  htmlFor?: string;
  orientation?: "horizontal" | "vertical";
  className?: string;
};

export function SettingRow({
  label,
  description,
  control,
  htmlFor,
  orientation = "horizontal",
  className,
}: SettingRowProps) {
  const Label = htmlFor ? "label" : "div";
  return (
    <div
      className={cn(
        "flex gap-4 border-b py-4 first:pt-0 last:border-b-0 last:pb-0",
        orientation === "horizontal" ? "items-center justify-between" : "flex-col items-stretch",
        className,
      )}
    >
      <div className={cn("min-w-0", orientation === "horizontal" ? "max-w-[60%]" : undefined)}>
        <Label
          {...(htmlFor ? { htmlFor } : {})}
          className="block text-sm font-medium leading-tight"
        >
          {label}
        </Label>
        {description ? (
          <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{description}</p>
        ) : null}
      </div>
      <div
        className={cn(
          "shrink-0",
          orientation === "horizontal" ? "flex items-center justify-end" : "w-full",
        )}
      >
        {control}
      </div>
    </div>
  );
}

export function SettingSection({
  title,
  description,
  action,
  children,
  className,
}: {
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-xl border bg-card/30", className)}>
      {(title || description || action) && (
        <header className="flex items-start justify-between gap-3 border-b px-5 py-3">
          <div className="min-w-0">
            {title ? <h2 className="text-sm font-semibold">{title}</h2> : null}
            {description ? (
              <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
            ) : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </header>
      )}
      <div className="px-5 py-2">{children}</div>
    </section>
  );
}
