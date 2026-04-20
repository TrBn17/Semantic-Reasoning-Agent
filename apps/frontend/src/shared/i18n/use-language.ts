"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
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
      setLanguage: (language) => set({ language }),
      toggleLanguage: () =>
        set((state) => ({ language: state.language === "en" ? "vi" : "en" })),
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
