"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react";
import { DEFAULT_LANG, isRtl, LANGUAGES, UI, type Lang } from "./config";

const STORAGE_KEY = "masao-lang";
const LANGUAGE_CHANGE_EVENT = "masao-language-change";

type LanguageContextValue = {
  lang: Lang;
  rtl: boolean;
  setLang: (lang: Lang) => void;
  t: (typeof UI)[Lang];
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(subscribeToLanguage, getStoredLanguage, getServerLanguage);

  // Keep <html lang/dir> in sync for correct page-level RTL (scrollbars, etc.).
  useEffect(() => {
    const root = document.documentElement;
    root.lang = lang;
    root.dir = isRtl(lang) ? "rtl" : "ltr";
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    window.localStorage.setItem(STORAGE_KEY, next);
    window.dispatchEvent(new Event(LANGUAGE_CHANGE_EVENT));
  }, []);

  const value = useMemo<LanguageContextValue>(
    () => ({ lang, rtl: isRtl(lang), setLang, t: UI[lang] }),
    [lang, setLang],
  );

  return (
    <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return ctx;
}

function subscribeToLanguage(callback: () => void): () => void {
  window.addEventListener("storage", callback);
  window.addEventListener(LANGUAGE_CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(LANGUAGE_CHANGE_EVENT, callback);
  };
}

function getStoredLanguage(): Lang {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isSupportedLanguage(stored) ? stored : DEFAULT_LANG;
}

function getServerLanguage(): Lang {
  return DEFAULT_LANG;
}

function isSupportedLanguage(value: string | null): value is Lang {
  return LANGUAGES.some((language) => language.code === value);
}
