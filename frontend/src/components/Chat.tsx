"use client";

import { useEffect, useRef, useState } from "react";
import { buildReply, findMatches } from "@/lib/recommend";
import { useLanguage } from "@/i18n/LanguageContext";

type Message = { id: number; role: "user" | "bot"; text: string };

export function Chat() {
  const { lang, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);

  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-scroll to the latest message / typing indicator.
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, typing, open]);

  // Clean up a pending reply timer on unmount.
  useEffect(() => () => clearTimeout(timer.current ?? undefined), []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || typing) return;

    const userMsg: Message = { id: nextId.current++, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    // Simulate network latency, then reply from the (local) "AI".
    timer.current = setTimeout(() => {
      const matches = findMatches(text);
      const botMsg: Message = {
        id: nextId.current++,
        role: "bot",
        text: buildReply(matches, lang),
      };
      setMessages((prev) => [...prev, botMsg]);
      setTyping(false);
    }, 1200);
  }

  return (
    <>
      {/* Floating launcher — kept within the centered phone column */}
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-md justify-end px-5 pb-5">
        {!open && (
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label={t.chatLauncher}
            className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent text-white shadow-lg transition-transform active:scale-95"
          >
            <ChatIcon />
          </button>
        )}
      </div>

      {/* Chat panel */}
      {open && (
        <div className="fixed inset-x-0 bottom-0 z-40 mx-auto flex max-w-md flex-col px-3 pb-3">
          <div className="flex h-[70vh] flex-col overflow-hidden rounded-2xl border border-hairline bg-background shadow-2xl">
            {/* Header */}
            <header className="flex items-center justify-between border-b border-hairline px-4 py-3">
              <div>
                <p className="font-serif text-sm uppercase tracking-[0.2em] text-accent">
                  Masao
                </p>
                <p className="text-[11px] text-muted">{t.chatSubtitle}</p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label={t.chatClose}
                className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-surface hover:text-foreground"
              >
                ✕
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
              {typing && <TypingIndicator typingLabel={t.chatTyping} />}
            </div>

            {/* Composer */}
            <form
              onSubmit={handleSubmit}
              className="flex items-center gap-2 border-t border-hairline px-3 py-3"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t.chatPlaceholder}
                aria-label={t.chatPlaceholder}
                className="flex-1 rounded-full border border-hairline bg-surface px-4 py-2.5 text-sm text-foreground outline-none placeholder:text-muted focus:border-accent"
              />
              <button
                type="submit"
                disabled={!input.trim() || typing}
                aria-label={t.chatSend}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-white transition-opacity disabled:opacity-40"
              >
                <SendIcon />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
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
