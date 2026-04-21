"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listTools } from "@/shared/api/tools";
import type { RiskLevel, ToolSpec } from "@/shared/api/types";
import { queryKeys } from "@/shared/query/keys";
import { ToolInvokeDialog } from "@/components/tools/tool-invoke-dialog";

export function ToolsTable() {
  const [familyFilter, setFamilyFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.tools.list(),
    queryFn: () => listTools(),
  });

  const rows = useMemo(() => {
    return (data ?? []).filter((tool) => {
      if (familyFilter !== "all" && tool.tool_family !== familyFilter) return false;
      if (riskFilter !== "all" && tool.risk_level !== riskFilter) return false;
      if (!search.trim()) return true;
      const haystack = [
        tool.tool_name,
        tool.tool_family,
        tool.description,
        tool.capabilities.join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(search.trim().toLowerCase());
    });
  }, [data, familyFilter, riskFilter, search]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError) {
    return (
      <p className="text-sm text-destructive">
        Failed to load tools: {(error as Error)?.message ?? "unknown error"}.
      </p>
    );
  }

  const families = Array.from(new Set((data ?? []).map((tool) => tool.tool_family))).sort();

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search tools, families, or capabilities"
          className="max-w-sm"
        />
        <FilterChips value={familyFilter} onChange={setFamilyFilter} options={["all", ...families]} />
        <FilterChips value={riskFilter} onChange={setRiskFilter} options={["all", "low", "medium", "high"]} />
      </div>

      {rows.length === 0 ? (
        <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
          No tools matched the current filters.
        </p>
      ) : (
        <div className="rounded-2xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tool</TableHead>
                <TableHead>Family</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Runtime traits</TableHead>
                <TableHead>Capabilities</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((tool) => (
                <ToolRow key={tool.tool_name} tool={tool} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function FilterChips({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <Button
          key={option}
          type="button"
          variant={value === option ? "secondary" : "outline"}
          size="sm"
          onClick={() => onChange(option)}
        >
          {option}
        </Button>
      ))}
    </div>
  );
}

function ToolRow({ tool }: { tool: ToolSpec }) {
  return (
    <TableRow>
      <TableCell>
        <div className="font-mono text-sm font-medium">{tool.tool_name}</div>
        <div className="text-xs text-muted-foreground">{tool.description}</div>
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
        <div>{tool.supports_streaming ? "Streaming" : "Buffered"}</div>
        <div>{tool.side_effect_level.replace("_", " ")}</div>
        <div>{(tool.timeout_ms / 1000).toFixed(1)}s timeout</div>
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        <div className="flex flex-wrap gap-1">
          {tool.capabilities.length === 0 ? (
            <span className="italic">none</span>
          ) : (
            tool.capabilities.map((capability) => (
              <span
                key={capability}
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]"
              >
                {capability}
              </span>
            ))
          )}
        </div>
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
