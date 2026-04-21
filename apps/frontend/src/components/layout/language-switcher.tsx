"use client";

import { useI18n } from "@/shared/i18n/use-language";
import { Button } from "@/components/ui/button";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  return (
    <div className="flex items-center gap-1 rounded-full border bg-muted/40 p-1">
      <span className="px-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {t.languageLabel}
      </span>
      <Button
        type="button"
        size="sm"
        variant={language === "en" ? "default" : "ghost"}
        className="h-7 rounded-full px-3 text-xs"
        onClick={() => setLanguage("en")}
      >
        {t.languageOptions.english}
      </Button>
      <Button
        type="button"
        size="sm"
        variant={language === "vi" ? "default" : "ghost"}
        className="h-7 rounded-full px-3 text-xs"
        onClick={() => setLanguage("vi")}
      >
        {t.languageOptions.vietnamese}
      </Button>
    </div>
  );
}
