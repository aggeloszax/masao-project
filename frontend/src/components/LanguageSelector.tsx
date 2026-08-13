"use client";

import "flag-icons/css/flag-icons.min.css";
import { useEffect, useRef, useState } from "react";
import { LANGUAGES } from "@/i18n/config";
import { useLanguage } from "@/i18n/LanguageContext";

export function LanguageSelector() {
  const { lang, setLang, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = LANGUAGES.find((l) => l.code === lang) ?? LANGUAGES[0];

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t.selectLanguage}
        className="flex items-center gap-1.5 rounded-full border border-hairline bg-surface px-3 py-1.5 text-sm text-foreground transition-colors hover:border-accent"
      >
        <span className={`fi fi-${current.flagCode} rounded-[2px]`} aria-hidden />
        <span className="font-medium uppercase">{current.code}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute end-0 z-50 mt-2 min-w-44 overflow-hidden rounded-xl border border-hairline bg-background py-1 shadow-xl"
        >
          {LANGUAGES.map((l) => {
            const active = l.code === lang;
            return (
              <li key={l.code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => {
                    setLang(l.code);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm transition-colors hover:bg-surface ${
                    active ? "text-accent" : "text-foreground"
                  }`}
                >
                  <span className={`fi fi-${l.flagCode} rounded-[2px]`} aria-hidden />
                  <span className="font-medium">{l.label}</span>
                  {active && (
                    <span className="ms-auto text-accent" aria-hidden>
                      ✓
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
