"use client";

import { getLocalized, menu, menuGroups } from "@/data/menu";
import { GROUP_LABELS } from "@/i18n/config";
import { useLanguage } from "@/i18n/LanguageContext";
import { MenuNav } from "@/components/MenuNav";
import { MenuCard } from "@/components/MenuCard";
import { Chat } from "@/components/Chat";
import { LanguageSelector } from "@/components/LanguageSelector";

export function MenuApp() {
  const { lang, rtl, t } = useLanguage();

  const tabs = menuGroups.map((group) => ({
    id: group.id,
    label: GROUP_LABELS[group.id][lang],
  }));

  return (
    <div
      dir={rtl ? "rtl" : "ltr"}
      className="mx-auto flex w-full max-w-md flex-1 flex-col bg-background"
    >
      {/* Hero */}
      <header className="relative px-6 pt-12 pb-8 text-center">
        <div className="absolute top-4 end-4">
          <LanguageSelector />
        </div>
        <p className="font-serif text-xs uppercase tracking-[0.45em] text-accent-soft">
          {t.tagline}
        </p>
        <h1 className="mt-3 font-serif text-5xl font-semibold tracking-tight text-foreground">
          Masao
        </h1>
        <p className="mt-3 text-sm text-muted">Sushi · Bao · Cocktails · Shisha</p>
        <div className="mx-auto mt-6 h-px w-16 bg-accent" />
      </header>

      <MenuNav tabs={tabs} />

      <main className="px-6 pb-20">
        {menuGroups.map((group) => (
          <section key={group.id} id={group.id} className="scroll-mt-16 pt-10">
            {/* Group header */}
            <div className="flex items-center gap-3">
              <h2 className="font-serif text-2xl uppercase tracking-[0.2em] text-accent">
                {GROUP_LABELS[group.id][lang]}
              </h2>
              <div className="h-px flex-1 bg-hairline" />
            </div>

            {group.sections.map((section) => (
              <div key={section.category} className="mt-6">
                {/* Sub-category label (shown when a group has more than one) */}
                {group.sections.length > 1 && (
                  <h3 className="mb-4 text-[11px] font-semibold uppercase tracking-[0.25em] text-accent-soft">
                    {getLocalized(section.items[0], lang).category}
                  </h3>
                )}

                <div className="flex flex-col gap-5">
                  {section.items.map((item) => (
                    <MenuCard key={item.id} item={item} />
                  ))}
                </div>
              </div>
            ))}
          </section>
        ))}
      </main>

      <footer className="border-t border-hairline px-6 py-8 text-center">
        <p className="text-xs tracking-wide text-muted">{t.footer(menu.length)}</p>
      </footer>

      <Chat />
    </div>
  );
}
