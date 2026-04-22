"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ensureI18n } from "@/shared/i18n/config";
import { dictionaries, type Language } from "./dictionaries";

type LanguageState = {
  language: Language;
  setLanguage: (language: Language) => void;
  toggleLanguage: () => void;
};

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: "en",
      setLanguage: (language) => {
        set({ language });
        void ensureI18n().then((instance) => instance.changeLanguage(language));
      },
      toggleLanguage: () =>
        set((state) => {
          const next = state.language === "en" ? "vi" : "en";
          void ensureI18n().then((instance) => instance.changeLanguage(next));
          return { language: next };
        }),
    }),
    {
      name: "semantic-reasoning-language",
    },
  ),
);

export function useI18n() {
  const language = useLanguageStore((state) => state.language);
  const setLanguage = useLanguageStore((state) => state.setLanguage);
  const toggleLanguage = useLanguageStore((state) => state.toggleLanguage);

  return {
    language,
    setLanguage,
    toggleLanguage,
    t: dictionaries[language],
  };
}
