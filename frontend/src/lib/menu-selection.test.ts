import { describe, expect, it } from "vitest";
import type { MenuGroup } from "@/data/menu";
import { resolveActiveGroupId, resolveMenuGroupLabel } from "@/lib/menu-selection";

const groups = [
  { id: "sushi", label: "Sushi", sections: [] },
  { id: "bao", label: "Bao", sections: [] },
] satisfies MenuGroup[];

describe("resolveActiveGroupId", () => {
  it("keeps the selected group when it exists in the loaded menu", () => {
    expect(resolveActiveGroupId(groups, "bao")).toBe("bao");
  });

  it("selects the first loaded group when the previous selection is no longer valid", () => {
    expect(resolveActiveGroupId(groups, "legacy-group")).toBe("sushi");
  });

  it("returns an empty selection when the menu has no groups", () => {
    expect(resolveActiveGroupId([], "sushi")).toBe("");
  });
});

describe("resolveMenuGroupLabel", () => {
  it("uses the localized label for a known fallback menu group", () => {
    expect(resolveMenuGroupLabel(groups[0], "el")).toBe("Σούσι");
  });

  it("keeps the backend label for a category that is not a fallback group", () => {
    const apiGroup = {
      id: "signature-rolls-8pcs",
      label: "Signature-Rollen (8 Stück)",
      sections: [],
    } satisfies MenuGroup;

    expect(resolveMenuGroupLabel(apiGroup, "de")).toBe("Signature-Rollen (8 Stück)");
  });
});
