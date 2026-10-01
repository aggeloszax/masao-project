"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  deleteItem,
  describeAdminError,
  isSessionExpired,
  listCategories,
  listItems,
  missingTranslationLanguages,
  reorderItems,
  updateItem,
  type AdminCategory,
  type AdminItem,
} from "@/lib/admin-api";
import {
  BUTTON_PRIMARY,
  Banner,
  EmptyState,
  INPUT_CLASS,
  LoadingState,
} from "@/components/admin/ui";

type Availability = "all" | "available" | "unavailable";

const AVAILABILITY_OPTIONS: { value: Availability; label: string }[] = [
  { value: "all", label: "Όλα" },
  { value: "available", label: "Διαθέσιμα" },
  { value: "unavailable", label: "Μη διαθέσιμα" },
];

type ItemGroup = { categoryId: number; categoryName: string; items: AdminItem[] };

export function ItemsBoard() {
  const router = useRouter();
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [items, setItems] = useState<AdminItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [availability, setAvailability] = useState<Availability>("all");
  const [onlyMissingTranslations, setOnlyMissingTranslations] = useState(false);

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

  // Η αναζήτηση χτυπάει το backend: μικρή καθυστέρηση ώστε να μη φεύγει
  // request σε κάθε πλήκτρο.
  useEffect(() => {
    const timeoutId = window.setTimeout(() => setSearch(searchInput), 300);
    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  useEffect(() => {
    listCategories().then(setCategories).catch(handleFailure);
  }, [handleFailure]);

  const filters = useMemo(
    () => ({
      categoryId,
      isAvailable: availability === "all" ? null : availability === "available",
      search,
    }),
    [availability, categoryId, search],
  );

  // Τα φίλτρα τρέχουν στο backend, οπότε κάθε αλλαγή τους ξαναφέρνει τη λίστα.
  // Το state ενημερώνεται μέσα στα callbacks του promise, ποτέ σύγχρονα.
  useEffect(() => {
    let isCurrent = true;
    listItems(filters)
      .then((nextItems) => {
        if (!isCurrent) return;
        setItems(nextItems);
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
  }, [filters, handleFailure]);

  /** Imperative refresh after a mutation that reshuffles the whole list. */
  const load = useCallback(async () => {
    try {
      setItems(await listItems(filters));
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    }
  }, [filters, handleFailure]);

  const groups = useMemo<ItemGroup[]>(() => {
    const visible = onlyMissingTranslations
      ? items.filter((item) => missingTranslationLanguages(item.translations).length > 0)
      : items;

    // Το backend επιστρέφει ήδη ταξινομημένα ανά κατηγορία, οπότε η σειρά
    // εισαγωγής στο Map είναι η σωστή σειρά εμφάνισης.
    const byCategory = new Map<number, ItemGroup>();
    for (const item of visible) {
      const group = byCategory.get(item.category_id) ?? {
        categoryId: item.category_id,
        categoryName: item.category_name,
        items: [],
      };
      group.items.push(item);
      byCategory.set(item.category_id, group);
    }
    return [...byCategory.values()];
  }, [items, onlyMissingTranslations]);

  async function toggleAvailability(item: AdminItem) {
    const nextValue = !item.is_available;
    setBusyId(item.id);
    setNotice(null);
    try {
      await updateItem(item.id, { is_available: nextValue });
      setItems((current) => {
        const updated = current.map((row) =>
          row.id === item.id ? { ...row, is_available: nextValue } : row,
        );
        // Με ενεργό φίλτρο διαθεσιμότητας το πιάτο δεν ανήκει πια στη λίστα.
        if (availability === "all") return updated;
        return updated.filter((row) => row.is_available === (availability === "available"));
      });
      setNotice(nextValue ? `«${item.name}» είναι ξανά διαθέσιμο` : `«${item.name}» βγήκε από το μενού`);
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function savePrice(item: AdminItem, price: number) {
    setBusyId(item.id);
    try {
      await updateItem(item.id, { price });
      setItems((current) => current.map((row) => (row.id === item.id ? { ...row, price } : row)));
      setNotice(`Νέα τιμή για «${item.name}»: ${price.toFixed(2)}€`);
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function move(group: ItemGroup, index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= group.items.length) return;

    const ids = group.items.map((item) => item.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];

    setBusyId(group.items[index].id);
    try {
      await reorderItems(ids);
      await load();
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  async function remove(item: AdminItem) {
    if (!window.confirm(`Διαγραφή του «${item.name}»; Η ενέργεια δεν αναιρείται.`)) return;

    setBusyId(item.id);
    try {
      await deleteItem(item.id);
      setItems((current) => current.filter((row) => row.id !== item.id));
      setNotice(`Το «${item.name}» διαγράφηκε`);
      setError(null);
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">Μενού</h1>
        <Link href="/admin/items/new" className={BUTTON_PRIMARY}>
          + Νέο πιάτο
        </Link>
      </div>

      <div className="grid gap-3 rounded-xl border border-hairline bg-white p-4 sm:grid-cols-2 lg:grid-cols-4">
        <input
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Αναζήτηση σε όνομα ή περιγραφή…"
          aria-label="Αναζήτηση πιάτων"
          className={`${INPUT_CLASS} sm:col-span-2`}
        />

        <select
          value={categoryId ?? ""}
          onChange={(event) => setCategoryId(event.target.value ? Number(event.target.value) : null)}
          aria-label="Φίλτρο κατηγορίας"
          className={INPUT_CLASS}
        >
          <option value="">Όλες οι κατηγορίες</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>

        <select
          value={availability}
          onChange={(event) => setAvailability(event.target.value as Availability)}
          aria-label="Φίλτρο διαθεσιμότητας"
          className={INPUT_CLASS}
        >
          {AVAILABILITY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-sm text-muted sm:col-span-2 lg:col-span-4">
          <input
            type="checkbox"
            checked={onlyMissingTranslations}
            onChange={(event) => setOnlyMissingTranslations(event.target.checked)}
            className="size-4 accent-[var(--accent)]"
          />
          Μόνο όσα έχουν μεταφράσεις που λείπουν
        </label>
      </div>

      {error && <Banner kind="error" message={error} onDismiss={() => setError(null)} />}
      {notice && <Banner kind="success" message={notice} onDismiss={() => setNotice(null)} />}

      {isLoading ? (
        <LoadingState />
      ) : groups.length === 0 ? (
        <EmptyState message="Κανένα πιάτο δεν ταιριάζει με τα φίλτρα." />
      ) : (
        <div className="space-y-6">
          {groups.map((group) => (
            <section key={group.categoryId} className="space-y-2">
              <h2 className="font-serif text-sm font-semibold uppercase tracking-widest text-accent">
                {group.categoryName}
                <span className="ml-2 font-sans text-xs font-normal normal-case tracking-normal text-muted">
                  {group.items.length}
                </span>
              </h2>

              <ul className="divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-white">
                {group.items.map((item, index) => (
                  <ItemRow
                    key={item.id}
                    item={item}
                    isBusy={busyId === item.id}
                    isFirst={index === 0}
                    isLast={index === group.items.length - 1}
                    onToggle={() => toggleAvailability(item)}
                    onSavePrice={(price) => savePrice(item, price)}
                    onMoveUp={() => move(group, index, -1)}
                    onMoveDown={() => move(group, index, 1)}
                    onDelete={() => remove(item)}
                  />
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function ItemRow({
  item,
  isBusy,
  isFirst,
  isLast,
  onToggle,
  onSavePrice,
  onMoveUp,
  onMoveDown,
  onDelete,
}: {
  item: AdminItem;
  isBusy: boolean;
  isFirst: boolean;
  isLast: boolean;
  onToggle: () => void;
  onSavePrice: (price: number) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
}) {
  return (
    <li className={`flex flex-wrap items-center gap-3 px-4 py-3 ${isBusy ? "opacity-60" : ""}`}>
      <button
        type="button"
        onClick={onToggle}
        disabled={isBusy}
        role="switch"
        aria-checked={item.is_available}
        aria-label={`Διαθεσιμότητα για ${item.name}`}
        title={item.is_available ? "Διαθέσιμο — κλικ για απόκρυψη" : "Μη διαθέσιμο — κλικ για επαναφορά"}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:cursor-not-allowed ${
          item.is_available ? "bg-accent" : "bg-hairline"
        }`}
      >
        <span
          aria-hidden
          className={`absolute top-0.5 size-5 rounded-full bg-white shadow transition-[left] ${
            item.is_available ? "left-[22px]" : "left-0.5"
          }`}
        />
      </button>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <Link
            href={`/admin/items/${item.id}`}
            className={`truncate text-[15px] font-medium transition-colors hover:text-accent ${
              item.is_available ? "text-foreground" : "text-muted line-through"
            }`}
          >
            {item.name}
          </Link>
        </div>
        {item.description && (
          <p className="mt-0.5 truncate text-xs text-muted">{item.description}</p>
        )}
      </div>

      <PriceCell item={item} isBusy={isBusy} onSave={onSavePrice} />

      <div className="flex shrink-0 items-center gap-1">
        <IconButton label={`Μετακίνηση πάνω: ${item.name}`} disabled={isBusy || isFirst} onClick={onMoveUp}>
          ↑
        </IconButton>
        <IconButton label={`Μετακίνηση κάτω: ${item.name}`} disabled={isBusy || isLast} onClick={onMoveDown}>
          ↓
        </IconButton>
        <IconButton label={`Διαγραφή: ${item.name}`} disabled={isBusy} onClick={onDelete} danger>
          ✕
        </IconButton>
      </div>
    </li>
  );
}

function PriceCell({
  item,
  isBusy,
  onSave,
}: {
  item: AdminItem;
  isBusy: boolean;
  onSave: (price: number) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(item.price.toFixed(2));

  function commit() {
    setIsEditing(false);
    const parsed = Number(draft.replace(",", "."));
    if (!Number.isFinite(parsed) || parsed < 0) {
      setDraft(item.price.toFixed(2));
      return;
    }
    const rounded = Math.round(parsed * 100) / 100;
    if (rounded === item.price) return;
    onSave(rounded);
  }

  if (!isEditing) {
    return (
      <button
        type="button"
        disabled={isBusy}
        onClick={() => {
          setDraft(item.price.toFixed(2));
          setIsEditing(true);
        }}
        aria-label={`Επεξεργασία τιμής για ${item.name}`}
        className="shrink-0 rounded px-1.5 py-0.5 font-serif text-base font-medium tabular-nums text-foreground transition-colors hover:bg-surface hover:text-accent disabled:cursor-not-allowed"
      >
        {item.price.toFixed(2)}€
      </button>
    );
  }

  return (
    <input
      type="text"
      inputMode="decimal"
      autoFocus
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === "Enter") commit();
        if (event.key === "Escape") {
          setDraft(item.price.toFixed(2));
          setIsEditing(false);
        }
      }}
      aria-label={`Τιμή για ${item.name}`}
      className="w-20 shrink-0 rounded border border-accent px-2 py-1 text-right font-serif text-base tabular-nums outline-none"
    />
  );
}

function IconButton({
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
