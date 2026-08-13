import type { Lang } from "@/i18n/config";

export type SelectionCopy = {
  add: string;
  selection: string;
  title: string;
  empty: string;
  note: string;
  notePlaceholder: string;
  total: string;
  clear: string;
  clearConfirm: string;
  showWaiter: string;
  edit: string;
  waiterTitle: string;
  table: string;
  noTable: string;
  waiterHint: string;
  close: string;
  decrease: string;
  increase: string;
  remove: string;
};

export const SELECTION_COPY: Record<Lang, SelectionCopy> = {
  el: { add: "Προσθήκη", selection: "Η επιλογή μου", title: "Η επιλογή μου", empty: "Δεν έχετε προσθέσει κάτι ακόμη.", note: "Σημείωση", notePlaceholder: "π.χ. χωρίς κρεμμύδι", total: "Σύνολο", clear: "Καθαρισμός", clearConfirm: "Να διαγραφεί όλη η επιλογή σας;", showWaiter: "Έτοιμο για παραγγελία", edit: "Επεξεργασία", waiterTitle: "Παραγγελία", table: "Τραπέζι", noTable: "Χωρίς αριθμό τραπεζιού", waiterHint: "Δείξτε αυτή την οθόνη στον σερβιτόρο", close: "Κλείσιμο", decrease: "Μείωση ποσότητας", increase: "Αύξηση ποσότητας", remove: "Αφαίρεση" },
  en: { add: "Add", selection: "My selection", title: "My selection", empty: "You haven't added anything yet.", note: "Note", notePlaceholder: "e.g. no onion", total: "Total", clear: "Clear", clearConfirm: "Clear your entire selection?", showWaiter: "Ready to order", edit: "Edit", waiterTitle: "Order", table: "Table", noTable: "No table number", waiterHint: "Show this screen to your waiter", close: "Close", decrease: "Decrease quantity", increase: "Increase quantity", remove: "Remove" },
  de: { add: "Hinzufügen", selection: "Meine Auswahl", title: "Meine Auswahl", empty: "Sie haben noch nichts hinzugefügt.", note: "Hinweis", notePlaceholder: "z. B. ohne Zwiebeln", total: "Gesamt", clear: "Leeren", clearConfirm: "Ihre gesamte Auswahl löschen?", showWaiter: "Bestellbereit", edit: "Bearbeiten", waiterTitle: "Bestellung", table: "Tisch", noTable: "Keine Tischnummer", waiterHint: "Zeigen Sie diese Ansicht dem Kellner", close: "Schließen", decrease: "Menge verringern", increase: "Menge erhöhen", remove: "Entfernen" },
  it: { add: "Aggiungi", selection: "La mia scelta", title: "La mia scelta", empty: "Non hai ancora aggiunto nulla.", note: "Nota", notePlaceholder: "es. senza cipolla", total: "Totale", clear: "Svuota", clearConfirm: "Vuoi cancellare tutta la selezione?", showWaiter: "Pronto per ordinare", edit: "Modifica", waiterTitle: "Ordine", table: "Tavolo", noTable: "Nessun numero di tavolo", waiterHint: "Mostra questa schermata al cameriere", close: "Chiudi", decrease: "Riduci quantità", increase: "Aumenta quantità", remove: "Rimuovi" },
  sv: { add: "Lägg till", selection: "Mitt val", title: "Mitt val", empty: "Du har inte lagt till något ännu.", note: "Anteckning", notePlaceholder: "t.ex. utan lök", total: "Totalt", clear: "Rensa", clearConfirm: "Rensa hela ditt val?", showWaiter: "Redo att beställa", edit: "Redigera", waiterTitle: "Beställning", table: "Bord", noTable: "Inget bordsnummer", waiterHint: "Visa den här skärmen för kyparen", close: "Stäng", decrease: "Minska antal", increase: "Öka antal", remove: "Ta bort" },
  fr: { add: "Ajouter", selection: "Ma sélection", title: "Ma sélection", empty: "Vous n’avez encore rien ajouté.", note: "Note", notePlaceholder: "ex. sans oignon", total: "Total", clear: "Vider", clearConfirm: "Vider toute votre sélection ?", showWaiter: "Prêt à commander", edit: "Modifier", waiterTitle: "Commande", table: "Table", noTable: "Aucun numéro de table", waiterHint: "Montrez cet écran à votre serveur", close: "Fermer", decrease: "Diminuer la quantité", increase: "Augmenter la quantité", remove: "Retirer" },
  ru: { add: "Добавить", selection: "Мой выбор", title: "Мой выбор", empty: "Вы пока ничего не добавили.", note: "Примечание", notePlaceholder: "например, без лука", total: "Итого", clear: "Очистить", clearConfirm: "Очистить весь список?", showWaiter: "Готово к заказу", edit: "Изменить", waiterTitle: "Заказ", table: "Стол", noTable: "Без номера стола", waiterHint: "Покажите этот экран официанту", close: "Закрыть", decrease: "Уменьшить количество", increase: "Увеличить количество", remove: "Удалить" },
  he: { add: "הוספה", selection: "הבחירה שלי", title: "הבחירה שלי", empty: "עדיין לא הוספתם פריטים.", note: "הערה", notePlaceholder: "למשל ללא בצל", total: "סה״כ", clear: "ניקוי", clearConfirm: "למחוק את כל הבחירה?", showWaiter: "מוכן להזמנה", edit: "עריכה", waiterTitle: "הזמנה", table: "שולחן", noTable: "ללא מספר שולחן", waiterHint: "הציגו את המסך למלצר", close: "סגירה", decrease: "הפחתת כמות", increase: "הגדלת כמות", remove: "הסרה" },
};

export const SELECTION_ADDED_COPY: Record<Lang, string> = {
  el: "Προστέθηκε",
  en: "Added",
  de: "Hinzugefügt",
  it: "Aggiunto",
  sv: "Tillagd",
  fr: "Ajouté",
  ru: "Добавлено",
  he: "נוסף",
};
