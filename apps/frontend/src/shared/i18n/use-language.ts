"use client";

import { create } from "zustand";
import { dictionaries, type Language } from "./dictionaries";
import { getBrowserLanguage, syncBrowserLanguage } from "./locale";

type LanguageState = {
  language: Language;
  setLanguage: (language: Language) => void;
  toggleLanguage: () => void;
};

export const useLanguageStore = create<LanguageState>()(
  (set, get) => ({
    language: getBrowserLanguage(),
    setLanguage: (language) => {
      syncBrowserLanguage(language);
      set({ language });
    },
    toggleLanguage: () => {
      const nextLanguage = get().language === "en" ? "vi" : "en";
      syncBrowserLanguage(nextLanguage);
      set({ language: nextLanguage });
    },
  }),
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
