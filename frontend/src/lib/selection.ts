export type SelectionItem = {
  id: string;
  name: string;
  price: number;
  quantity: number;
  note: string;
};

export type SelectableItem = Pick<SelectionItem, "id" | "name" | "price">;

export function addSelectionItem(items: SelectionItem[], item: SelectableItem): SelectionItem[] {
  const existing = items.find((entry) => entry.id === item.id);
  if (!existing) return [...items, { ...item, quantity: 1, note: "" }];
  return items.map((entry) =>
    entry.id === item.id
      ? { ...entry, name: item.name, price: item.price, quantity: entry.quantity + 1 }
      : entry,
  );
}

export function setSelectionQuantity(
  items: SelectionItem[],
  id: string,
  quantity: number,
): SelectionItem[] {
  if (quantity <= 0) return items.filter((item) => item.id !== id);
  return items.map((item) => (item.id === id ? { ...item, quantity } : item));
}

export function setSelectionNote(items: SelectionItem[], id: string, note: string): SelectionItem[] {
  return items.map((item) => (item.id === id ? { ...item, note } : item));
}

export function selectionCount(items: SelectionItem[]): number {
  return items.reduce((sum, item) => sum + item.quantity, 0);
}

export function selectionTotal(items: SelectionItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

export function parseStoredSelection(value: string | null): SelectionItem[] {
  if (!value) return [];
  try {
    const parsed: unknown = JSON.parse(value);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isSelectionItem);
  } catch {
    return [];
  }
}

function isSelectionItem(value: unknown): value is SelectionItem {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<SelectionItem>;
  return (
    typeof item.id === "string" &&
    typeof item.name === "string" &&
    typeof item.price === "number" &&
    Number.isFinite(item.price) &&
    typeof item.quantity === "number" &&
    Number.isInteger(item.quantity) &&
    item.quantity > 0 &&
    typeof item.note === "string"
  );
}
