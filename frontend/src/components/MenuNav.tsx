"use client";

import { useEffect, useRef } from "react";

type Tab = { id: string; label: string };

export function MenuNav({
  tabs,
  selected,
  onSelect,
}: {
  tabs: Tab[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  // Keep the selected tab in view within the horizontal scroller.
  useEffect(() => {
    tabRefs.current[selected]?.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest",
    });
  }, [selected]);

  return (
    <nav className="sticky top-0 z-20 border-b border-hairline bg-background/85 backdrop-blur-md">
      <div className="no-scrollbar flex gap-1.5 overflow-x-auto px-4 py-3">
        {tabs.map((tab) => {
          const isActive = tab.id === selected;
          return (
            <button
              key={tab.id}
              type="button"
              ref={(el) => {
                tabRefs.current[tab.id] = el;
              }}
              onClick={() => onSelect(tab.id)}
              aria-pressed={isActive}
              className={`shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-[13px] font-medium tracking-wide transition-colors ${
                isActive
                  ? "bg-accent text-white"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
