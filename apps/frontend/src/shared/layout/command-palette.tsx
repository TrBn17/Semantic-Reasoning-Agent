"use client";

import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useI18n } from "@/shared/i18n/use-language";

type CommandItem = {
  id: string;
  label: string;
  href: string;
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { t } = useI18n();

  const items = useMemo<CommandItem[]>(
    () => [
      { id: "home", label: t.nav.home, href: "/" },
      { id: "ask", label: t.nav.ask, href: "/ask" },
      { id: "documents", label: t.nav.documents, href: "/documents" },
      { id: "ontology", label: t.nav.ontology, href: "/ontology/builds" },
      { id: "graph", label: t.nav.graph, href: "/graph" },
      { id: "agents", label: t.nav.agents, href: "/agents" },
      { id: "settings", label: t.nav.settings, href: "/settings" },
    ],
    [t],
  );

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="overflow-hidden p-0 sm:max-w-xl">
        <Command className="rounded-lg border shadow-md">
          <Command.Input
            className="h-11 w-full border-b px-3 text-sm outline-none"
            placeholder={t.commandPalette.inputPlaceholder}
          />
          <Command.List className="max-h-[320px] overflow-y-auto p-2">
            <Command.Empty className="px-2 py-3 text-sm text-muted-foreground">
              {t.commandPalette.noResults}
            </Command.Empty>
            <Command.Group heading={t.commandPalette.navigationHeading} className="text-xs text-muted-foreground">
              {items.map((item) => (
                <Command.Item
                  key={item.id}
                  className="cursor-pointer rounded-md px-2 py-2 text-sm aria-selected:bg-accent"
                  onSelect={() => {
                    setOpen(false);
                    router.push(item.href);
                  }}
                >
                  {item.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
