"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { LANGUAGES, isRtl, type Lang } from "@/i18n/config";
import {
  TRANSLATABLE_LANGUAGES,
  createCategory,
  deleteCategory,
  describeAdminError,
  isSessionExpired,
  listCategories,
  reorderCategories,
  saveCategoryTranslation,
  translateCategory,
  updateCategory,
  type AdminCategory,
} from "@/lib/admin-api";
import {
  BUTTON_GHOST,
  BUTTON_PRIMARY,
  Banner,
  EmptyState,
  Field,
  INPUT_CLASS,
  LoadingState,
} from "@/components/admin/ui";

const LANGUAGE_LABELS = new Map(LANGUAGES.map((language) => [language.code, language.label]));

export function CategoriesBoard() {
  const router = useRouter();
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleFailure = useCallback(
    (cause: unknown) => {
      if (isSessionExpired(cause)) {
        router.replace("/admin/login");
        return;
      }
      setError(describeAdminError(cause));
    },
    [router],
  );

  // Το state ενημερώνεται μέσα στα callbacks του promise, ποτέ σύγχρονα μέσα
  // στο effect.
  useEffect(() => {
    let isCurrent = true;
    listCategories()
      .then((nextCategories) => {
        if (!isCurrent) return;
        setCategories(nextCategories);
        setError(null);
      })
      .catch((cause) => {
        if (isCurrent) handleFailure(cause);
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [handleFailure]);

  /** Imperative refresh after a mutation that reshuffles the whole list. */
  const load = useCallback(async () => {
    try {
      setCategories(await listCategories());
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    }
  }, [handleFailure]);

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= categories.length) return;

    const ids = categories.map((category) => category.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];

    setBusyId(categories[index].id);
    try {
      await reorderCategories(ids);
      await load();
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function rename(category: AdminCategory, name: string) {
    const trimmed = name.trim();
    if (!trimmed || trimmed === category.name) return;

    setBusyId(category.id);
    try {
      await updateCategory(category.id, { name: trimmed });
      setCategories((current) =>
        current.map((row) => (row.id === category.id ? { ...row, name: trimmed } : row)),
      );
      setNotice(`Η κατηγορία μετονομάστηκε σε «${trimmed}»`);
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function remove(category: AdminCategory) {
    if (category.item_count > 0) {
      setError(
        `Η «${category.name}» έχει ${category.item_count} πιάτα. Μετακινήστε ή διαγράψτε τα πρώτα.`,
      );
      return;
    }
    if (!window.confirm(`Διαγραφή της κατηγορίας «${category.name}»;`)) return;

    setBusyId(category.id);
    try {
      await deleteCategory(category.id);
      setCategories((current) => current.filter((row) => row.id !== category.id));
      setNotice(`Η κατηγορία «${category.name}» διαγράφηκε`);
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;

    setIsCreating(true);
    try {
      await createCategory({
        name,
        slug: newSlug.trim() || null,
        // Νέα κατηγορία στο τέλος της λίστας.
        display_order: categories.length,
      });
      setNewName("");
      setNewSlug("");
      setNotice(`Η κατηγορία «${name}» δημιουργήθηκε`);
      setError(null);
      await load();
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">Κατηγορίες</h1>

      {error && <Banner kind="error" message={error} onDismiss={() => setError(null)} />}
      {notice && <Banner kind="success" message={notice} onDismiss={() => setNotice(null)} />}

      <form
        onSubmit={handleCreate}
        className="grid gap-3 rounded-xl border border-hairline bg-white p-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
      >
        <Field label="Νέα κατηγορία">
          <input
            type="text"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="π.χ. Ορεκτικά"
            maxLength={120}
            className={INPUT_CLASS}
          />
        </Field>
        <Field label="Slug" hint="Προαιρετικό, σταθερό αναγνωριστικό για το frontend">
          <input
            type="text"
            value={newSlug}
            onChange={(event) => setNewSlug(event.target.value)}
            placeholder="π.χ. starters"
            maxLength={160}
            className={INPUT_CLASS}
          />
        </Field>
        <button type="submit" disabled={isCreating || !newName.trim()} className={BUTTON_PRIMARY}>
          {isCreating ? "Δημιουργία…" : "Προσθήκη"}
        </button>
      </form>

      {isLoading ? (
        <LoadingState />
      ) : categories.length === 0 ? (
        <EmptyState message="Δεν υπάρχουν κατηγορίες ακόμη." />
      ) : (
        <ul className="space-y-2">
          {categories.map((category, index) => (
            <CategoryRow
              key={category.id}
              category={category}
              isBusy={busyId === category.id}
              isFirst={index === 0}
              isLast={index === categories.length - 1}
              isExpanded={expandedId === category.id}
              onToggleExpanded={() =>
                setExpandedId((current) => (current === category.id ? null : category.id))
              }
              onRename={(name) => rename(category, name)}
              onMoveUp={() => move(index, -1)}
              onMoveDown={() => move(index, 1)}
              onDelete={() => remove(category)}
              onCategoryChange={(updated) =>
                setCategories((current) =>
                  current.map((row) => (row.id === updated.id ? updated : row)),
                )
              }
              onError={handleFailure}
              onNotice={setNotice}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function CategoryRow({
  category,
  isBusy,
  isFirst,
  isLast,
  isExpanded,
  onToggleExpanded,
  onRename,
  onMoveUp,
  onMoveDown,
  onDelete,
  onCategoryChange,
  onError,
  onNotice,
}: {
  category: AdminCategory;
  isBusy: boolean;
  isFirst: boolean;
  isLast: boolean;
  isExpanded: boolean;
  onToggleExpanded: () => void;
  onRename: (name: string) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
  onCategoryChange: (category: AdminCategory) => void;
  onError: (cause: unknown) => void;
  onNotice: (message: string) => void;
}) {
  const [name, setName] = useState(category.name);

  return (
    <li className={`rounded-xl border border-hairline bg-white ${isBusy ? "opacity-60" : ""}`}>
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          onBlur={() => onRename(name)}
          onKeyDown={(event) => {
            if (event.key === "Enter") event.currentTarget.blur();
            if (event.key === "Escape") setName(category.name);
          }}
          aria-label={`Όνομα κατηγορίας ${category.name}`}
          className="min-w-0 flex-1 rounded border border-transparent px-2 py-1 text-[15px] font-medium text-foreground outline-none transition-colors hover:border-hairline focus:border-accent"
        />

        <span className="shrink-0 text-xs text-muted">{category.item_count} πιάτα</span>

        <div className="flex shrink-0 items-center gap-1">
          <SmallButton label="Μετακίνηση πάνω" disabled={isBusy || isFirst} onClick={onMoveUp}>
            ↑
          </SmallButton>
          <SmallButton label="Μετακίνηση κάτω" disabled={isBusy || isLast} onClick={onMoveDown}>
            ↓
          </SmallButton>
          <button
            type="button"
            onClick={onToggleExpanded}
            aria-expanded={isExpanded}
            className="rounded-lg border border-hairline px-2.5 py-1.5 text-xs font-medium text-muted transition-colors hover:border-accent hover:text-accent"
          >
            Μεταφράσεις {isExpanded ? "▴" : "▾"}
          </button>
          <SmallButton label="Διαγραφή κατηγορίας" disabled={isBusy} onClick={onDelete} danger>
            ✕
          </SmallButton>
        </div>
      </div>

      {isExpanded && (
        <CategoryTranslations
          category={category}
          onCategoryChange={onCategoryChange}
          onError={onError}
          onNotice={onNotice}
        />
      )}
    </li>
  );
}

function CategoryTranslations({
  category,
  onCategoryChange,
  onError,
  onNotice,
}: {
  category: AdminCategory;
  onCategoryChange: (category: AdminCategory) => void;
  onError: (cause: unknown) => void;
  onNotice: (message: string) => void;
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      TRANSLATABLE_LANGUAGES.map((code) => [code, category.translations[code] ?? ""]),
    ),
  );
  const [busyLanguage, setBusyLanguage] = useState<Lang | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);

  async function save(code: Lang) {
    const value = drafts[code].trim();
    if (!value) return;

    setBusyLanguage(code);
    try {
      await saveCategoryTranslation(category.id, code, value);
      onCategoryChange({
        ...category,
        translations: { ...category.translations, [code]: value },
      });
      onNotice(`Αποθηκεύτηκε: ${LANGUAGE_LABELS.get(code) ?? code}`);
    } catch (cause) {
      onError(cause);
    } finally {
      setBusyLanguage(null);
    }
  }

  async function autoTranslate() {
    setIsTranslating(true);
    try {
      const result = await translateCategory(category.id, { overwrite: false });
      if (result.translated.length === 0) {
        onNotice("Δεν έλειπε καμία μετάφραση.");
        return;
      }
      const merged = { ...category.translations, ...result.translations };
      onCategoryChange({ ...category, translations: merged });
      setDrafts((current) => ({ ...current, ...result.translations }));
      onNotice(`Μεταφράστηκαν ${result.translated.length} γλώσσες`);
    } catch (cause) {
      onError(cause);
    } finally {
      setIsTranslating(false);
    }
  }

  return (
    <div className="space-y-3 border-t border-hairline bg-surface px-4 py-4">
      <button type="button" onClick={autoTranslate} disabled={isTranslating} className={BUTTON_GHOST}>
        {isTranslating ? "Μετάφραση…" : "Αυτόματη μετάφραση όσων λείπουν"}
      </button>

      <ul className="grid gap-2 sm:grid-cols-2">
        {TRANSLATABLE_LANGUAGES.map((code) => (
          <li key={code} className="flex items-center gap-2">
            <span className="w-10 shrink-0 text-xs font-semibold uppercase text-muted">{code}</span>
            <input
              type="text"
              value={drafts[code]}
              onChange={(event) =>
                setDrafts((current) => ({ ...current, [code]: event.target.value }))
              }
              onBlur={() => save(code)}
              onKeyDown={(event) => {
                if (event.key === "Enter") event.currentTarget.blur();
              }}
              disabled={busyLanguage === code || isTranslating}
              placeholder={LANGUAGE_LABELS.get(code) ?? code}
              aria-label={`Όνομα κατηγορίας στα ${LANGUAGE_LABELS.get(code) ?? code}`}
              dir={isRtl(code) ? "rtl" : "ltr"}
              className={`${INPUT_CLASS} py-1.5 text-sm`}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

function SmallButton({
  label,
  disabled,
  danger,
  onClick,
  children,
}: {
  label: string;
  disabled?: boolean;
  danger?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`size-8 rounded-lg border border-hairline text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
        danger ? "text-accent-soft hover:border-accent-soft" : "text-muted hover:border-accent hover:text-accent"
      }`}
    >
      {children}
    </button>
  );
}
