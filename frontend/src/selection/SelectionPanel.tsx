"use client";

import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/i18n/LanguageContext";
import { getTableNumberFromUrl } from "@/lib/chat-api";
import { SELECTION_COPY } from "@/selection/copy";
import { useSelection } from "@/selection/SelectionContext";

export function SelectionPanel() {
  const { lang } = useLanguage();
  const copy = SELECTION_COPY[lang];
  const { items, count, total, setQuantity, setNote, clear } = useSelection();
  const [open, setOpen] = useState(false);
  const [waiterMode, setWaiterMode] = useState(false);
  const [tableNumber] = useState(() => typeof window === "undefined" ? null : getTableNumberFromUrl());
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setWaiterMode(false);
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  return (
    <>
      {count > 0 && !open && (
        <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-start px-5 pb-5">
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label={`${copy.selection}: ${count}`}
            className="pointer-events-auto relative flex h-14 w-14 items-center justify-center rounded-full bg-foreground text-background shadow-lg active:scale-95"
          >
            <BagIcon />
            <span className="absolute -end-1 -top-1 flex h-6 min-w-6 items-center justify-center rounded-full bg-accent px-1.5 text-[11px] font-bold text-white ring-2 ring-background">
              {count}
            </span>
          </button>
        </div>
      )}

      {open && (
        <div role="dialog" aria-modal="true" aria-label={copy.title} className="fixed inset-0 z-50 bg-background">
          <div className="mx-auto flex h-full w-full max-w-md flex-col bg-background">
            <header className="flex items-center justify-between border-b border-hairline px-5 py-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-soft">Masao</p>
                <h2 className="mt-1 font-serif text-2xl text-foreground">{waiterMode ? copy.waiterTitle : copy.title}</h2>
              </div>
              <button ref={closeRef} type="button" onClick={() => { setWaiterMode(false); setOpen(false); }} aria-label={copy.close} className="h-10 w-10 rounded-full border border-hairline text-xl text-muted">×</button>
            </header>

            {waiterMode ? (
              <WaiterSummary tableNumber={tableNumber} onEdit={() => setWaiterMode(false)} />
            ) : (
              <div className="flex min-h-0 flex-1 flex-col">
                <div className="flex-1 overflow-y-auto px-5 py-5">
                  {items.length === 0 ? (
                    <p className="py-16 text-center text-sm text-muted">{copy.empty}</p>
                  ) : (
                    <div className="space-y-5">
                      {items.map((item) => (
                        <article key={item.id} className="border-b border-hairline pb-5">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-medium text-foreground">{item.name}</h3>
                              <p className="mt-1 font-serif text-sm text-accent">{(item.price * item.quantity).toFixed(2)}€</p>
                            </div>
                            <div className="flex items-center rounded-full border border-hairline">
                              <button type="button" aria-label={item.quantity === 1 ? copy.remove : copy.decrease} onClick={() => setQuantity(item.id, item.quantity - 1)} className="h-9 w-9 text-lg text-muted">{item.quantity === 1 ? "×" : "−"}</button>
                              <span className="min-w-8 text-center text-sm font-semibold tabular-nums">{item.quantity}</span>
                              <button type="button" aria-label={copy.increase} onClick={() => setQuantity(item.id, item.quantity + 1)} className="h-9 w-9 text-lg text-accent">+</button>
                            </div>
                          </div>
                          <label className="mt-3 block text-[11px] font-semibold uppercase tracking-wide text-muted">
                            {copy.note}
                            <input value={item.note} onChange={(event) => setNote(item.id, event.target.value)} maxLength={120} placeholder={copy.notePlaceholder} className="mt-1.5 w-full rounded-xl border border-hairline bg-surface px-3 py-2.5 text-sm font-normal normal-case tracking-normal text-foreground outline-none focus:border-accent" />
                          </label>
                        </article>
                      ))}
                    </div>
                  )}
                </div>

                {items.length > 0 && (
                  <footer className="border-t border-hairline bg-background px-5 py-4">
                    <div className="mb-4 flex items-baseline justify-between">
                      <span className="font-semibold text-foreground">{copy.total}</span>
                      <span className="font-serif text-2xl text-accent tabular-nums">{total.toFixed(2)}€</span>
                    </div>
                    <button type="button" onClick={() => setWaiterMode(true)} className="w-full rounded-full bg-accent px-5 py-3.5 text-sm font-semibold text-white">{copy.showWaiter}</button>
                    <button type="button" onClick={() => { if (window.confirm(copy.clearConfirm)) clear(); }} className="mt-2 w-full px-5 py-2 text-xs text-muted underline underline-offset-4">{copy.clear}</button>
                  </footer>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function WaiterSummary({ tableNumber, onEdit }: { tableNumber: number | null; onEdit: () => void }) {
  const { lang } = useLanguage();
  const copy = SELECTION_COPY[lang];
  const { items, total } = useSelection();
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-7">
        {tableNumber && (
          <div className="rounded-2xl bg-foreground px-5 py-4 text-center text-background">
            <p className="text-xs uppercase tracking-[0.25em] opacity-70">{copy.table}</p>
            <p className="mt-1 font-serif text-5xl">{tableNumber}</p>
          </div>
        )}
        <div className="mt-7 space-y-5">
          {items.map((item) => (
            <div key={item.id} className="flex gap-4 border-b border-hairline pb-5">
              <span className="flex h-9 min-w-9 items-center justify-center rounded-full bg-accent text-sm font-bold text-white">{item.quantity}×</span>
              <div className="min-w-0 flex-1">
                <p className="text-lg font-semibold leading-tight text-foreground">{item.name}</p>
                {item.note && <p className="mt-1.5 text-sm font-medium text-accent">{copy.note}: {item.note}</p>}
              </div>
              <p className="shrink-0 font-serif text-lg tabular-nums">{(item.price * item.quantity).toFixed(2)}€</p>
            </div>
          ))}
        </div>
        <div className="mt-7 flex items-baseline justify-between border-t-2 border-foreground pt-4">
          <span className="text-lg font-bold">{copy.total}</span>
          <span className="font-serif text-3xl font-semibold text-accent tabular-nums">{total.toFixed(2)}€</span>
        </div>
        <p className="mt-8 text-center text-xs text-muted">{copy.waiterHint}</p>
      </div>
      <div className="border-t border-hairline px-5 py-4">
        <button type="button" onClick={onEdit} className="w-full rounded-full border border-foreground px-5 py-3 text-sm font-semibold text-foreground">{copy.edit}</button>
      </div>
    </div>
  );
}

function BagIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden><path d="M5 8h14l-1 12H6L5 8zm4 0a3 3 0 016 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}
