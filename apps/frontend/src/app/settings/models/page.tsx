import { Suspense } from "react";
import { SettingsShell } from "@/components/settings/settings-shell";

export default function SettingsModelsPage() {
  return (
    <Suspense fallback={null}>
      <SettingsShell defaultTab="models" />
    </Suspense>
  );
}
