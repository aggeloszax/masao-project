"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/i18n/LanguageContext";
import {
  ChatApiError,
  getOrCreateDeviceId,
  getTableNumberFromUrl,
  sendChatMessage,
  warmChatApi,
  type ChatApiMenuItem,
  type ChatApiMessage,
} from "@/lib/chat-api";
import type { Lang } from "@/i18n/config";
import { SELECTION_ADDED_COPY, SELECTION_COPY } from "@/selection/copy";
import { useSelection } from "@/selection/SelectionContext";

type Message = { id: string; role: "user" | "bot"; text: string };

const RESTAURANT_SLUG = "masao";

function createConversationId(): string {
  return typeof window.crypto?.randomUUID === "function"
    ? window.crypto.randomUUID()
    : `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const ERROR_COPY: Record<Lang, string> = {
  el: "Ο σερβιτόρος δεν είναι διαθέσιμος αυτή τη στιγμή. Δοκιμάστε ξανά σε λίγο.",
  en: "The waiter is unavailable right now. Please try again in a moment.",
  de: "Der Kellner ist gerade nicht verfügbar. Bitte versuchen Sie es gleich erneut.",
  it: "Il cameriere non è disponibile al momento. Riprovi tra poco.",
  sv: "Kyparen är inte tillgänglig just nu. Försök igen om en stund.",
  fr: "Le serveur n’est pas disponible pour le moment. Veuillez réessayer dans un instant.",
  ru: "Официант сейчас недоступен. Попробуйте ещё раз через некоторое время.",
  he: "המלצר אינו זמין כרגע. נסו שוב בעוד רגע.",
  tr: "Garson şu anda müsait değil. Lütfen birazdan tekrar deneyin.",
};

const RATE_LIMIT_COPY: Record<Lang, string> = {
  el: "Περιμένετε λίγο πριν στείλετε ξανά.",
  en: "Please wait a moment before sending another message.",
  de: "Bitte warten Sie kurz, bevor Sie eine weitere Nachricht senden.",
  it: "Attenda un momento prima di inviare un altro messaggio.",
  sv: "Vänta en stund innan du skickar ett nytt meddelande.",
  fr: "Veuillez patienter un instant avant d’envoyer un autre message.",
  ru: "Подождите немного, прежде чем отправить следующее сообщение.",
  he: "המתינו רגע לפני שליחת הודעה נוספת.",
  tr: "Yeni bir mesaj göndermeden önce lütfen biraz bekleyin.",
};

const SUGGESTIONS_COPY: Record<Lang, string> = {
  el: "Προτάσεις από το μενού",
  en: "Suggestions from the menu",
  de: "Vorschläge aus der Karte",
  it: "Suggerimenti dal menu",
  sv: "Förslag från menyn",
  fr: "Suggestions du menu",
  ru: "Предложения из меню",
  he: "הצעות מהתפריט",
  tr: "Menüden öneriler",
};

export function Chat() {
  const { lang, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [recommendedItems, setRecommendedItems] = useState<ChatApiMenuItem[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [deviceId, setDeviceId] = useState(() =>
    typeof window === "undefined" ? "" : getOrCreateDeviceId(),
  );
  const [conversationId] = useState(() =>
    typeof window === "undefined" ? "" : createConversationId(),
  );
  const [tableNumber] = useState(() =>
    typeof window === "undefined" ? 1 : (getTableNumberFromUrl() ?? 1),
  );

  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;

    void warmChatApi();

    const previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    inputRef.current?.focus();

    function handleDialogKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
        return;
      }

      if (event.key !== "Tab") return;

      const focusableElements = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      );
      if (!focusableElements?.length) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleDialogKeyDown);
    return () => {
      document.removeEventListener("keydown", handleDialogKeyDown);
      document.body.style.overflow = previousBodyOverflow;
      window.requestAnimationFrame(() => document.getElementById("masao-chat-launcher")?.focus());
    };
  }, [open]);

  // Auto-scroll to the latest message / typing indicator.
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, typing, open]);

  // Language-stamped snapshots (server replies, recommendation cards) would
  // otherwise keep showing the previous language after a switch.
  useEffect(() => {
    setMessages([]);
    setRecommendedItems([]);
  }, [lang]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || typing) return;

    const activeDeviceId = deviceId || getOrCreateDeviceId();
    if (!deviceId) setDeviceId(activeDeviceId);

    const userMsg: Message = { id: `local-${nextId.current++}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setRecommendedItems([]);
    setInput("");
    setTyping(true);

    try {
      const response = await sendChatMessage({
        restaurantSlug: RESTAURANT_SLUG,
        tableNumber,
        deviceId: activeDeviceId,
        conversationId: conversationId || createConversationId(),
        userMessage: text,
        languageCode: lang,
      });
      setMessages((prev) => [...prev, mapApiMessage(response.assistant_message)]);
      setRecommendedItems(response.recommended_items);
    } catch (error) {
      const text =
        error instanceof ChatApiError && error.status === 429
          ? RATE_LIMIT_COPY[lang]
          : ERROR_COPY[lang];
      const botMsg: Message = { id: `local-${nextId.current++}`, role: "bot", text };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setTyping(false);
    }
  }

  return (
    <>
      {/* Floating launcher — kept within the centered phone column */}
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-end px-5 pb-5">
        {!open && (
          <button
            id="masao-chat-launcher"
            type="button"
            onClick={() => setOpen(true)}
            aria-label={t.chatLauncher}
            aria-haspopup="dialog"
            aria-expanded={open}
            className="pointer-events-auto flex h-14 items-center gap-2.5 rounded-full bg-accent px-5 text-white shadow-lg transition-transform active:scale-95"
          >
            <ChatIcon />
            <span className="text-sm font-semibold tracking-wide">{t.chatBadge}</span>
          </button>
        )}
      </div>

      {/* Chat panel */}
      {open && (
        <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/20 px-3 pb-3">
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="masao-chat-title"
            aria-describedby="masao-chat-subtitle"
            className="flex h-[70vh] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-hairline bg-background shadow-2xl"
          >
            {/* Header */}
            <header className="flex items-center justify-between border-b border-hairline px-4 py-3">
              <div>
                <p
                  id="masao-chat-title"
                  className="font-serif text-sm uppercase tracking-[0.2em] text-accent"
                >
                  Masao
                </p>
                <p id="masao-chat-subtitle" className="text-[11px] text-muted">
                  {t.chatSubtitle}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label={t.chatClose}
                className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-surface hover:text-foreground"
              >
                <CloseIcon />
              </button>
            </header>

            {/* Messages */}
            <div
              ref={scrollRef}
              className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
              aria-live="polite"
            >
              <Bubble role="bot" text={t.chatGreeting} />
              {messages.map((m) => (
                <Bubble key={m.id} role={m.role} text={m.text} />
              ))}
              {!typing && recommendedItems.length > 0 && (
                <RecommendedItems items={recommendedItems} title={SUGGESTIONS_COPY[lang]} />
              )}
              {typing && <TypingIndicator typingLabel={t.chatTyping} />}
            </div>

            {/* Composer */}
            <form
              onSubmit={handleSubmit}
              className="flex flex-wrap items-center gap-2 border-t border-hairline px-3 py-3"
            >
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                maxLength={1000}
                placeholder={t.chatPlaceholder}
                aria-label={t.chatPlaceholder}
                className="flex-1 touch-manipulation rounded-full border border-hairline bg-surface px-4 py-2.5 text-[16px] text-foreground outline-none placeholder:text-muted focus:border-accent"
              />
              <button
                type="submit"
                disabled={!input.trim() || typing}
                aria-label={t.chatSend}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-white transition-opacity disabled:opacity-40"
              >
                <SendIcon />
              </button>
              <p className="basis-full px-1 pt-1 text-[10px] leading-relaxed text-muted">
                {t.allergyNotice}
              </p>
              <p className="basis-full px-1 text-[10px] leading-relaxed text-muted">
                {t.chatPrivacyNotice}{" "}
                <Link href="/privacy" className="font-medium text-accent underline underline-offset-2">
                  {t.privacyPolicy}
                </Link>
              </p>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

function mapApiMessage(message: ChatApiMessage): Message {
  return {
    id: `server-${message.id}`,
    role: message.role === "user" ? "user" : "bot",
    text: message.content,
  };
}

function Bubble({ role, text }: { role: "user" | "bot"; text: string }) {
  const isUser = role === "user";
  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <p
        className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "rounded-ee-sm bg-accent text-white"
            : "rounded-es-sm bg-surface text-foreground"
        }`}
      >
        {text}
      </p>
    </div>
  );
}

function RecommendedItems({ items, title }: { items: ChatApiMenuItem[]; title: string }) {
  const { lang } = useLanguage();
  const { addItem, items: selectedItems } = useSelection();
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-soft">
        {title}
      </p>
      {items.map((item) => {
        const selectionId = String(item.external_id ?? item.id);
        const isSelected = selectedItems.some((selectedItem) => selectedItem.id === selectionId);

        return (
          <div
            key={item.id}
            className="rounded-2xl rounded-es-sm border border-hairline bg-surface px-3.5 py-2.5"
          >
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-sm font-semibold text-foreground">{item.name}</p>
              <p className="shrink-0 text-sm text-accent">{item.price.toFixed(2)}€</p>
            </div>
            {item.description && (
              <p className="mt-0.5 text-xs leading-relaxed text-muted">{item.description}</p>
            )}
            <button
              type="button"
              onClick={() => addItem({ id: selectionId, name: item.name, price: item.price })}
              className={`mt-2 inline-flex items-center gap-1 rounded-full border border-accent px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                isSelected ? "bg-accent text-white" : "text-accent"
              }`}
            >
              <span aria-hidden>{isSelected ? "✓" : "+"}</span>
              {isSelected ? SELECTION_ADDED_COPY[lang] : SELECTION_COPY[lang].add}
            </button>
          </div>
        );
      })}
    </div>
  );
}

function TypingIndicator({ typingLabel }: { typingLabel: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1 rounded-2xl rounded-es-sm bg-surface px-3.5 py-3">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
      <span className="text-[11px] text-muted">{typingLabel}</span>
    </div>
  );
}

function ChatIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 5h16v11H8l-4 4V5z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden className="rtl:-scale-x-100">
      <path
        d="M4 12l16-7-7 16-2.5-6.5L4 12z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M6 6l12 12M18 6L6 18"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}
