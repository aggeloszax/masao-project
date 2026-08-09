"use client";

import { createContext, useCallback, useContext, useMemo, useSyncExternalStore } from "react";
import {
  addSelectionItem,
  parseStoredSelection,
  selectionCount,
  selectionTotal,
  setSelectionNote,
  setSelectionQuantity,
  type SelectableItem,
  type SelectionItem,
} from "@/lib/selection";

const STORAGE_KEY = "masao-selection-v1";
const CHANGE_EVENT = "masao-selection-change";
const EMPTY_SELECTION: SelectionItem[] = [];
let selectionSnapshot: SelectionItem[] | null = null;

type SelectionContextValue = {
  items: SelectionItem[];
  count: number;
  total: number;
  addItem: (item: SelectableItem) => void;
  setQuantity: (id: string, quantity: number) => void;
  setNote: (id: string, note: string) => void;
  clear: () => void;
};

const SelectionContext = createContext<SelectionContextValue | null>(null);

export function SelectionProvider({ children }: { children: React.ReactNode }) {
  const items = useSyncExternalStore(subscribe, getSnapshot, () => EMPTY_SELECTION);

  const addItem = useCallback((item: SelectableItem) => {
    updateSelection((current) => addSelectionItem(current, item));
  }, []);
  const setQuantity = useCallback((id: string, quantity: number) => {
    updateSelection((current) => setSelectionQuantity(current, id, quantity));
  }, []);
  const setNote = useCallback((id: string, note: string) => {
    updateSelection((current) => setSelectionNote(current, id, note));
  }, []);
  const clear = useCallback(() => updateSelection(() => []), []);

  const value = useMemo<SelectionContextValue>(
    () => ({
      items,
      count: selectionCount(items),
      total: selectionTotal(items),
      addItem,
      setQuantity,
      setNote,
      clear,
    }),
    [addItem, clear, items, setNote, setQuantity],
  );

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

export function useSelection(): SelectionContextValue {
  const context = useContext(SelectionContext);
  if (!context) throw new Error("useSelection must be used within SelectionProvider");
  return context;
}

function subscribe(callback: () => void): () => void {
  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      selectionSnapshot = parseStoredSelection(event.newValue);
      callback();
    }
  };
  window.addEventListener("storage", handleStorage);
  window.addEventListener(CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(CHANGE_EVENT, callback);
  };
}

function getSnapshot(): SelectionItem[] {
  if (selectionSnapshot === null) {
    selectionSnapshot = parseStoredSelection(window.localStorage.getItem(STORAGE_KEY));
  }
  return selectionSnapshot;
}

function updateSelection(update: (items: SelectionItem[]) => SelectionItem[]): void {
  selectionSnapshot = update(getSnapshot());
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(selectionSnapshot));
  window.dispatchEvent(new Event(CHANGE_EVENT));
}
