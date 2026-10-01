"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  createItem,
  describeAdminError,
  getItem,
  isSessionExpired,
  listCategories,
  updateItem,
  type AdminCategory,
  type AdminItem,
  type ItemPayload,
} from "@/lib/admin-api";
import { TranslationsPanel } from "@/components/admin/TranslationsPanel";
import {
  BUTTON_GHOST,
  BUTTON_PRIMARY,
  Banner,
  Field,
  INPUT_CLASS,
  LoadingState,
} from "@/components/admin/ui";

type FormState = {
  category_id: string;
  name: string;
  description: string;
  price: string;
  tags: string;
  is_available: boolean;
  display_order: string;
};

const EMPTY_FORM: FormState = {
  category_id: "",
  name: "",
  description: "",
  price: "",
  tags: "",
  is_available: true,
  display_order: "0",
};

function formFrom(item: AdminItem): FormState {
  return {
    category_id: String(item.category_id),
    name: item.name,
    description: item.description,
    price: item.price.toFixed(2),
    tags: item.tags.join(", "),
    is_available: item.is_available,
    display_order: String(item.display_order),
  };
}

type ParseResult = { ok: true; payload: ItemPayload } | { ok: false; message: string };

function toPayload(form: FormState): ParseResult {
  const categoryId = Number(form.category_id);
  if (!Number.isInteger(categoryId) || categoryId <= 0) {
    return { ok: false, message: "Επιλέξτε κατηγορία." };
  }

  const name = form.name.trim();
  if (!name) return { ok: false, message: "Το όνομα είναι υποχρεωτικό." };

  const price = Number(form.price.replace(",", "."));
  if (!Number.isFinite(price) || price < 0) {
    return { ok: false, message: "Η τιμή πρέπει να είναι θετικός αριθμός." };
  }

  const displayOrder = Number(form.display_order);
  if (!Number.isInteger(displayOrder) || displayOrder < 0) {
    return { ok: false, message: "Η σειρά εμφάνισης πρέπει να είναι ακέραιος ≥ 0." };
  }

  return {
    ok: true,
    payload: {
      category_id: categoryId,
      name,
      description: form.description.trim(),
      price: Math.round(price * 100) / 100,
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      is_available: form.is_available,
      display_order: displayOrder,
    },
  };
}

export function ItemEditor({ itemId }: { itemId: number | null }) {
  const router = useRouter();
  const isCreating = itemId === null;

  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [item, setItem] = useState<AdminItem | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [tab, setTab] = useState<"details" | "translations">("details");
  const [isLoading, setIsLoading] = useState(!isCreating);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

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

  useEffect(() => {
    listCategories().then(setCategories).catch(handleFailure);
  }, [handleFailure]);

  useEffect(() => {
    if (itemId === null) return;

    let isCurrent = true;
    getItem(itemId)
      .then((loaded) => {
        if (!isCurrent) return;
        setItem(loaded);
        setForm(formFrom(loaded));
        setError(null);
      })
      .catch(handleFailure)
      .finally(() => {
        if (isCurrent) setIsLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [handleFailure, itemId]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = toPayload(form);
    if (!parsed.ok) {
      setError(parsed.message);
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      if (itemId === null) {
        const created = await createItem(parsed.payload);
        router.push(`/admin/items/${created.id}`);
        return;
      }
      await updateItem(itemId, parsed.payload);
      // Το PATCH γυρνά τη βασική εγγραφή χωρίς κατηγορία/μεταφράσεις, οπότε
      // ξαναδιαβάζουμε το πλήρες record για να μείνει σωστό το tab μεταφράσεων.
      const refreshed = await getItem(itemId);
      setItem(refreshed);
      setForm(formFrom(refreshed));
      setNotice("Οι αλλαγές αποθηκεύτηκαν");
    } catch (cause) {
      handleFailure(cause);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href="/admin" className="text-sm text-muted transition-colors hover:text-accent">
            ← Μενού
          </Link>
          <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">
            {isCreating ? "Νέο πιάτο" : item?.name}
          </h1>
        </div>
      </div>

      {error && <Banner kind="error" message={error} onDismiss={() => setError(null)} />}
      {notice && <Banner kind="success" message={notice} onDismiss={() => setNotice(null)} />}

      {!isCreating && item !== null && (
        <div className="flex gap-1 border-b border-hairline">
          {(
            [
              { key: "details", label: "Στοιχεία" },
              { key: "translations", label: "Μεταφράσεις" },
            ] as const
          ).map((entry) => (
            <button
              key={entry.key}
              type="button"
              onClick={() => setTab(entry.key)}
              aria-current={tab === entry.key ? "true" : undefined}
              className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                tab === entry.key
                  ? "border-accent text-accent"
                  : "border-transparent text-muted hover:text-accent"
              }`}
            >
              {entry.label}
            </button>
          ))}
        </div>
      )}

      {tab === "details" || isCreating || item === null ? (
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-hairline bg-white p-4 sm:p-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Κατηγορία">
              <select
                value={form.category_id}
                onChange={(event) => update("category_id", event.target.value)}
                required
                className={INPUT_CLASS}
              >
                <option value="">— Επιλέξτε —</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Τιμή (€)">
              <input
                type="text"
                inputMode="decimal"
                value={form.price}
                onChange={(event) => update("price", event.target.value)}
                required
                className={INPUT_CLASS}
              />
            </Field>
          </div>

          <Field label="Όνομα" hint="Το βασικό κείμενο της εγγραφής· οι γλώσσες ζουν στις μεταφράσεις">
            <input
              type="text"
              value={form.name}
              onChange={(event) => update("name", event.target.value)}
              required
              maxLength={160}
              className={INPUT_CLASS}
            />
          </Field>

          <Field label="Περιγραφή">
            <textarea
              value={form.description}
              onChange={(event) => update("description", event.target.value)}
              rows={3}
              maxLength={4000}
              className={`${INPUT_CLASS} resize-y`}
            />
          </Field>

          <Field label="Tags" hint="Χωρισμένα με κόμμα, π.χ. vegan, spicy">
            <input
              type="text"
              value={form.tags}
              onChange={(event) => update("tags", event.target.value)}
              className={INPUT_CLASS}
            />
          </Field>

          <div className="sm:max-w-[50%]">
            <Field label="Σειρά εμφάνισης" hint="Μικρότερος αριθμός = ψηλότερα στην κατηγορία">
              <input
                type="number"
                min={0}
                value={form.display_order}
                onChange={(event) => update("display_order", event.target.value)}
                className={INPUT_CLASS}
              />
            </Field>
          </div>

          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={form.is_available}
              onChange={(event) => update("is_available", event.target.checked)}
              className="size-4 accent-[var(--accent)]"
            />
            Διαθέσιμο στο μενού
          </label>

          <div className="flex flex-wrap gap-2 pt-1">
            <button type="submit" disabled={isSaving} className={BUTTON_PRIMARY}>
              {isSaving ? "Αποθήκευση…" : isCreating ? "Δημιουργία" : "Αποθήκευση"}
            </button>
            <Link href="/admin" className={BUTTON_GHOST}>
              Άκυρο
            </Link>
          </div>

          {isCreating && (
            <p className="text-xs text-muted">
              Οι μεταφράσεις γίνονται διαθέσιμες μόλις δημιουργηθεί το πιάτο.
            </p>
          )}
        </form>
      ) : (
        <TranslationsPanel
          item={item}
          onItemChange={setItem}
          onError={handleFailure}
          onNotice={setNotice}
        />
      )}
    </div>
  );
}
