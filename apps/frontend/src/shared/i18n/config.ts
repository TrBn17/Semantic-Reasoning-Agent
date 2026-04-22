"use client";

import i18next from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import resourcesToBackend from "i18next-resources-to-backend";
import { initReactI18next } from "react-i18next";

let initialized = false;

export async function ensureI18n() {
  if (initialized || i18next.isInitialized) {
    initialized = true;
    return i18next;
  }

  await i18next
    .use(initReactI18next)
    .use(LanguageDetector)
    .use(
      resourcesToBackend((language: string, namespace: string) =>
        import(`../../../public/locales/${language}/${namespace}.json`),
      ),
    )
    .init({
      fallbackLng: "en",
      supportedLngs: ["en", "vi"],
      defaultNS: "common",
      ns: ["common", "nav"],
      interpolation: { escapeValue: false },
      react: { useSuspense: false },
      detection: {
        order: ["localStorage", "navigator"],
        caches: ["localStorage"],
      },
      returnNull: false,
    });

  initialized = true;
  return i18next;
}

export { i18next };
