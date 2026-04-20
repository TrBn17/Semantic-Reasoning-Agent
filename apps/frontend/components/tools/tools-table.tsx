"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listTools } from "@/lib/api/tools";
import type { RiskLevel, ToolSpec } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

import { ToolInvokeDialog } from "@/components/tools/tool-invoke-dialog";
import { useI18n } from "@/src/shared/i18n/use-language";

export function ToolsTable() {
  const { t } = useI18n();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.tools.list(),
    queryFn: () => listTools(),
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return (
      <p className="text-sm text-destructive">
        {t.tools.loadFailedPrefix} {(error as Error)?.message ?? t.common.unknown}.
      </p>
    );
  if (!data || data.length === 0)
    return (
      <p className="surface-panel border-dashed p-6 text-center text-sm text-muted-foreground">
        {t.tools.empty}
      </p>
    );

  return (
    <div className="surface-panel overflow-hidden">
      <Table>
        <TableHeader className="bg-muted/30">
          <TableRow>
            <TableHead className="pl-4">{t.tools.table.tool}</TableHead>
            <TableHead>{t.tools.table.family}</TableHead>
            <TableHead>{t.tools.table.risk}</TableHead>
            <TableHead>{t.tools.table.capabilities}</TableHead>
            <TableHead className="text-right">{t.tools.table.timeout}</TableHead>
            <TableHead className="pr-4 text-right">{t.tools.table.action}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((tool) => (
            <ToolRow key={tool.tool_name} tool={tool} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ToolRow({ tool }: { tool: ToolSpec }) {
  const { t } = useI18n();

  return (
    <TableRow className="transition-colors hover:bg-accent/40">
      <TableCell className="pl-4 align-top">
        <div className="font-mono text-sm font-semibold text-foreground">{tool.tool_name}</div>
        <div className="max-w-xl text-xs leading-5 text-muted-foreground">{tool.description}</div>
        <div className="mt-1 flex flex-wrap gap-1 text-[10px] text-muted-foreground">
          <span className="uppercase">{tool.tool_type.replace("_", " ")}</span>
          <span>·</span>
          <span>v{tool.version}</span>
          <span>·</span>
          <span>{tool.side_effect_level.replace("_", " ")}</span>
        </div>
      </TableCell>
      <TableCell className="align-top">
        <Badge variant="outline" className="rounded-full font-mono text-xs">
          {tool.tool_family}
        </Badge>
      </TableCell>
      <TableCell className="align-top">
        <RiskBadge level={tool.risk_level} />
      </TableCell>
      <TableCell className="align-top text-xs text-muted-foreground">
        {tool.capabilities.length === 0 ? (
          <span className="italic">{t.common.none}</span>
        ) : (
          <div className="flex flex-wrap gap-1">
            {tool.capabilities.map((cap) => (
              <span
                key={cap}
                className="rounded-full bg-muted px-2 py-0.5 font-mono text-[10px]"
              >
                {cap}
              </span>
            ))}
          </div>
        )}
      </TableCell>
      <TableCell className="align-top text-right font-mono text-xs text-muted-foreground">
        {(tool.timeout_ms / 1000).toFixed(1)}s
      </TableCell>
      <TableCell className="align-top pr-4 text-right">
        <ToolInvokeDialog tool={tool} />
      </TableCell>
    </TableRow>
  );
}

function RiskBadge({ level }: { level: RiskLevel }) {
  const { t } = useI18n();
  const variant = level === "high" ? "destructive" : level === "medium" ? "warning" : "success";
  const label = level === "high" ? t.tools.risk.high : level === "medium" ? t.tools.risk.medium : t.tools.risk.low;
  return (
    <Badge variant={variant} className="capitalize">
      {label}
    </Badge>
  );
}
