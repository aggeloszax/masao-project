"use client";

import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/i18n/LanguageContext";
import { getTableNumberFromUrl } from "@/lib/chat-api";
import { OrderError, submitTakeawayOrder } from "@/lib/orders-api";
import { ORDER_COPY, pickupLabel, type PickupSlot } from "@/selection/order-copy";
import { SELECTION_COPY } from "@/selection/copy";
import { useSelection } from "@/selection/SelectionContext";

/**
 * cart   — η λίστα επιλογής
 * mode   — dine in ή take away
 * waiter — η οθόνη που δείχνει ο πελάτης στον σερβιτόρο (αμετάβλητη)
 * form   — στοιχεία επικοινωνίας για take away
 * sent   — επιβεβαίωση αποστολής
 */
type Step = "cart" | "mode" | "waiter" | "form" | "sent";

export function SelectionPanel() {
  const { lang } = useLanguage();
  const copy = SELECTION_COPY[lang];
  const orderCopy = ORDER_COPY[lang];
  const { items, count, total, setQuantity, setNote, clear } = useSelection();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("cart");
  const [sentTotal, setSentTotal] = useState(0);
  const [tableNumber] = useState(() => (typeof window === "undefined" ? null : getTableNumberFromUrl()));
  const closeRef = useRef<HTMLButtonElement>(null);

  function closePanel() {
    // Μετά από σταλμένη παραγγελία το καλάθι αδειάζει, ώστε να μην ξανασταλεί
    // κατά λάθος η ίδια παραγγελία.
    if (step === "sent") clear();
    setStep("cart");
    setOpen(false);
  }

  // Ο listener στήνεται μία φορά ανά άνοιγμα· το ref κρατά την τρέχουσα
  // closePanel ώστε το Escape να ξέρει σε ποιο βήμα βρισκόμαστε.
  const closePanelRef = useRef(closePanel);
  useEffect(() => {
    closePanelRef.current = closePanel;
  });

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") closePanelRef.current();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  const headings: Record<Step, string> = {
    cart: copy.title,
    mode: orderCopy.modeTitle,
    waiter: copy.waiterTitle,
    form: orderCopy.takeawayTitle,
    sent: orderCopy.successTitle,
  };

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
        <div role="dialog" aria-modal="true" aria-label={headings[step]} className="fixed inset-0 z-50 bg-background">
          <div className="mx-auto flex h-full w-full max-w-md flex-col bg-background">
            <header className="flex items-center justify-between border-b border-hairline px-5 py-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-soft">Masao</p>
                <h2 className="mt-1 font-serif text-2xl text-foreground">{headings[step]}</h2>
              </div>
              <button ref={closeRef} type="button" onClick={closePanel} aria-label={copy.close} className="h-10 w-10 rounded-full border border-hairline text-xl text-muted">×</button>
            </header>

            {step === "waiter" && <WaiterSummary tableNumber={tableNumber} onEdit={() => setStep("cart")} />}

            {step === "mode" && (
              <ModeChooser
                onDineIn={() => setStep("waiter")}
                onTakeAway={() => setStep("form")}
                onBack={() => setStep("cart")}
              />
            )}

            {step === "form" && (
              <TakeawayForm
                onBack={() => setStep("mode")}
                onSent={(orderTotal) => {
                  setSentTotal(orderTotal);
                  setStep("sent");
                }}
              />
            )}

            {step === "sent" && <OrderSent total={sentTotal} onClose={closePanel} />}

            {step === "cart" && (
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
                    <button type="button" onClick={() => setStep("mode")} className="w-full rounded-full bg-accent px-5 py-3.5 text-sm font-semibold text-white">{copy.showWaiter}</button>
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

function ModeChooser({
  onDineIn,
  onTakeAway,
  onBack,
}: {
  onDineIn: () => void;
  onTakeAway: () => void;
  onBack: () => void;
}) {
  const { lang } = useLanguage();
  const orderCopy = ORDER_COPY[lang];
  const { total } = useSelection();

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-5 py-7">
        <div className="space-y-3">
          <button
            type="button"
            onClick={onDineIn}
            className="w-full rounded-2xl border-2 border-foreground px-5 py-5 text-start transition-colors hover:bg-surface active:scale-[0.99]"
          >
            <span className="block text-lg font-semibold text-foreground">{orderCopy.dineIn}</span>
            <span className="mt-1 block text-sm text-muted">{orderCopy.dineInHint}</span>
          </button>

          <button
            type="button"
            onClick={onTakeAway}
            className="w-full rounded-2xl border-2 border-accent bg-accent px-5 py-5 text-start text-white transition-opacity hover:opacity-90 active:scale-[0.99]"
          >
            <span className="block text-lg font-semibold">{orderCopy.takeAway}</span>
            <span className="mt-1 block text-sm opacity-85">{orderCopy.takeAwayHint}</span>
          </button>
        </div>

        <p className="mt-7 text-center font-serif text-2xl text-accent tabular-nums">{total.toFixed(2)}€</p>
      </div>

      <div className="border-t border-hairline px-5 py-4">
        <button type="button" onClick={onBack} className="w-full px-5 py-2 text-xs text-muted underline underline-offset-4">
          {orderCopy.back}
        </button>
      </div>
    </div>
  );
}

const PICKUP_SLOTS: PickupSlot[] = ["asap", "in_30", "in_60"];

function TakeawayForm({ onBack, onSent }: { onBack: () => void; onSent: (total: number) => void }) {
  const { lang } = useLanguage();
  const orderCopy = ORDER_COPY[lang];
  const selectionCopy = SELECTION_COPY[lang];
  const { items, total } = useSelection();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pickupSlot, setPickupSlot] = useState<PickupSlot>("asap");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = name.trim().length > 0 && phone.trim().length >= 5 && !isSending;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setError(orderCopy.errorRequired);
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      const result = await submitTakeawayOrder({
        customerName: name.trim(),
        customerPhone: phone.trim(),
        pickupSlot,
        language: lang,
        items: items.map((item) => ({ itemRef: item.id, quantity: item.quantity, note: item.note })),
      });
      onSent(result.total);
    } catch (cause) {
      // Το 422 του backend λέει ακριβώς τι φταίει (π.χ. πιάτο μη διαθέσιμο).
      setError(cause instanceof OrderError && cause.status === 422 ? cause.message : orderCopy.errorSend);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-5 py-6">
        {error && (
          <p role="alert" className="mb-4 rounded-xl border border-accent-soft/40 bg-accent-soft/5 px-4 py-3 text-sm text-accent-soft">
            {error}
          </p>
        )}

        <label className="block text-[11px] font-semibold uppercase tracking-wide text-muted">
          {orderCopy.name}
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={orderCopy.namePlaceholder}
            maxLength={120}
            autoComplete="name"
            required
            className="mt-1.5 w-full rounded-xl border border-hairline bg-surface px-3 py-3 text-base font-normal normal-case tracking-normal text-foreground outline-none focus:border-accent"
          />
        </label>

        <label className="mt-4 block text-[11px] font-semibold uppercase tracking-wide text-muted">
          {orderCopy.phone}
          <input
            type="tel"
            inputMode="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            placeholder={orderCopy.phonePlaceholder}
            maxLength={40}
            autoComplete="tel"
            required
            className="mt-1.5 w-full rounded-xl border border-hairline bg-surface px-3 py-3 text-base font-normal normal-case tracking-normal text-foreground outline-none focus:border-accent"
          />
        </label>

        <fieldset className="mt-5">
          <legend className="text-[11px] font-semibold uppercase tracking-wide text-muted">{orderCopy.pickup}</legend>
          <div className="mt-2 space-y-2">
            {PICKUP_SLOTS.map((slot) => (
              <button
                key={slot}
                type="button"
                onClick={() => setPickupSlot(slot)}
                aria-pressed={pickupSlot === slot}
                className={`w-full rounded-xl border px-4 py-3 text-start text-sm font-medium transition-colors ${
                  pickupSlot === slot
                    ? "border-accent bg-accent text-white"
                    : "border-hairline bg-surface text-foreground hover:border-accent"
                }`}
              >
                {pickupLabel(orderCopy, slot)}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="mt-6 flex items-baseline justify-between border-t border-hairline pt-4">
          <span className="font-semibold text-foreground">{selectionCopy.total}</span>
          <span className="font-serif text-2xl text-accent tabular-nums">{total.toFixed(2)}€</span>
        </div>
      </div>

      <div className="border-t border-hairline px-5 py-4">
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-full bg-accent px-5 py-3.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {isSending ? orderCopy.sending : orderCopy.confirm}
        </button>
        <button type="button" onClick={onBack} disabled={isSending} className="mt-2 w-full px-5 py-2 text-xs text-muted underline underline-offset-4">
          {orderCopy.back}
        </button>
      </div>
    </form>
  );
}

function OrderSent({ total, onClose }: { total: number; onClose: () => void }) {
  const { lang } = useLanguage();
  const orderCopy = ORDER_COPY[lang];

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-1 flex-col items-center justify-center px-8 text-center">
        <span aria-hidden className="flex h-16 w-16 items-center justify-center rounded-full bg-accent text-3xl text-white">✓</span>
        <h3 className="mt-6 font-serif text-2xl text-foreground">{orderCopy.successTitle}</h3>
        <p className="mt-3 text-sm leading-relaxed text-muted">{orderCopy.successBody}</p>
        <p className="mt-6 font-serif text-3xl text-accent tabular-nums">{total.toFixed(2)}€</p>
      </div>
      <div className="border-t border-hairline px-5 py-4">
        <button type="button" onClick={onClose} className="w-full rounded-full bg-foreground px-5 py-3.5 text-sm font-semibold text-background">
          {orderCopy.done}
        </button>
      </div>
    </div>
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
