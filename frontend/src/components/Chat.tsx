"use client";

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

type Message = { id: string; role: "user" | "bot"; text: string };

const RESTAURANT_SLUG = "masao";

const ERROR_COPY: Record<Lang, string> = {
  el: "Ο σερβιτόρος δεν είναι διαθέσιμος αυτή τη στιγμή. Δοκιμάστε ξανά σε λίγο.",
  en: "The waiter is unavailable right now. Please try again in a moment.",
  de: "Der Kellner ist gerade nicht verfügbar. Bitte versuchen Sie es gleich erneut.",
  it: "Il cameriere non è disponibile al momento. Riprovi tra poco.",
  sv: "Kyparen är inte tillgänglig just nu. Försök igen om en stund.",
};

const RATE_LIMIT_COPY: Record<Lang, string> = {
  el: "Περιμένετε λίγο πριν στείλετε ξανά.",
  en: "Please wait a moment before sending another message.",
  de: "Bitte warten Sie kurz, bevor Sie eine weitere Nachricht senden.",
  it: "Attenda un momento prima di inviare un altro messaggio.",
  sv: "Vänta en stund innan du skickar ett nytt meddelande.",
};

const SUGGESTIONS_COPY: Record<Lang, string> = {
  el: "Προτάσεις από το μενού",
  en: "Suggestions from the menu",
  de: "Vorschläge aus der Karte",
  it: "Suggerimenti dal menu",
  sv: "Förslag från menyn",
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
  const [tableNumber] = useState(() =>
    typeof window === "undefined" ? 1 : getTableNumberFromUrl(),
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
        userMessage: text,
        languageCode: lang,
      });
      setMessages(response.messages.map(mapApiMessage));
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
                className="flex-1 rounded-full border border-hairline bg-surface px-4 py-2.5 text-base text-foreground outline-none placeholder:text-muted focus:border-accent"
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
                {t.chatPrivacyNotice}
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
            ? "rounded-br-sm bg-accent text-white"
            : "rounded-bl-sm bg-surface text-foreground"
        }`}
      >
        {text}
      </p>
    </div>
  );
}

function RecommendedItems({ items, title }: { items: ChatApiMenuItem[]; title: string }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-soft">
        {title}
      </p>
      {items.map((item) => (
        <div
          key={item.id}
          className="rounded-2xl rounded-bl-sm border border-hairline bg-surface px-3.5 py-2.5"
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-sm font-semibold text-foreground">{item.name}</p>
            <p className="shrink-0 text-sm text-accent">{item.price.toFixed(2)}€</p>
          </div>
          {item.description && (
            <p className="mt-0.5 text-xs leading-relaxed text-muted">{item.description}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function TypingIndicator({ typingLabel }: { typingLabel: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-surface px-3.5 py-3">
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
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
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
