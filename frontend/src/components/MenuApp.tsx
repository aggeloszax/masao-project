"use client";

import { useEffect, useMemo, useState } from "react";
import { getLocalized, menuGroups as staticMenuGroups, type MenuGroup } from "@/data/menu";
import { useLanguage } from "@/i18n/LanguageContext";
import { MenuNav } from "@/components/MenuNav";
import { MenuCard } from "@/components/MenuCard";
import { Chat } from "@/components/Chat";
import { LanguageSelector } from "@/components/LanguageSelector";
import { fetchMenuGroups } from "@/lib/menu-api";
import { resolveActiveGroupId, resolveMenuGroupLabel } from "@/lib/menu-selection";

type MenuResult = {
  lang: string;
  groups: MenuGroup[] | null;
  status: "ready" | "fallback";
};

export function MenuApp() {
  const { lang, rtl, t } = useLanguage();
  const [menuResult, setMenuResult] = useState<MenuResult | null>(null);
  const [selectedGroup, setSelectedGroup] = useState(staticMenuGroups[0]?.id ?? "");

  useEffect(() => {
    let cancelled = false;

    fetchMenuGroups(lang)
      .then((groups) => {
        if (cancelled) return;
        setMenuResult({ lang, groups, status: "ready" });
      })
      .catch(() => {
        if (cancelled) return;
        setMenuResult({ lang, groups: null, status: "fallback" });
      });

    return () => {
      cancelled = true;
    };
  }, [lang]);

  const menuStatus = menuResult?.lang === lang ? menuResult.status : "loading";
  const menuGroups =
    menuResult?.lang === lang && menuResult.groups ? menuResult.groups : staticMenuGroups;
  const activeGroupId = resolveActiveGroupId(menuGroups, selectedGroup);
  const itemCount = useMemo(
    () =>
      menuGroups.reduce(
        (count, group) =>
          count + group.sections.reduce((total, section) => total + section.items.length, 0),
        0,
      ),
    [menuGroups],
  );

  const tabs = menuGroups.map((group) => ({
    id: group.id,
    label: resolveMenuGroupLabel(group, lang),
  }));

  // Εμφάνιση μόνο της επιλεγμένης κατηγορίας· fallback στην πρώτη αν λείπει.
  const visibleGroups = menuGroups.filter((group) => group.id === activeGroupId);

  function handleSelectGroup(id: string) {
    setSelectedGroup(id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

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

      {menuStatus === "loading" && (
        <p className="px-6 pb-3 text-center text-xs text-muted">{t.menuLoading}</p>
      )}

      {menuStatus === "fallback" && (
        <p className="px-6 pb-3 text-center text-xs text-muted">{t.menuFallback}</p>
      )}

      <MenuNav tabs={tabs} selected={activeGroupId} onSelect={handleSelectGroup} />

      <main className="px-6 pb-20">
        {visibleGroups.map((group) => (
          <section key={group.id} id={group.id} className="scroll-mt-16 pt-10">
            {/* Group header */}
            <div className="flex items-center gap-3">
              <h2 className="font-serif text-2xl uppercase tracking-[0.2em] text-accent">
                {resolveMenuGroupLabel(group, lang)}
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
        <p className="mx-auto mb-3 max-w-sm text-[11px] leading-relaxed text-muted">
          {t.allergyNotice}
        </p>
        <p className="text-xs tracking-wide text-muted">{t.footer(itemCount)}</p>
      </footer>

      <Chat />
    </div>
  );
}
