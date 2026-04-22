"use client";

import { memo, useDeferredValue, useEffect, useMemo, useState } from "react";
import { Command } from "cmdk";
import { Check, ChevronDown, ChevronUp, Cpu, Radio } from "lucide-react";
import type { SettingsModelOption } from "@/shared/api/types";
import { composeModelValue } from "@/shared/utils/model-value";
import { rankItems } from "@/shared/utils/fuzzy";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/shared/utils";

type ModelComboboxProps = {
  models: SettingsModelOption[];
  value?: string;
  onChange: (value: string) => void;
  onlyReady?: boolean;
  collapseOnSelect?: boolean;
  labels?: {
    providerPlaceholder?: string;
    allProviders?: string;
    searchModelPlaceholder?: string;
    selectModelPlaceholder?: string;
    noModelMatch?: string;
    assignmentUnavailable?: string;
    readyBadge?: string;
    blockedBadge?: string;
    capabilityStreaming?: string;
    capabilityStructured?: string;
  };
};

type RankedModel = {
  item: SettingsModelOption;
  score: number;
};

export const ModelCombobox = memo(function ModelCombobox({
  models,
  value,
  onChange,
  onlyReady = false,
  collapseOnSelect = false,
  labels,
}: ModelComboboxProps) {
  const selected = useMemo(
    () => models.find((item) => composeModelValue(item.provider, item.model) === value),
    [models, value],
  );
  const providers = useMemo(
    () => Array.from(new Set(models.map((item) => item.provider))).sort((a, b) => a.localeCompare(b)),
    [models],
  );
  const [providerFilter, setProviderFilter] = useState<string>("all");
  const [searchText, setSearchText] = useState("");
  const [modelsOpen, setModelsOpen] = useState(!collapseOnSelect);
  const deferredSearchText = useDeferredValue(searchText);

  useEffect(() => {
    if (collapseOnSelect && value) {
      setModelsOpen(false);
    }
  }, [collapseOnSelect, value]);

  const filteredModels = useMemo(() => {
    const scoped = models.filter((model) => {
      if (onlyReady && !model.ready) return false;
      if (providerFilter !== "all" && model.provider !== providerFilter) return false;
      return true;
    });
    const ranked: RankedModel[] = deferredSearchText.trim()
      ? rankItems(scoped, deferredSearchText, (item) => [
          item.label,
          item.model,
          item.provider,
          item.reason,
          item.context_window ? `${Math.round(item.context_window / 1000)}k` : "",
        ]).map(({ item, score }) => ({ item, score }))
      : scoped.map((item) => ({ item, score: 0 }));
    ranked.sort((a, b) => {
      if (a.item.ready !== b.item.ready) return a.item.ready ? -1 : 1;
      if (a.score !== b.score) return b.score - a.score;
      return a.item.label.localeCompare(b.item.label);
    });
    return ranked;
  }, [deferredSearchText, models, onlyReady, providerFilter]);

  return (
    <div className="min-w-0 space-y-2">
      <div className="grid gap-2 md:grid-cols-[180px_minmax(0,1fr)]">
        <Select value={providerFilter} onValueChange={setProviderFilter}>
          <SelectTrigger>
            <SelectValue placeholder={labels?.providerPlaceholder ?? "Provider"} />
          </SelectTrigger>
          <SelectContent className="max-h-64 max-w-[min(90vw,20rem)]">
            <SelectItem value="all">{labels?.allProviders ?? "All providers"}</SelectItem>
            {providers.map((provider) => (
              <SelectItem key={provider} value={provider}>
                {provider}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Command className="rounded-md border">
          <Command.Input
            value={searchText}
            onValueChange={setSearchText}
            placeholder={labels?.searchModelPlaceholder ?? "Search model"}
            className="h-9 w-full border-0 bg-transparent px-3 text-sm outline-none"
          />
        </Command>
      </div>

      <Command className="max-w-full min-w-0 overflow-hidden rounded-md border">
        <button
          type="button"
          className="flex w-full min-w-0 items-center justify-between gap-2 border-b px-3 py-2 text-left text-xs text-muted-foreground"
          onClick={() => setModelsOpen((open) => !open)}
        >
          <span className="truncate">
            {selected
              ? `${labels?.selectModelPlaceholder ?? "Select model"}: ${selected.label}`
              : labels?.selectModelPlaceholder ?? "Select model"}
          </span>
          {modelsOpen ? (
            <ChevronUp className="h-3.5 w-3.5 shrink-0" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 shrink-0" />
          )}
        </button>
        <Command.List className={cn("w-full max-h-56 overflow-x-hidden overflow-y-auto p-1", !modelsOpen && "hidden")}>
          {filteredModels.map(({ item }) => {
            const itemValue = composeModelValue(item.provider, item.model);
            const isSelected = itemValue === value;
            return (
              <Command.Item
                key={itemValue}
                value={`${item.provider} ${item.model} ${item.label} ${item.reason ?? ""}`}
                onSelect={() => {
                  onChange(itemValue);
                  if (collapseOnSelect) setModelsOpen(false);
                }}
                className={cn(
                  "w-full max-w-full cursor-pointer overflow-hidden rounded-md px-2 py-1.5 text-sm aria-selected:bg-muted",
                  isSelected ? "bg-muted" : "",
                )}
              >
                <div className="flex w-full items-start gap-2">
                  <div className="pt-0.5">
                    {isSelected ? <Check className="h-3.5 w-3.5 text-primary" /> : null}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="truncate">{item.label}</span>
                      <Badge variant="outline" className="text-[10px]">
                        {item.provider}
                      </Badge>
                      {item.context_window ? (
                        <Badge variant="outline" className="text-[10px]">
                          {Math.round(item.context_window / 1000)}k ctx
                        </Badge>
                      ) : null}
                      <Badge variant={item.ready ? "success" : "warning"} className="text-[10px]">
                        {item.ready
                          ? labels?.readyBadge ?? "ready"
                          : labels?.blockedBadge ?? "blocked"}
                      </Badge>
                    </div>
                    <p className="truncate text-xs text-muted-foreground">
                      <span className="inline-block max-w-full truncate align-bottom font-mono">{item.model}</span>
                      {item.reason ? ` · ${item.reason}` : ""}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-1.5">
                      <Badge variant={item.supports_streaming ? "info" : "outline"} className="text-[10px]">
                        <Radio className="mr-1 h-3 w-3" />
                        {labels?.capabilityStreaming ?? "streaming"}
                      </Badge>
                      <Badge
                        variant={item.supports_structured_output ? "info" : "outline"}
                        className="text-[10px]"
                      >
                        <Cpu className="mr-1 h-3 w-3" />
                        {labels?.capabilityStructured ?? "structured"}
                      </Badge>
                    </div>
                  </div>
                </div>
              </Command.Item>
            );
          })}
        </Command.List>
      </Command>

      {filteredModels.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          {labels?.noModelMatch ?? "No model matched the current filter."}
        </p>
      ) : null}
      {value && !selected ? (
        <p className="text-xs text-amber-700">
          {labels?.assignmentUnavailable ?? "Current assignment is no longer available in the catalog."}
        </p>
      ) : null}
    </div>
  );
});
