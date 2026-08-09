import { describe, expect, it } from "vitest";
import {
  addSelectionItem,
  parseStoredSelection,
  selectionCount,
  selectionTotal,
  setSelectionNote,
  setSelectionQuantity,
  type SelectionItem,
} from "./selection";

const salmon: SelectionItem = {
  id: "SR001",
  name: "Salmon Roll",
  price: 12.5,
  quantity: 1,
  note: "",
};

describe("selection helpers", () => {
  it("adds a new item and increments an existing one", () => {
    const added = addSelectionItem([], salmon);
    const incremented = addSelectionItem(added, { id: salmon.id, name: salmon.name, price: salmon.price });
    expect(incremented).toEqual([{ ...salmon, quantity: 2 }]);
  });

  it("updates quantity and removes an item at zero", () => {
    expect(setSelectionQuantity([salmon], salmon.id, 3)[0]?.quantity).toBe(3);
    expect(setSelectionQuantity([salmon], salmon.id, 0)).toEqual([]);
  });

  it("updates notes and calculates count and total", () => {
    const items = [setSelectionNote([salmon], salmon.id, "No onion")[0]!, { ...salmon, id: "D1", price: 5, quantity: 2 }];
    expect(items[0].note).toBe("No onion");
    expect(selectionCount(items)).toBe(3);
    expect(selectionTotal(items)).toBe(22.5);
  });

  it("restores only valid local-storage entries", () => {
    expect(parseStoredSelection(JSON.stringify([salmon, { id: 1 }]))).toEqual([salmon]);
    expect(parseStoredSelection("not-json")).toEqual([]);
  });
});
