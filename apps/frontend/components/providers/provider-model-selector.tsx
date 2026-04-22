"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchProviderModels } from "@/lib/api/providers";
import { queryKeys } from "@/lib/query/keys";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, AlertCircle } from "lucide-react";
import { useI18n } from "@/src/shared/i18n/use-language";

interface ProviderModelSelectorProps {
  provider: string;
  onModelSelect: (modelId: string) => void;
  selectedModel?: string;
  workspaceId?: string | null;
}

/**
 * Dynamic model selector that fetches available models from a provider
 * Shows both hardcoded defaults and live models from provider API
 */
export function ProviderModelSelector({
  provider,
  onModelSelect,
  selectedModel,
  workspaceId,
}: ProviderModelSelectorProps) {
  const { t } = useI18n();
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.providers.models(provider, workspaceId),
    queryFn: () => fetchProviderModels(provider, workspaceId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  const models = data?.models ?? [];

  if (error) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
        <div className="flex items-start gap-2">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">{t.providerModelSelector.loadFailedTitle}</p>
            <p className="text-xs text-amber-700">
              {error instanceof Error ? error.message : t.providerModelSelector.unknownError}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        {t.providerModelSelector.loadingModels}
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        {t.providerModelSelector.noModelsForProvider}
      </div>
    );
  }

  return (
    <Select value={selectedModel} onValueChange={onModelSelect}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={t.providerModelSelector.selectModelPlaceholder} />
      </SelectTrigger>
      <SelectContent className="max-w-md">
        {models.map((model) => (
          <SelectItem key={model.id} value={model.id}>
            <div className="flex items-center gap-2">
              <div>
                <div className="font-medium">{model.name || model.id}</div>
                <div className="text-xs text-muted-foreground">
                  {model.context_window
                    ? `${(model.context_window / 1000).toFixed(0)}K context`
                    : t.providerModelSelector.contextUnknown}
                  {model.supports_streaming && ` • ${t.providerModelSelector.streaming}`}
                  {model.supports_structured_output && ` • ${t.providerModelSelector.structured}`}
                </div>
              </div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

interface ProviderModelComparisonProps {
  providers: string[];
  onModelSelect: (provider: string, modelId: string) => void;
}

/**
 * Side-by-side comparison of models from multiple providers
 */
export function ProviderModelComparison({
  providers,
  onModelSelect,
}: ProviderModelComparisonProps) {
  return (
    <Tabs defaultValue={providers[0]} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        {providers.map((provider) => (
          <TabsTrigger key={provider} value={provider} className="capitalize">
            {provider}
          </TabsTrigger>
        ))}
      </TabsList>

      {providers.map((provider) => (
        <TabsContent key={provider} value={provider}>
          <ProviderModelSelector
            provider={provider}
            onModelSelect={(modelId) => onModelSelect(provider, modelId)}
          />
        </TabsContent>
      ))}
    </Tabs>
  );
}

/**
 * Inline model loader showing latest models from provider
 */
export function ProviderModelsPreview({
  provider,
  workspaceId,
}: {
  provider: string;
  workspaceId?: string | null;
}) {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.providers.models(provider, workspaceId),
    queryFn: () => fetchProviderModels(provider, workspaceId),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const models = data?.models ?? [];

  if (isLoading) {
    return <span className="text-xs text-muted-foreground">{t.providerModelSelector.loading}</span>;
  }

  if (!models.length) {
    return (
      <span className="text-xs text-muted-foreground">{t.providerModelSelector.noModels}</span>
    );
  }

  return (
    <div className="space-y-2">
      {models.slice(0, 5).map((model) => (
        <div key={model.id} className="text-xs">
          <Badge variant="outline" className="mr-2">
            {model.name || model.id}
          </Badge>
          {model.context_window && (
            <span className="text-muted-foreground">
              {(model.context_window / 1000).toFixed(0)}K
            </span>
          )}
        </div>
      ))}
      {models.length > 5 && (
        <div className="text-xs text-muted-foreground">
          +{models.length - 5} {t.providerModelSelector.moreModelsSuffix}
        </div>
      )}
    </div>
  );
}
