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

export function ToolsTable() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.tools.list(),
    queryFn: () => listTools(),
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return (
      <p className="text-sm text-destructive">
        Failed to load tools: {(error as Error)?.message ?? "unknown error"}.
      </p>
    );
  if (!data || data.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No tools registered yet.
      </p>
    );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Tool</TableHead>
            <TableHead>Family</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead>Capabilities</TableHead>
            <TableHead className="text-right">Timeout</TableHead>
            <TableHead className="text-right">Action</TableHead>
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
  return (
    <TableRow>
      <TableCell>
        <div className="font-medium font-mono text-sm">{tool.tool_name}</div>
        <div className="text-xs text-muted-foreground">{tool.description}</div>
        <div className="mt-1 flex gap-1 text-[10px] text-muted-foreground">
          <span className="uppercase">{tool.tool_type.replace("_", " ")}</span>
          <span>·</span>
          <span>v{tool.version}</span>
          <span>·</span>
          <span>{tool.side_effect_level.replace("_", " ")}</span>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant="outline" className="font-mono text-xs">
          {tool.tool_family}
        </Badge>
      </TableCell>
      <TableCell>
        <RiskBadge level={tool.risk_level} />
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {tool.capabilities.length === 0 ? (
          <span className="italic">none</span>
        ) : (
          <div className="flex flex-wrap gap-1">
            {tool.capabilities.map((cap) => (
              <span
                key={cap}
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]"
              >
                {cap}
              </span>
            ))}
          </div>
        )}
      </TableCell>
      <TableCell className="text-right font-mono text-xs">
        {(tool.timeout_ms / 1000).toFixed(1)}s
      </TableCell>
      <TableCell className="text-right">
        <ToolInvokeDialog tool={tool} />
      </TableCell>
    </TableRow>
  );
}

function RiskBadge({ level }: { level: RiskLevel }) {
  const variant = level === "high" ? "destructive" : level === "medium" ? "warning" : "success";
  return (
    <Badge variant={variant} className="capitalize">
      {level}
    </Badge>
  );
}
