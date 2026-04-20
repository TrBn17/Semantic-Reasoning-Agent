export type SupportedLanguage = "en" | "vi";

export const DEFAULT_LANGUAGE: SupportedLanguage = "en";
export const LOCALE_COOKIE_NAME = "semantic-reasoning-language";

export function normalizeLanguage(value: string | null | undefined): SupportedLanguage {
  return value === "vi" ? "vi" : "en";
}

export function getBrowserLanguage(): SupportedLanguage {
  if (typeof document !== "undefined") {
    const htmlLanguage = document.documentElement.lang?.trim();
    if (htmlLanguage) {
      return normalizeLanguage(htmlLanguage);
    }
  }

  if (typeof localStorage !== "undefined") {
    return normalizeLanguage(localStorage.getItem(LOCALE_COOKIE_NAME));
  }

  return DEFAULT_LANGUAGE;
}

export function syncBrowserLanguage(language: SupportedLanguage) {
  if (typeof document !== "undefined") {
    document.documentElement.lang = language;
    document.cookie = `${LOCALE_COOKIE_NAME}=${language}; path=/; max-age=31536000; samesite=lax`;
  }

  if (typeof localStorage !== "undefined") {
    localStorage.setItem(LOCALE_COOKIE_NAME, language);
  }
}
