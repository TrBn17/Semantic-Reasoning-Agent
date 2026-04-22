"use client";

import { memo, startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import type { SettingsModelOption } from "@/shared/api/types";
import { composeModelValue, parseModelValue } from "@/shared/utils/model-value";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function formatPresetLabel(preset: string) {
  return preset
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function summarizeKnowledgeScope(count: number) {
  if (count === 0) return "No knowledge packs";
  if (count === 1) return "1 knowledge pack";
  return `${count} knowledge packs`;
}

type TaskModelPickerProps = {
  models: SettingsModelOption[];
  value?: string;
  onChange: (value: string) => void;
  labels: {
    providerPlaceholder: string;
    allProviders: string;
    searchModelPlaceholder: string;
    selectModelPlaceholder: string;
    noModelMatch: string;
    assignmentUnavailable: string;
  };
};

export const TaskModelPicker = memo(function TaskModelPicker({
  models,
  value,
  onChange,
  labels,
}: TaskModelPickerProps) {
  const selected = useMemo(
    () => models.find((item) => composeModelValue(item.provider, item.model) === value),
    [models, value],
  );
  const providers = useMemo(
    () => Array.from(new Set(models.map((item) => item.provider))).sort((a, b) => a.localeCompare(b)),
    [models],
  );
  const [providerFilter, setProviderFilter] = useState<string>(selected?.provider ?? "all");
  const [searchText, setSearchText] = useState("");
  const deferredSearchText = useDeferredValue(searchText);

  useEffect(() => {
    const selectedValue = parseModelValue(value);
    setProviderFilter(selectedValue?.provider ?? "all");
  }, [value]);

  const filteredModels = useMemo(() => {
    const keyword = deferredSearchText.trim().toLowerCase();
    return models
      .filter((item) => {
        if (providerFilter !== "all" && item.provider !== providerFilter) {
          return false;
        }
        if (!keyword) {
          return true;
        }
        return (
          item.label.toLowerCase().includes(keyword) ||
          item.model.toLowerCase().includes(keyword) ||
          item.provider.toLowerCase().includes(keyword)
        );
      })
      .sort((a, b) => {
        if (a.ready !== b.ready) {
          return a.ready ? -1 : 1;
        }
        return a.label.localeCompare(b.label);
      });
  }, [deferredSearchText, models, providerFilter]);

  return (
    <div className="space-y-2">
      <div className="grid gap-2 md:grid-cols-[180px_minmax(0,1fr)]">
        <Select value={providerFilter} onValueChange={setProviderFilter}>
          <SelectTrigger>
            <SelectValue placeholder={labels.providerPlaceholder} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{labels.allProviders}</SelectItem>
            {providers.map((provider) => (
              <SelectItem key={provider} value={provider}>
                {provider}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          value={searchText}
          onChange={(event) =>
            startTransition(() => {
              setSearchText(event.target.value);
            })
          }
          placeholder={labels.searchModelPlaceholder}
        />
      </div>

      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={labels.selectModelPlaceholder} />
        </SelectTrigger>
        <SelectContent>
          {filteredModels.map((model) => (
            <SelectItem
              key={composeModelValue(model.provider, model.model)}
              value={composeModelValue(model.provider, model.model)}
            >
              {model.label} · {model.provider}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {filteredModels.length === 0 && (
        <p className="text-xs text-muted-foreground">
          {labels.noModelMatch}
        </p>
      )}
      {value && !selected && (
        <p className="text-xs text-amber-700">
          {labels.assignmentUnavailable}
        </p>
      )}
    </div>
  );
});
