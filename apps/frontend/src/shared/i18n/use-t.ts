"use client";

import { useTranslation } from "react-i18next";

export function useT(ns: string | string[] = "common") {
  const { t, i18n } = useTranslation(ns);
  return {
    t,
    lang: (i18n.language?.startsWith("vi") ? "vi" : "en") as "en" | "vi",
    setLang: (language: "en" | "vi") => i18n.changeLanguage(language),
  };
}
