"use client";

import { BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import type { Citation } from "@/shared/api/types";
import { useI18n } from "@/shared/i18n/use-language";

export function CitationsDrawer({ citations }: { citations: Citation[] }) {
  const { t } = useI18n();
  if (!citations || citations.length === 0) return null;

  const suffix = citations.length === 1 ? "" : "s";
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          <BookOpen className="h-4 w-4" />
          {t.citationsDrawer.citationCount
            .replace("{count}", citations.length.toString())
            .replace("{suffix}", suffix)}
        </Button>
      </SheetTrigger>
      <SheetContent
        className="w-[480px] sm:max-w-[480px]"
        closeLabel={t.common.accessibility.closeSheet}
      >
        <SheetHeader>
          <SheetTitle>{t.citationsDrawer.title}</SheetTitle>
          <SheetDescription>{t.citationsDrawer.description}</SheetDescription>
        </SheetHeader>
        <ScrollArea className="mt-4 h-[calc(100vh-120px)] pr-3">
          <div className="space-y-3">
            {citations.map((c) => (
              <div key={c.chunk_id} className="rounded-md border bg-card p-3 text-sm shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{c.document_title}</span>
                  <Badge variant="outline" className="uppercase">
                    {c.document_type}
                  </Badge>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">{c.location_label}</div>
                <p className="mt-2 whitespace-pre-wrap text-sm">{c.excerpt}</p>
              </div>
            ))}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
