import { describe, expect, it } from "vitest";
import { buildReply, findMatches, normalize } from "./recommend";

describe("recommendation matching", () => {
  it("normalizes Greek accents and final sigma", () => {
    expect(normalize("Σολομός")).toBe("σολομοσ");
  });

  it("matches Greek user intents through accent normalization and synonyms", () => {
    const matches = findMatches("θέλω σούσι καυτερό", 5);

    expect(matches.length).toBeGreaterThan(0);
    expect(
      matches.some((item) =>
        `${item.name} ${item.category} ${item.tags.join(" ")}`.toLowerCase().includes("spicy") ||
        item.tags.some((tag) => normalize(tag).includes("πικαντικ")),
      ),
    ).toBe(true);
  });

  it("returns no matches for empty or stopword-only queries", () => {
    expect(findMatches("και το να")).toEqual([]);
  });

  it("builds localized fallback and suggestion replies", () => {
    expect(buildReply([], "en")).toContain("Sorry");

    const [first] = findMatches("σούσι καυτερό");
    if (!first) throw new Error("Expected a Greek sushi query to match a menu item");
    expect(buildReply([first], "el")).toContain(first.name);
  });
});
