"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/shared/i18n/use-language";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useI18n();
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-lg flex-col items-center justify-center gap-4 px-6 text-center">
      <h2 className="text-xl font-semibold">{t.pages.error.title}</h2>
      <p className="text-sm text-muted-foreground">
        {error.message || t.pages.error.unexpectedMessage}
      </p>
      <Button onClick={() => reset()}>{t.pages.error.tryAgain}</Button>
    </div>
  );
}
