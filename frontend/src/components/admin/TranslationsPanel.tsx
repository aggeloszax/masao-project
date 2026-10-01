"use client";

import { useState } from "react";
import { LANGUAGES, isRtl, type Lang } from "@/i18n/config";
import {
  TRANSLATABLE_LANGUAGES,
  saveItemTranslation,
  translateItem,
  type AdminItem,
  type AdminTranslationValue,
} from "@/lib/admin-api";
import {
  BUTTON_GHOST,
  BUTTON_PRIMARY,
  INPUT_CLASS,
  LABEL_CLASS,
} from "@/components/admin/ui";

const LANGUAGE_LABELS = new Map(LANGUAGES.map((language) => [language.code, language.label]));

type Drafts = Record<string, AdminTranslationValue>;

function draftsFrom(item: AdminItem): Drafts {
  const drafts: Drafts = {};
  for (const code of TRANSLATABLE_LANGUAGES) {
    const stored = item.translations[code];
    drafts[code] = { name: stored?.name ?? "", description: stored?.description ?? "" };
  }
  return drafts;
}

export function TranslationsPanel({
  item,
  onItemChange,
  onError,
  onNotice,
}: {
  item: AdminItem;
  onItemChange: (item: AdminItem) => void;
  onError: (cause: unknown) => void;
  onNotice: (message: string) => void;
}) {
  const [drafts, setDrafts] = useState<Drafts>(() => draftsFrom(item));
  const [busyLanguage, setBusyLanguage] = useState<Lang | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);

  function updateDraft(code: Lang, patch: Partial<AdminTranslationValue>) {
    setDrafts((current) => ({ ...current, [code]: { ...current[code], ...patch } }));
  }

  async function saveLanguage(code: Lang) {
    const draft = drafts[code];
    if (!draft.name.trim()) {
      onNotice(`Συμπληρώστε όνομα για ${LANGUAGE_LABELS.get(code) ?? code}`);
      return;
    }

    setBusyLanguage(code);
    try {
      const value = { name: draft.name.trim(), description: draft.description.trim() };
      await saveItemTranslation(item.id, code, value);
      onItemChange({ ...item, translations: { ...item.translations, [code]: value } });
      onNotice(`Αποθηκεύτηκε: ${LANGUAGE_LABELS.get(code) ?? code}`);
    } catch (cause) {
      onError(cause);
    } finally {
      setBusyLanguage(null);
    }
  }

  async function runAutoTranslate(overwrite: boolean) {
    setIsTranslating(true);
    try {
      const result = await translateItem(item.id, { overwrite });
      if (result.translated.length === 0) {
        onNotice("Δεν έλειπε καμία μετάφραση.");
        return;
      }

      const merged = { ...item.translations, ...result.translations };
      onItemChange({ ...item, translations: merged });
      setDrafts(draftsFrom({ ...item, translations: merged }));
      onNotice(`Μεταφράστηκαν ${result.translated.length} γλώσσες: ${result.translated.join(", ")}`);
    } catch (cause) {
      onError(cause);
    } finally {
      setIsTranslating(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-hairline bg-surface p-4">
        <p className={LABEL_CLASS}>Βασική εγγραφή</p>
        <p className="mt-1.5 text-[15px] font-medium text-foreground">{item.name}</p>
        {item.description && <p className="mt-1 text-sm text-muted">{item.description}</p>}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => runAutoTranslate(false)}
          disabled={isTranslating}
          className={BUTTON_PRIMARY}
        >
          {isTranslating ? "Μετάφραση…" : "Αυτόματη μετάφραση όσων λείπουν"}
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Να αντικατασταθούν και οι υπάρχουσες μεταφράσεις;")) {
              void runAutoTranslate(true);
            }
          }}
          disabled={isTranslating}
          className={BUTTON_GHOST}
        >
          Ξαναμετάφραση όλων
        </button>
      </div>

      <ul className="space-y-3">
        {TRANSLATABLE_LANGUAGES.map((code) => {
          const draft = drafts[code];
          const isStored = code in item.translations;
          const rtl = isRtl(code);

          return (
            <li key={code} className="rounded-xl border border-hairline bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-foreground">
                  {LANGUAGE_LABELS.get(code) ?? code}
                  <span className="ml-2 text-xs font-normal uppercase text-muted">{code}</span>
                </h3>
                {!isStored && (
                  <span className="rounded-full border border-accent-soft/40 px-2 py-0.5 text-[11px] font-medium text-accent-soft">
                    λείπει
                  </span>
                )}
              </div>

              <div className="mt-3 space-y-2">
                <input
                  type="text"
                  value={draft.name}
                  onChange={(event) => updateDraft(code, { name: event.target.value })}
                  placeholder="Όνομα"
                  aria-label={`Όνομα (${code})`}
                  dir={rtl ? "rtl" : "ltr"}
                  className={INPUT_CLASS}
                />
                <textarea
                  value={draft.description}
                  onChange={(event) => updateDraft(code, { description: event.target.value })}
                  placeholder="Περιγραφή"
                  aria-label={`Περιγραφή (${code})`}
                  dir={rtl ? "rtl" : "ltr"}
                  rows={2}
                  className={`${INPUT_CLASS} resize-y`}
                />
              </div>

              <button
                type="button"
                onClick={() => saveLanguage(code)}
                disabled={busyLanguage === code || isTranslating}
                className={`${BUTTON_GHOST} mt-3`}
              >
                {busyLanguage === code ? "Αποθήκευση…" : "Αποθήκευση"}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
