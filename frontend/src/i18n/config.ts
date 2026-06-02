export type Lang = "el" | "en" | "de" | "it" | "sv";

export const DEFAULT_LANG: Lang = "el";

/** Languages offered in the selector. */
export const LANGUAGES: { code: Lang; label: string; flag: string; rtl?: boolean }[] = [
  { code: "el", label: "Ελληνικά", flag: "🇬🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
  { code: "it", label: "Italiano", flag: "🇮🇹" },
  { code: "sv", label: "Svenska", flag: "🇸🇪" },
];

export function isRtl(lang: Lang): boolean {
  void lang;
  return false;
}

/** Static UI strings. */
type UIStrings = {
  tagline: string;
  selectLanguage: string;
  chatLauncher: string;
  chatSubtitle: string;
  chatGreeting: string;
  chatPlaceholder: string;
  chatSend: string;
  chatClose: string;
  chatTyping: string;
  footer: (count: number) => string;
};

export const UI: Record<Lang, UIStrings> = {
  el: {
    tagline: "Λάουντζ Ασιατικής Κουζίνας",
    selectLanguage: "Επιλογή γλώσσας",
    chatLauncher: "Συνομιλία με τον σερβιτόρο",
    chatSubtitle: "Ο σερβιτόρος σας",
    chatGreeting:
      "Καλώς ήρθατε στο Masao! Πείτε μου τι σας αρέσει — κάτι καυτερό, με γαρίδα, vegan; — και θα σας προτείνω κάτι.",
    chatPlaceholder: "Γράψτε ένα μήνυμα…",
    chatSend: "Αποστολή",
    chatClose: "Κλείσιμο",
    chatTyping: "Ο σερβιτόρος πληκτρολογεί…",
    footer: (n) => `${n} πιάτα & ποτά · Masao`,
  },
  en: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Select language",
    chatLauncher: "Chat with AI Waiter",
    chatSubtitle: "Your waiter",
    chatGreeting:
      "Welcome to Masao! Tell me what you fancy — something spicy, with shrimp, vegan? — and I'll suggest something.",
    chatPlaceholder: "Type a message…",
    chatSend: "Send",
    chatClose: "Close",
    chatTyping: "The waiter is typing…",
    footer: (n) => `${n} dishes & drinks · Masao`,
  },
  de: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Sprache wählen",
    chatLauncher: "Mit dem Kellner chatten",
    chatSubtitle: "Ihr Kellner",
    chatGreeting:
      "Willkommen bei Masao! Sagen Sie mir, worauf Sie Lust haben — etwas Scharfes, mit Garnelen, vegan? — und ich empfehle Ihnen etwas.",
    chatPlaceholder: "Nachricht schreiben…",
    chatSend: "Senden",
    chatClose: "Schließen",
    chatTyping: "Der Kellner schreibt…",
    footer: (n) => `${n} Gerichte & Getränke · Masao`,
  },
  it: {
    tagline: "Lounge Fusion Asiatica",
    selectLanguage: "Seleziona lingua",
    chatLauncher: "Chatta con il cameriere",
    chatSubtitle: "Il vostro cameriere",
    chatGreeting:
      "Benvenuti da Masao! Ditemi cosa vi piace — qualcosa di piccante, con gamberi, vegano? — e vi consiglierò qualcosa.",
    chatPlaceholder: "Scrivi un messaggio…",
    chatSend: "Invia",
    chatClose: "Chiudi",
    chatTyping: "Il cameriere sta scrivendo…",
    footer: (n) => `${n} piatti e bevande · Masao`,
  },
  sv: {
    tagline: "Asiatisk Fusion Lounge",
    selectLanguage: "Välj språk",
    chatLauncher: "Chatta med kyparen",
    chatSubtitle: "Din kypare",
    chatGreeting:
      "Välkommen till Masao! Berätta vad du är sugen på — något starkt, med räkor, veganskt? — så föreslår jag något.",
    chatPlaceholder: "Skriv ett meddelande…",
    chatSend: "Skicka",
    chatClose: "Stäng",
    chatTyping: "Kyparen skriver…",
    footer: (n) => `${n} rätter & drycker · Masao`,
  },
};

/** Localized labels for the high-level nav groups, keyed by group id. */
export const GROUP_LABELS: Record<string, Record<Lang, string>> = {
  sushi: { el: "Σούσι", en: "Sushi", de: "Sushi", it: "Sushi", sv: "Sushi" },
  bites: { el: "Ορεκτικά", en: "Bites", de: "Häppchen", it: "Stuzzichini", sv: "Tilltugg" },
  bao: { el: "Μπάο", en: "Bao", de: "Bao", it: "Bao", sv: "Bao" },
  noodles: { el: "Νουντλς", en: "Noodles", de: "Nudeln", it: "Noodles", sv: "Nudlar" },
  burgers: { el: "Μπέργκερ", en: "Burgers", de: "Burger", it: "Burger", sv: "Burgare" },
  poke: { el: "Πόκε", en: "Poke", de: "Poke", it: "Poke", sv: "Poke" },
  salads: { el: "Σαλάτες", en: "Salads", de: "Salate", it: "Insalate", sv: "Sallader" },
  desserts: { el: "Επιδόρπια", en: "Desserts", de: "Desserts", it: "Dolci", sv: "Efterrätter" },
  cocktails: { el: "Κοκτέιλ", en: "Cocktails", de: "Cocktails", it: "Cocktail", sv: "Cocktails" },
  drinks: { el: "Ποτά", en: "Drinks", de: "Getränke", it: "Bevande", sv: "Drycker" },
  wines: { el: "Κρασιά", en: "Wines", de: "Weine", it: "Vini", sv: "Viner" },
  shisha: { el: "Ναργιλές", en: "Shisha", de: "Shisha", it: "Shisha", sv: "Shisha" },
};

/**
 * Display translations for the Greek tag tokens. Tags are stored in Greek in
 * the JSON (so the backend AI can filter on them); we translate only at render
 * time. Tags without an entry fall back to the original Greek token.
 */
export const TAG_TRANSLATIONS: Record<string, Record<Lang, string>> = {
  γαρίδα: { el: "Γαρίδα", en: "Shrimp", de: "Garnele", it: "Gambero", sv: "Räka" },
  κοτόπουλο: { el: "Κοτόπουλο", en: "Chicken", de: "Hähnchen", it: "Pollo", sv: "Kyckling" },
  σολομός: { el: "Σολομός", en: "Salmon", de: "Lachs", it: "Salmone", sv: "Lax" },
  τόνος: { el: "Τόνος", en: "Tuna", de: "Thunfisch", it: "Tonno", sv: "Tonfisk" },
  καυτερό: { el: "Καυτερό", en: "Spicy", de: "Scharf", it: "Piccante", sv: "Stark" },
  ελαφρύ: { el: "Ελαφρύ", en: "Light", de: "Leicht", it: "Leggero", sv: "Lätt" },
  δροσερό: { el: "Δροσερό", en: "Refreshing", de: "Erfrischend", it: "Rinfrescante", sv: "Uppfriskande" },
  γλυκόξινο: { el: "Γλυκόξινο", en: "Sweet & Sour", de: "Süß-sauer", it: "Agrodolce", sv: "Sursöt" },
  θαλασσινά: { el: "Θαλασσινά", en: "Seafood", de: "Meeresfrüchte", it: "Frutti di mare", sv: "Skaldjur" },
  premium: { el: "Premium", en: "Premium", de: "Premium", it: "Premium", sv: "Premium" },
  sushi: { el: "Sushi", en: "Sushi", de: "Sushi", it: "Sushi", sv: "Sushi" },
  τρούφα: { el: "Τρούφα", en: "Truffle", de: "Trüffel", it: "Tartufo", sv: "Tryffel" },

  // --- All remaining tags present in the menu data ---
  αλμυρό: { el: "Αλμυρό", en: "Salty", de: "Salzig", it: "Salato", sv: "Salt" },
  ανθισμένο: { el: "Ανθισμένο", en: "Floral", de: "Blumig", it: "Floreale", sv: "Blommig" },
  άπαχο: { el: "Άπαχο", en: "Lean", de: "Mager", it: "Magro", sv: "Magert" },
  απλό: { el: "Απλό", en: "Simple", de: "Einfach", it: "Semplice", sv: "Enkel" },
  αρωματικό: { el: "Αρωματικό", en: "Aromatic", de: "Aromatisch", it: "Aromatico", sv: "Aromatisk" },
  αφρώδες: { el: "Αφρώδες", en: "Sparkling", de: "Sprudelnd", it: "Frizzante", sv: "Mousserande" },
  "βαθύ άρωμα": { el: "Βαθύ άρωμα", en: "Deep aroma", de: "Tiefes Aroma", it: "Aroma intenso", sv: "Djup arom" },
  "βαθύ γεύση": { el: "Βαθιά γεύση", en: "Deep flavour", de: "Tiefer Geschmack", it: "Sapore intenso", sv: "Djup smak" },
  βασικό: { el: "Βασικό", en: "Basic", de: "Basis", it: "Base", sv: "Basic" },
  βότανα: { el: "Βότανα", en: "Herbal", de: "Kräuter", it: "Erbe", sv: "Örter" },
  βουτυράτο: { el: "Βουτυράτο", en: "Buttery", de: "Butterig", it: "Burroso", sv: "Smörig" },
  γαλλικό: { el: "Γαλλικό", en: "French", de: "Französisch", it: "Francese", sv: "Franskt" },
  γεμάτο: { el: "Γεμάτο", en: "Full-bodied", de: "Vollmundig", it: "Corposo", sv: "Fyllig" },
  γήινο: { el: "Γήινο", en: "Earthy", de: "Erdig", it: "Terroso", sv: "Jordig" },
  γλυκό: { el: "Γλυκό", en: "Sweet", de: "Süß", it: "Dolce", sv: "Söt" },
  γλυκόπικρο: { el: "Γλυκόπικρο", en: "Bittersweet", de: "Bittersüß", it: "Dolceamaro", sv: "Bitterljuv" },
  δυνατό: { el: "Δυνατό", en: "Strong", de: "Stark", it: "Forte", sv: "Stark" },
  ελληνικό: { el: "Ελληνικό", en: "Greek", de: "Griechisch", it: "Greco", sv: "Grekiskt" },
  έντονο: { el: "Έντονο", en: "Intense", de: "Intensiv", it: "Intenso", sv: "Intensiv" },
  εξωτικό: { el: "Εξωτικό", en: "Exotic", de: "Exotisch", it: "Esotico", sv: "Exotisk" },
  επίμονο: { el: "Επίμονο", en: "Lingering", de: "Anhaltend", it: "Persistente", sv: "Långvarig" },
  εσπεριδοειδές: { el: "Εσπεριδοειδές", en: "Citrus", de: "Zitrus", it: "Agrumato", sv: "Citrus" },
  ζεστό: { el: "Ζεστό", en: "Warm", de: "Warm", it: "Caldo", sv: "Varm" },
  ζουμερό: { el: "Ζουμερό", en: "Juicy", de: "Saftig", it: "Succoso", sv: "Saftig" },
  ημίγλυκο: { el: "Ημίγλυκο", en: "Semi-sweet", de: "Halbsüß", it: "Amabile", sv: "Halvsöt" },
  ημίξηρο: { el: "Ημίξηρο", en: "Semi-dry", de: "Halbtrocken", it: "Semisecco", sv: "Halvtorr" },
  θαλασσινό: { el: "Θαλασσινό", en: "Seafood", de: "Meeresfrüchte", it: "Di mare", sv: "Skaldjur" },
  θαλάσσιο: { el: "Θαλάσσιο", en: "Marine", de: "Maritim", it: "Marino", sv: "Marin" },
  ιαπωνικό: { el: "Ιαπωνικό", en: "Japanese", de: "Japanisch", it: "Giapponese", sv: "Japanskt" },
  καθαρό: { el: "Καθαρό", en: "Clean", de: "Klar", it: "Pulito", sv: "Ren" },
  καπνιστό: { el: "Καπνιστό", en: "Smoky", de: "Rauchig", it: "Affumicato", sv: "Rökig" },
  καφέ: { el: "Καφέ", en: "Coffee", de: "Kaffee", it: "Caffè", sv: "Kaffe" },
  κλασικό: { el: "Κλασικό", en: "Classic", de: "Klassisch", it: "Classico", sv: "Klassisk" },
  κοινωνικό: { el: "Κοινωνικό", en: "Social", de: "Gesellig", it: "Conviviale", sv: "Social" },
  κρεμώδες: { el: "Κρεμώδες", en: "Creamy", de: "Cremig", it: "Cremoso", sv: "Krämig" },
  λεπτό: { el: "Λεπτό", en: "Delicate", de: "Fein", it: "Delicato", sv: "Delikat" },
  λουλουδάτο: { el: "Λουλουδάτο", en: "Flowery", de: "Blumig", it: "Floreale", sv: "Blommig" },
  μέντα: { el: "Μέντα", en: "Mint", de: "Minze", it: "Menta", sv: "Mynta" },
  μεσογειακό: { el: "Μεσογειακό", en: "Mediterranean", de: "Mediterran", it: "Mediterraneo", sv: "Medelhavs" },
  μεταλλικό: { el: "Μεταλλικό", en: "Mineral", de: "Mineralisch", it: "Minerale", sv: "Mineralisk" },
  μούρα: { el: "Μούρα", en: "Berries", de: "Beeren", it: "Frutti di bosco", sv: "Bär" },
  νησιώτικο: { el: "Νησιώτικο", en: "Island", de: "Insel", it: "Isolano", sv: "Ö-karaktär" },
  ξηρό: { el: "Ξηρό", en: "Dry", de: "Trocken", it: "Secco", sv: "Torr" },
  ουδέτερο: { el: "Ουδέτερο", en: "Neutral", de: "Neutral", it: "Neutro", sv: "Neutral" },
  πικάντικο: { el: "Πικάντικο", en: "Spicy", de: "Würzig", it: "Piccante", sv: "Kryddig" },
  πικρό: { el: "Πικρό", en: "Bitter", de: "Bitter", it: "Amaro", sv: "Bitter" },
  πλούσιο: { el: "Πλούσιο", en: "Rich", de: "Reichhaltig", it: "Ricco", sv: "Rik" },
  ποικιλία: { el: "Ποικιλία", en: "Variety", de: "Auswahl", it: "Varietà", sv: "Variation" },
  πολύπλοκο: { el: "Πολύπλοκο", en: "Complex", de: "Komplex", it: "Complesso", sv: "Komplex" },
  πολυτελές: { el: "Πολυτελές", en: "Luxurious", de: "Luxuriös", it: "Lussuoso", sv: "Lyxig" },
  Προβηγκία: { el: "Προβηγκία", en: "Provence", de: "Provence", it: "Provenza", sv: "Provence" },
  σιταρένιο: { el: "Σιταρένιο", en: "Wheat", de: "Weizen", it: "Di grano", sv: "Vete" },
  σοκολάτα: { el: "Σοκολάτα", en: "Chocolate", de: "Schokolade", it: "Cioccolato", sv: "Choklad" },
  σύνθετο: { el: "Σύνθετο", en: "Layered", de: "Vielschichtig", it: "Articolato", sv: "Sammansatt" },
  τανικό: { el: "Τανικό", en: "Tannic", de: "Tanninreich", it: "Tannico", sv: "Tanninrik" },
  τραγανό: { el: "Τραγανό", en: "Crispy", de: "Knusprig", it: "Croccante", sv: "Krispig" },
  τροπικό: { el: "Τροπικό", en: "Tropical", de: "Tropisch", it: "Tropicale", sv: "Tropisk" },
  φρέσκο: { el: "Φρέσκο", en: "Fresh", de: "Frisch", it: "Fresco", sv: "Färsk" },
  φρουτώδες: { el: "Φρουτώδες", en: "Fruity", de: "Fruchtig", it: "Fruttato", sv: "Fruktig" },
  χορτοφαγικό: { el: "Χορτοφαγικό", en: "Vegetarian", de: "Vegetarisch", it: "Vegetariano", sv: "Vegetarisk" },
  "alcohol-free": { el: "Χωρίς αλκοόλ", en: "Alcohol-free", de: "Alkoholfrei", it: "Analcolico", sv: "Alkoholfri" },
  "comfort food": { el: "Comfort food", en: "Comfort food", de: "Soulfood", it: "Comfort food", sv: "Comfort food" },
  fermented: { el: "Ζυμωμένο", en: "Fermented", de: "Fermentiert", it: "Fermentato", sv: "Fermenterad" },
  healthy: { el: "Υγιεινό", en: "Healthy", de: "Gesund", it: "Sano", sv: "Hälsosam" },
  indulgent: { el: "Απολαυστικό", en: "Indulgent", de: "Genussvoll", it: "Goloso", sv: "Frossig" },
  lounge: { el: "Lounge", en: "Lounge", de: "Lounge", it: "Lounge", sv: "Lounge" },
  signature: { el: "Signature", en: "Signature", de: "Signature", it: "Signature", sv: "Signatur" },
  umami: { el: "Umami", en: "Umami", de: "Umami", it: "Umami", sv: "Umami" },
  vegan: { el: "Vegan", en: "Vegan", de: "Vegan", it: "Vegano", sv: "Vegansk" },
  "vegan-friendly": { el: "Vegan-friendly", en: "Vegan-friendly", de: "Vegan-freundlich", it: "Adatto ai vegani", sv: "Veganvänlig" },
};

/** Translate a Greek tag token to the active language, falling back to the token. */
export function translateTag(tag: string, lang: Lang): string {
  return TAG_TRANSLATIONS[tag]?.[lang] ?? tag;
}

/** Chatbot reply templates per language. */
export const REPLY: Record<
  Lang,
  {
    suggest: (name: string, price: string, desc: string) => string;
    also: (list: string) => string;
    fallback: string;
  }
> = {
  el: {
    suggest: (name, price, desc) =>
      `Φυσικά! Σας προτείνω να δοκιμάσετε το ${name} (${price}€) το οποίο είναι ${desc}. Πώς σας φαίνεται;`,
    also: (list) => ` Επίσης θα μπορούσατε να δοκιμάσετε: ${list}.`,
    fallback:
      "Συγγνώμη, δεν είμαι σίγουρος τι ακριβώς αναζητάτε. Θα προτιμούσατε κάτι από sushi, noodles, burgers, cocktails ή shisha; Πείτε μου τι σας αρέσει και θα σας προτείνω κάτι ξεχωριστό!",
  },
  en: {
    suggest: (name, price, desc) =>
      `Of course! I'd suggest the ${name} (${price}€), which is ${desc}. How does that sound?`,
    also: (list) => ` You might also like: ${list}.`,
    fallback:
      "Sorry, I'm not quite sure what you're looking for. Would you prefer sushi, noodles, burgers, cocktails or shisha? Tell me what you like and I'll suggest something special!",
  },
  de: {
    suggest: (name, price, desc) =>
      `Gerne! Ich empfehle Ihnen ${name} (${price}€) – ${desc}. Wie klingt das?`,
    also: (list) => ` Ebenfalls empfehlenswert: ${list}.`,
    fallback:
      "Entschuldigung, ich bin mir nicht ganz sicher, wonach Sie suchen. Möchten Sie lieber Sushi, Nudeln, Burger, Cocktails oder Shisha? Sagen Sie mir, was Ihnen gefällt!",
  },
  it: {
    suggest: (name, price, desc) =>
      `Certo! Le consiglio ${name} (${price}€), ovvero ${desc}. Che ne dice?`,
    also: (list) => ` Potrebbero piacerle anche: ${list}.`,
    fallback:
      "Mi scusi, non sono sicuro di cosa stia cercando. Preferisce sushi, noodles, burger, cocktail o shisha? Mi dica cosa le piace e le consiglierò qualcosa!",
  },
  sv: {
    suggest: (name, price, desc) =>
      `Självklart! Jag rekommenderar ${name} (${price}€), som är ${desc}. Hur låter det?`,
    also: (list) => ` Du kan också prova: ${list}.`,
    fallback:
      "Ursäkta, jag är inte riktigt säker på vad du letar efter. Föredrar du sushi, nudlar, burgare, cocktails eller shisha? Berätta vad du gillar så föreslår jag något!",
  },
};
