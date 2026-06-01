"use client";

import { getLocalized, type MenuItem } from "@/data/menu";
import { translateTag } from "@/i18n/config";
import { useLanguage } from "@/i18n/LanguageContext";

export function MenuCard({ item }: { item: MenuItem }) {
  const { lang } = useLanguage();
  const { name, description } = getLocalized(item, lang);

  return (
    <article className="border-b border-hairline pb-5">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-[17px] font-medium leading-tight tracking-tight text-foreground">
          {name}
        </h3>
        <div
          aria-hidden
          className="mx-1 h-px flex-1 translate-y-[-2px] self-end bg-hairline"
        />
        <span className="shrink-0 font-serif text-lg font-medium text-foreground tabular-nums">
          {item.price.toFixed(2)}€
        </span>
      </div>

      {description && (
        <p className="mt-1.5 text-sm leading-relaxed text-muted">{description}</p>
      )}

      {item.tags.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {item.tags.map((tag) => (
            <li
              key={tag}
              className="rounded-full border border-hairline bg-surface px-2 py-0.5 text-[11px] font-medium tracking-wide text-muted"
            >
              {translateTag(tag, lang)}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
