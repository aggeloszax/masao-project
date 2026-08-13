import { describe, expect, it } from "vitest";
import { DEFAULT_LANG, LANGUAGES, type Lang } from "@/i18n/config";
import { menu } from "./menu";

// Derived from the selector so a language added to LANGUAGES cannot ship
// without menu translations.
const REQUIRED_TRANSLATION_LANGS = LANGUAGES.map((l) => l.code).filter(
  (code): code is Exclude<Lang, "el"> => code !== DEFAULT_LANG,
);

describe("menu data invariants", () => {
  it("has unique ids and valid prices", () => {
    const ids = new Set<string>();

    for (const item of menu) {
      expect(ids.has(item.id), `duplicate id ${item.id}`).toBe(false);
      ids.add(item.id);
      expect(Number.isFinite(item.price), `${item.id} price should be numeric`).toBe(true);
      expect(item.price, `${item.id} price should be positive`).toBeGreaterThan(0);
    }
  });

  it("has required non-Greek translations", () => {
    for (const item of menu) {
      for (const lang of REQUIRED_TRANSLATION_LANGS) {
        const translation = item.translations[lang];
        expect(translation?.name, `${item.id} missing ${lang} name`).toBeTruthy();
        expect(translation?.description, `${item.id} missing ${lang} description`).toBeTruthy();
        expect(translation?.category, `${item.id} missing ${lang} category`).toBeTruthy();
      }
    }
  });

  it("does not mark the tobico Veggie Roll as vegetarian", () => {
    const veggieRoll = menu.find((item) => item.id === "UR003");

    expect(veggieRoll).toBeDefined();
    expect(veggieRoll?.description.toLowerCase()).toContain("tobico");
    expect(veggieRoll?.tags).not.toContain("χορτοφαγικό");
  });
});
