"use client";

import { useEffect, useRef, useState } from "react";

type Tab = { id: string; label: string };

export function MenuNav({ tabs }: { tabs: Tab[] }) {
  const [active, setActive] = useState(tabs[0]?.id);
  const navRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Record<string, HTMLAnchorElement | null>>({});

  // Scroll-spy: highlight the section currently nearest the top of the viewport.
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 },
    );

    for (const { id } of tabs) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [tabs]);

  // Keep the active tab in view within the horizontal scroller.
  useEffect(() => {
    if (!active) return;
    tabRefs.current[active]?.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest",
    });
  }, [active]);

  return (
    <nav className="sticky top-0 z-20 border-b border-hairline bg-background/85 backdrop-blur-md">
      <div
        ref={navRef}
        className="no-scrollbar flex gap-1.5 overflow-x-auto px-4 py-3"
      >
        {tabs.map((tab) => {
          const isActive = tab.id === active;
          return (
            <a
              key={tab.id}
              href={`#${tab.id}`}
              ref={(el) => {
                tabRefs.current[tab.id] = el;
              }}
              onClick={() => setActive(tab.id)}
              aria-current={isActive ? "true" : undefined}
              className={`shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-[13px] font-medium tracking-wide transition-colors ${
                isActive
                  ? "bg-accent text-white"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {tab.label}
            </a>
          );
        })}
      </div>
    </nav>
  );
}
