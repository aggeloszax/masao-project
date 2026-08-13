import tagTranslationsFrRu from "@/data/tag-translations-fr-ru.json";

export type Lang = "el" | "en" | "de" | "it" | "sv" | "fr" | "ru" | "he" | "tr";

export const DEFAULT_LANG: Lang = "el";

/** Languages offered in the selector. */
export const LANGUAGES: { code: Lang; label: string; flag: string; rtl?: boolean }[] = [
  { code: "el", label: "Ελληνικά", flag: "🇬🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
  { code: "it", label: "Italiano", flag: "🇮🇹" },
  { code: "sv", label: "Svenska", flag: "🇸🇪" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "ru", label: "Русский", flag: "🇷🇺" },
  { code: "he", label: "עברית", flag: "🇮🇱", rtl: true },
  { code: "tr", label: "Türkçe", flag: "🇹🇷" },
];

export function isRtl(lang: Lang): boolean {
  return LANGUAGES.some((language) => language.code === lang && language.rtl);
}

/** Static UI strings. */
type UIStrings = {
  tagline: string;
  selectLanguage: string;
  chatLauncher: string;
  chatBadge: string;
  chatSubtitle: string;
  chatGreeting: string;
  chatPlaceholder: string;
  chatSend: string;
  chatClose: string;
  chatTyping: string;
  menuLoading: string;
  menuFallback: string;
  allergyNotice: string;
  chatPrivacyNotice: string;
  privacyPolicy: string;
  footer: (count: number) => string;
};

export const UI: Record<Lang, UIStrings> = {
  el: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Επιλογή γλώσσας",
    chatLauncher: "Συνομιλία με τον σερβιτόρο",
    chatBadge: "AI Σερβιτόρος",
    chatSubtitle: "Ο AI σερβιτόρος σας",
    chatGreeting:
      "Καλώς ήρθατε στο Masao! Είμαι ο ψηφιακός σας σερβιτόρος. Ρωτήστε με ό,τι θέλετε για το μενού, ή πείτε μου τι σας αρέσει και θα σας προτείνω κάτι.",
    chatPlaceholder: "Γράψτε ένα μήνυμα…",
    chatSend: "Αποστολή",
    chatClose: "Κλείσιμο",
    chatTyping: "Ο σερβιτόρος πληκτρολογεί…",
    menuLoading: "Φόρτωση μενού…",
    menuFallback: "Προσωρινή εμφάνιση αποθηκευμένου μενού.",
    allergyNotice: "Οι πληροφορίες αλλεργιογόνων και οι απαντήσεις του AI μπορεί να είναι ελλιπείς. Για αλλεργίες ή δυσανεξίες, ενημερώστε και επιβεβαιώστε πάντα με το προσωπικό πριν παραγγείλετε.",
    chatPrivacyNotice: "Το chat επεξεργάζεται από AI και τα μηνύματα διατηρούνται έως 30 ημέρες. Μην γράφετε όνομα, τηλέφωνο ή άλλα στοιχεία ταυτοποίησης.",
    privacyPolicy: "Πολιτική Απορρήτου",
    footer: (n) => `${n} πιάτα & ποτά · Masao`,
  },
  en: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Select language",
    chatLauncher: "Chat with AI Waiter",
    chatBadge: "AI Waiter",
    chatSubtitle: "Your AI waiter",
    chatGreeting:
      "Welcome to Masao! I'm your digital waiter. Ask me anything about the menu, or tell me what you're in the mood for and I'll suggest something.",
    chatPlaceholder: "Type a message…",
    chatSend: "Send",
    chatClose: "Close",
    chatTyping: "The waiter is typing…",
    menuLoading: "Loading menu…",
    menuFallback: "Showing the saved menu for now.",
    allergyNotice: "Allergen information and AI answers may be incomplete. For allergies or intolerances, always inform and confirm with our staff before ordering.",
    chatPrivacyNotice: "The chat is processed by AI and messages are retained for up to 30 days. Do not enter your name, phone number or other identifying details.",
    privacyPolicy: "Privacy Policy",
    footer: (n) => `${n} dishes & drinks · Masao`,
  },
  de: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Sprache wählen",
    chatLauncher: "Mit dem Kellner chatten",
    chatBadge: "KI-Kellner",
    chatSubtitle: "Ihr KI-Kellner",
    chatGreeting:
      "Willkommen bei Masao! Ich bin Ihr digitaler Kellner. Fragen Sie mich alles zur Karte, oder sagen Sie mir, worauf Sie Lust haben, und ich empfehle Ihnen etwas.",
    chatPlaceholder: "Nachricht schreiben…",
    chatSend: "Senden",
    chatClose: "Schließen",
    chatTyping: "Der Kellner schreibt…",
    menuLoading: "Menü wird geladen…",
    menuFallback: "Vorübergehend wird das gespeicherte Menü angezeigt.",
    allergyNotice: "Allergeninformationen und KI-Antworten können unvollständig sein. Informieren Sie bei Allergien oder Unverträglichkeiten vor der Bestellung immer unser Personal.",
    chatPrivacyNotice: "Der Chat wird durch KI verarbeitet und Nachrichten werden bis zu 30 Tage gespeichert. Geben Sie keinen Namen, keine Telefonnummer oder andere Identifikationsdaten ein.",
    privacyPolicy: "Datenschutzerklärung",
    footer: (n) => `${n} Gerichte & Getränke · Masao`,
  },
  it: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Seleziona lingua",
    chatLauncher: "Chatta con il cameriere",
    chatBadge: "Cameriere AI",
    chatSubtitle: "Il vostro cameriere AI",
    chatGreeting:
      "Benvenuti da Masao! Sono il vostro cameriere digitale. Chiedetemi qualsiasi cosa sul menu, oppure ditemi cosa vi va e vi consiglierò qualcosa.",
    chatPlaceholder: "Scrivi un messaggio…",
    chatSend: "Invia",
    chatClose: "Chiudi",
    chatTyping: "Il cameriere sta scrivendo…",
    menuLoading: "Caricamento del menu…",
    menuFallback: "Per ora viene mostrato il menu salvato.",
    allergyNotice: "Le informazioni sugli allergeni e le risposte dell’AI possono essere incomplete. Per allergie o intolleranze, informate sempre il personale prima di ordinare.",
    chatPrivacyNotice: "La chat è elaborata dall’AI e i messaggi sono conservati fino a 30 giorni. Non inserite nome, telefono o altri dati identificativi.",
    privacyPolicy: "Informativa sulla privacy",
    footer: (n) => `${n} piatti e bevande · Masao`,
  },
  sv: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Välj språk",
    chatLauncher: "Chatta med kyparen",
    chatBadge: "AI-kypare",
    chatSubtitle: "Din AI-kypare",
    chatGreeting:
      "Välkommen till Masao! Jag är din digitala kypare. Fråga mig vad som helst om menyn, eller berätta vad du är sugen på så föreslår jag något.",
    chatPlaceholder: "Skriv ett meddelande…",
    chatSend: "Skicka",
    chatClose: "Stäng",
    chatTyping: "Kyparen skriver…",
    menuLoading: "Laddar menyn…",
    menuFallback: "Visar den sparade menyn tills vidare.",
    allergyNotice: "Allergeninformation och AI-svar kan vara ofullständiga. Vid allergier eller intoleranser ska du alltid informera personalen innan du beställer.",
    chatPrivacyNotice: "Chatten behandlas av AI och meddelanden sparas i upp till 30 dagar. Ange inte namn, telefonnummer eller andra identifierande uppgifter.",
    privacyPolicy: "Integritetspolicy",
    footer: (n) => `${n} rätter & drycker · Masao`,
  },
  fr: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Choisir la langue",
    chatLauncher: "Discuter avec le serveur IA",
    chatBadge: "Serveur IA",
    chatSubtitle: "Votre serveur IA",
    chatGreeting: "Bienvenue chez Masao ! Je suis votre serveur numérique. Posez-moi vos questions sur le menu ou dites-moi ce qui vous fait envie et je vous proposerai quelque chose.",
    chatPlaceholder: "Écrivez un message…",
    chatSend: "Envoyer",
    chatClose: "Fermer",
    chatTyping: "Le serveur écrit…",
    menuLoading: "Chargement du menu…",
    menuFallback: "Affichage temporaire du menu enregistré.",
    allergyNotice: "Les informations sur les allergènes et les réponses de l’IA peuvent être incomplètes. En cas d’allergie ou d’intolérance, informez toujours le personnel et confirmez avec lui avant de commander.",
    chatPrivacyNotice: "Le chat est traité par une IA et les messages sont conservés jusqu’à 30 jours. N’indiquez pas votre nom, votre numéro de téléphone ni d’autres informations permettant de vous identifier.",
    privacyPolicy: "Politique de confidentialité",
    footer: (n) => `${n} plats et boissons · Masao`,
  },
  ru: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Выбрать язык",
    chatLauncher: "Чат с ИИ-официантом",
    chatBadge: "ИИ-официант",
    chatSubtitle: "Ваш ИИ-официант",
    chatGreeting: "Добро пожаловать в Masao! Я ваш цифровой официант. Спросите меня о меню или расскажите, чего вам хочется, и я что-нибудь порекомендую.",
    chatPlaceholder: "Введите сообщение…",
    chatSend: "Отправить",
    chatClose: "Закрыть",
    chatTyping: "Официант печатает…",
    menuLoading: "Загрузка меню…",
    menuFallback: "Временно показываем сохранённое меню.",
    allergyNotice: "Информация об аллергенах и ответы ИИ могут быть неполными. При аллергии или непереносимости обязательно сообщите персоналу и уточните информацию перед заказом.",
    chatPrivacyNotice: "Чат обрабатывается ИИ, а сообщения хранятся до 30 дней. Не указывайте имя, номер телефона и другие идентифицирующие данные.",
    privacyPolicy: "Политика конфиденциальности",
    footer: (n) => `${n} блюд и напитков · Masao`,
  },
  he: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "בחירת שפה",
    chatLauncher: "צ'אט עם המלצר",
    chatBadge: "מלצר AI",
    chatSubtitle: "מלצר ה-AI שלכם",
    chatGreeting:
      "ברוכים הבאים למסאו! אני המלצר הדיגיטלי שלכם. שאלו אותי כל דבר על התפריט, או ספרו לי מה בא לכם ואציע לכם משהו.",
    chatPlaceholder: "כתבו הודעה…",
    chatSend: "שליחה",
    chatClose: "סגירה",
    chatTyping: "המלצר מקליד…",
    menuLoading: "התפריט נטען…",
    menuFallback: "מוצג כרגע התפריט השמור.",
    allergyNotice: "מידע על אלרגנים ותשובות ה-AI עלולים להיות חלקיים. במקרה של אלרגיה או רגישות יש תמיד ליידע ולאשר עם הצוות לפני ההזמנה.",
    chatPrivacyNotice: "הצ'אט מעובד באמצעות AI וההודעות נשמרות עד 30 יום. אין להזין שם, מספר טלפון או פרטים מזהים אחרים.",
    privacyPolicy: "מדיניות פרטיות",
    footer: (n) => `${n} מנות ומשקאות · Masao`,
  },
  tr: {
    tagline: "Asian Fusion Lounge",
    selectLanguage: "Dil seçin",
    chatLauncher: "Garsonla sohbet edin",
    chatBadge: "Yapay Zekâ Garson",
    chatSubtitle: "Yapay zekâ garsonunuz",
    chatGreeting:
      "Masao'ya hoş geldiniz! Ben dijital garsonunuzum. Menüyle ilgili her şeyi sorabilir ya da canınızın ne istediğini söyleyebilirsiniz, size bir şeyler önereyim.",
    chatPlaceholder: "Bir mesaj yazın…",
    chatSend: "Gönder",
    chatClose: "Kapat",
    chatTyping: "Garson yazıyor…",
    menuLoading: "Menü yükleniyor…",
    menuFallback: "Şimdilik kayıtlı menü gösteriliyor.",
    allergyNotice: "Alerjen bilgileri ve yapay zekâ yanıtları eksik olabilir. Alerji veya intoleranslarınız varsa sipariş vermeden önce her zaman personelimizi bilgilendirin ve teyit edin.",
    chatPrivacyNotice: "Sohbet yapay zekâ tarafından işlenir ve mesajlar 30 güne kadar saklanır. Adınızı, telefon numaranızı veya diğer kimlik bilgilerinizi yazmayın.",
    privacyPolicy: "Gizlilik Politikası",
    footer: (n) => `${n} yemek ve içecek · Masao`,
  },
};

/** Localized labels for the high-level nav groups, keyed by group id. */
export const GROUP_LABELS: Record<string, Record<Lang, string>> = {
  sushi: { el: "Σούσι", en: "Sushi", de: "Sushi", it: "Sushi", sv: "Sushi", fr: "Sushi", ru: "Суши", he: "סושי", tr: "Suşi" },
  bites: { el: "Ορεκτικά", en: "Bites", de: "Häppchen", it: "Stuzzichini", sv: "Tilltugg", fr: "Entrées", ru: "Закуски", he: "נשנושים", tr: "Atıştırmalıklar" },
  bao: { el: "Μπάο", en: "Bao", de: "Bao", it: "Bao", sv: "Bao", fr: "Bao", ru: "Бао", he: "באו", tr: "Bao" },
  noodles: { el: "Νουντλς", en: "Noodles", de: "Nudeln", it: "Noodles", sv: "Nudlar", fr: "Nouilles", ru: "Лапша", he: "נודלס", tr: "Noodle" },
  burgers: { el: "Μπέργκερ", en: "Burgers", de: "Burger", it: "Burger", sv: "Burgare", fr: "Burgers", ru: "Бургеры", he: "המבורגרים", tr: "Burgerler" },
  poke: { el: "Πόκε", en: "Poke", de: "Poke", it: "Poke", sv: "Poke", fr: "Poke", ru: "Поке", he: "פוקי", tr: "Poke" },
  salads: { el: "Σαλάτες", en: "Salads", de: "Salate", it: "Insalate", sv: "Sallader", fr: "Salades", ru: "Салаты", he: "סלטים", tr: "Salatalar" },
  desserts: { el: "Επιδόρπια", en: "Desserts", de: "Desserts", it: "Dolci", sv: "Efterrätter", fr: "Desserts", ru: "Десерты", he: "קינוחים", tr: "Tatlılar" },
  cocktails: { el: "Κοκτέιλ", en: "Cocktails", de: "Cocktails", it: "Cocktail", sv: "Cocktails", fr: "Cocktails", ru: "Коктейли", he: "קוקטיילים", tr: "Kokteyller" },
  drinks: { el: "Ποτά", en: "Drinks", de: "Getränke", it: "Bevande", sv: "Drycker", fr: "Boissons", ru: "Напитки", he: "משקאות", tr: "İçecekler" },
  wines: { el: "Κρασιά", en: "Wines", de: "Weine", it: "Vini", sv: "Viner", fr: "Vins", ru: "Вина", he: "יינות", tr: "Şaraplar" },
  shisha: { el: "Ναργιλές", en: "Shisha", de: "Shisha", it: "Shisha", sv: "Shisha", fr: "Chicha", ru: "Кальян", he: "נרגילה", tr: "Nargile" },
};

/**
 * Display translations for the Greek tag tokens. Tags are stored in Greek in
 * the JSON (so the backend AI can filter on them); we translate only at render
 * time. Tags without an entry fall back to the original Greek token.
 */
export const TAG_TRANSLATIONS: Record<string, Partial<Record<Lang, string>>> = {
  γαρίδα: { el: "Γαρίδα", en: "Shrimp", de: "Garnele", it: "Gambero", sv: "Räka", he: "שרימפס", tr: "Karides" },
  κοτόπουλο: { el: "Κοτόπουλο", en: "Chicken", de: "Hähnchen", it: "Pollo", sv: "Kyckling", he: "עוף", tr: "Tavuk" },
  σολομός: { el: "Σολομός", en: "Salmon", de: "Lachs", it: "Salmone", sv: "Lax", he: "סלמון", tr: "Somon" },
  τόνος: { el: "Τόνος", en: "Tuna", de: "Thunfisch", it: "Tonno", sv: "Tonfisk", he: "טונה", tr: "Ton balığı" },
  καυτερό: { el: "Καυτερό", en: "Spicy", de: "Scharf", it: "Piccante", sv: "Stark", he: "חריף", tr: "Acılı" },
  ελαφρύ: { el: "Ελαφρύ", en: "Light", de: "Leicht", it: "Leggero", sv: "Lätt", he: "קליל", tr: "Hafif" },
  δροσερό: { el: "Δροσερό", en: "Refreshing", de: "Erfrischend", it: "Rinfrescante", sv: "Uppfriskande", he: "מרענן", tr: "Ferahlatıcı" },
  γλυκόξινο: { el: "Γλυκόξινο", en: "Sweet & Sour", de: "Süß-sauer", it: "Agrodolce", sv: "Sursöt", he: "חמוץ-מתוק", tr: "Tatlı-ekşi" },
  θαλασσινά: { el: "Θαλασσινά", en: "Seafood", de: "Meeresfrüchte", it: "Frutti di mare", sv: "Skaldjur", he: "פירות ים", tr: "Deniz ürünleri" },
  premium: { el: "Premium", en: "Premium", de: "Premium", it: "Premium", sv: "Premium", he: "פרימיום", tr: "Premium" },
  sushi: { el: "Sushi", en: "Sushi", de: "Sushi", it: "Sushi", sv: "Sushi", he: "סושי", tr: "Suşi" },
  τρούφα: { el: "Τρούφα", en: "Truffle", de: "Trüffel", it: "Tartufo", sv: "Tryffel", he: "כמהין", tr: "Trüf" },

  // --- All remaining tags present in the menu data ---
  αλμυρό: { el: "Αλμυρό", en: "Salty", de: "Salzig", it: "Salato", sv: "Salt", he: "מלוח", tr: "Tuzlu" },
  ανθισμένο: { el: "Ανθισμένο", en: "Floral", de: "Blumig", it: "Floreale", sv: "Blommig", he: "פרחוני", tr: "Çiçeksi" },
  άπαχο: { el: "Άπαχο", en: "Lean", de: "Mager", it: "Magro", sv: "Magert", he: "רזה", tr: "Yağsız" },
  απλό: { el: "Απλό", en: "Simple", de: "Einfach", it: "Semplice", sv: "Enkel", he: "פשוט", tr: "Sade" },
  αρωματικό: { el: "Αρωματικό", en: "Aromatic", de: "Aromatisch", it: "Aromatico", sv: "Aromatisk", he: "ארומטי", tr: "Aromatik" },
  αφρώδες: { el: "Αφρώδες", en: "Sparkling", de: "Sprudelnd", it: "Frizzante", sv: "Mousserande", he: "מבעבע", tr: "Köpüklü" },
  "βαθύ άρωμα": { el: "Βαθύ άρωμα", en: "Deep aroma", de: "Tiefes Aroma", it: "Aroma intenso", sv: "Djup arom", he: "ארומה עמוקה", tr: "Derin aroma" },
  "βαθύ γεύση": { el: "Βαθιά γεύση", en: "Deep flavour", de: "Tiefer Geschmack", it: "Sapore intenso", sv: "Djup smak", he: "טעם עמוק", tr: "Derin lezzet" },
  βασικό: { el: "Βασικό", en: "Basic", de: "Basis", it: "Base", sv: "Basic", he: "בסיסי", tr: "Temel" },
  βότανα: { el: "Βότανα", en: "Herbal", de: "Kräuter", it: "Erbe", sv: "Örter", he: "עשבי תיבול", tr: "Bitkisel" },
  βουτυράτο: { el: "Βουτυράτο", en: "Buttery", de: "Butterig", it: "Burroso", sv: "Smörig", he: "חמאתי", tr: "Tereyağımsı" },
  γαλλικό: { el: "Γαλλικό", en: "French", de: "Französisch", it: "Francese", sv: "Franskt", he: "צרפתי", tr: "Fransız" },
  γεμάτο: { el: "Γεμάτο", en: "Full-bodied", de: "Vollmundig", it: "Corposo", sv: "Fyllig", he: "מלא גוף", tr: "Dolgun" },
  γήινο: { el: "Γήινο", en: "Earthy", de: "Erdig", it: "Terroso", sv: "Jordig", he: "אדמתי", tr: "Topraksı" },
  γλυκό: { el: "Γλυκό", en: "Sweet", de: "Süß", it: "Dolce", sv: "Söt", he: "מתוק", tr: "Tatlı" },
  γλυκόπικρο: { el: "Γλυκόπικρο", en: "Bittersweet", de: "Bittersüß", it: "Dolceamaro", sv: "Bitterljuv", he: "מתוק-מריר", tr: "Tatlı-buruk" },
  δυνατό: { el: "Δυνατό", en: "Strong", de: "Stark", it: "Forte", sv: "Stark", he: "חזק", tr: "Sert" },
  ελληνικό: { el: "Ελληνικό", en: "Greek", de: "Griechisch", it: "Greco", sv: "Grekiskt", he: "יווני", tr: "Yunan" },
  έντονο: { el: "Έντονο", en: "Intense", de: "Intensiv", it: "Intenso", sv: "Intensiv", he: "עוצמתי", tr: "Yoğun" },
  εξωτικό: { el: "Εξωτικό", en: "Exotic", de: "Exotisch", it: "Esotico", sv: "Exotisk", he: "אקזוטי", tr: "Egzotik" },
  επίμονο: { el: "Επίμονο", en: "Lingering", de: "Anhaltend", it: "Persistente", sv: "Långvarig", he: "מתמשך", tr: "Kalıcı" },
  εσπεριδοειδές: { el: "Εσπεριδοειδές", en: "Citrus", de: "Zitrus", it: "Agrumato", sv: "Citrus", he: "הדרים", tr: "Narenciye" },
  ζεστό: { el: "Ζεστό", en: "Warm", de: "Warm", it: "Caldo", sv: "Varm", he: "חם", tr: "Sıcak" },
  ζουμερό: { el: "Ζουμερό", en: "Juicy", de: "Saftig", it: "Succoso", sv: "Saftig", he: "עסיסי", tr: "Sulu" },
  ημίγλυκο: { el: "Ημίγλυκο", en: "Semi-sweet", de: "Halbsüß", it: "Amabile", sv: "Halvsöt", he: "חצי מתוק", tr: "Yarı tatlı" },
  ημίξηρο: { el: "Ημίξηρο", en: "Semi-dry", de: "Halbtrocken", it: "Semisecco", sv: "Halvtorr", he: "חצי יבש", tr: "Yarı sek" },
  θαλασσινό: { el: "Θαλασσινό", en: "Seafood", de: "Meeresfrüchte", it: "Di mare", sv: "Skaldjur", he: "פירות ים", tr: "Deniz ürünlü" },
  θαλάσσιο: { el: "Θαλάσσιο", en: "Marine", de: "Maritim", it: "Marino", sv: "Marin", he: "ימי", tr: "Deniz esintili" },
  ιαπωνικό: { el: "Ιαπωνικό", en: "Japanese", de: "Japanisch", it: "Giapponese", sv: "Japanskt", he: "יפני", tr: "Japon" },
  καθαρό: { el: "Καθαρό", en: "Clean", de: "Klar", it: "Pulito", sv: "Ren", he: "נקי", tr: "Temiz" },
  καπνιστό: { el: "Καπνιστό", en: "Smoky", de: "Rauchig", it: "Affumicato", sv: "Rökig", he: "מעושן", tr: "İsli" },
  καφέ: { el: "Καφέ", en: "Coffee", de: "Kaffee", it: "Caffè", sv: "Kaffe", he: "קפה", tr: "Kahve" },
  κλασικό: { el: "Κλασικό", en: "Classic", de: "Klassisch", it: "Classico", sv: "Klassisk", he: "קלאסי", tr: "Klasik" },
  κοινωνικό: { el: "Κοινωνικό", en: "Social", de: "Gesellig", it: "Conviviale", sv: "Social", he: "חברתי", tr: "Paylaşımlık" },
  κρεμώδες: { el: "Κρεμώδες", en: "Creamy", de: "Cremig", it: "Cremoso", sv: "Krämig", he: "קרמי", tr: "Kremamsı" },
  λεπτό: { el: "Λεπτό", en: "Delicate", de: "Fein", it: "Delicato", sv: "Delikat", he: "עדין", tr: "Zarif" },
  λουλουδάτο: { el: "Λουλουδάτο", en: "Flowery", de: "Blumig", it: "Floreale", sv: "Blommig", he: "פרחוני", tr: "Çiçeksi" },
  μέντα: { el: "Μέντα", en: "Mint", de: "Minze", it: "Menta", sv: "Mynta", he: "נענע", tr: "Nane" },
  μεσογειακό: { el: "Μεσογειακό", en: "Mediterranean", de: "Mediterran", it: "Mediterraneo", sv: "Medelhavs", he: "ים-תיכוני", tr: "Akdeniz" },
  μεταλλικό: { el: "Μεταλλικό", en: "Mineral", de: "Mineralisch", it: "Minerale", sv: "Mineralisk", he: "מינרלי", tr: "Mineralli" },
  μούρα: { el: "Μούρα", en: "Berries", de: "Beeren", it: "Frutti di bosco", sv: "Bär", he: "פירות יער", tr: "Orman meyveleri" },
  νησιώτικο: { el: "Νησιώτικο", en: "Island", de: "Insel", it: "Isolano", sv: "Ö-karaktär", he: "מהאיים", tr: "Ada karakterli" },
  ξηρό: { el: "Ξηρό", en: "Dry", de: "Trocken", it: "Secco", sv: "Torr", he: "יבש", tr: "Sek" },
  ουδέτερο: { el: "Ουδέτερο", en: "Neutral", de: "Neutral", it: "Neutro", sv: "Neutral", he: "ניטרלי", tr: "Nötr" },
  πικάντικο: { el: "Πικάντικο", en: "Spicy", de: "Würzig", it: "Piccante", sv: "Kryddig", he: "פיקנטי", tr: "Baharatlı" },
  πικρό: { el: "Πικρό", en: "Bitter", de: "Bitter", it: "Amaro", sv: "Bitter", he: "מריר", tr: "Acı" },
  πλούσιο: { el: "Πλούσιο", en: "Rich", de: "Reichhaltig", it: "Ricco", sv: "Rik", he: "עשיר", tr: "Zengin" },
  ποικιλία: { el: "Ποικιλία", en: "Variety", de: "Auswahl", it: "Varietà", sv: "Variation", he: "מגוון", tr: "Çeşitli" },
  πολύπλοκο: { el: "Πολύπλοκο", en: "Complex", de: "Komplex", it: "Complesso", sv: "Komplex", he: "מורכב", tr: "Kompleks" },
  πολυτελές: { el: "Πολυτελές", en: "Luxurious", de: "Luxuriös", it: "Lussuoso", sv: "Lyxig", he: "יוקרתי", tr: "Lüks" },
  Προβηγκία: { el: "Προβηγκία", en: "Provence", de: "Provence", it: "Provenza", sv: "Provence", he: "פרובאנס", tr: "Provence" },
  σιταρένιο: { el: "Σιταρένιο", en: "Wheat", de: "Weizen", it: "Di grano", sv: "Vete", he: "חיטה", tr: "Buğday" },
  σοκολάτα: { el: "Σοκολάτα", en: "Chocolate", de: "Schokolade", it: "Cioccolato", sv: "Choklad", he: "שוקולד", tr: "Çikolata" },
  σύνθετο: { el: "Σύνθετο", en: "Layered", de: "Vielschichtig", it: "Articolato", sv: "Sammansatt", he: "רב-שכבתי", tr: "Katmanlı" },
  τανικό: { el: "Τανικό", en: "Tannic", de: "Tanninreich", it: "Tannico", sv: "Tanninrik", he: "טאני", tr: "Tanenli" },
  τραγανό: { el: "Τραγανό", en: "Crispy", de: "Knusprig", it: "Croccante", sv: "Krispig", he: "פריך", tr: "Çıtır" },
  τροπικό: { el: "Τροπικό", en: "Tropical", de: "Tropisch", it: "Tropicale", sv: "Tropisk", he: "טרופי", tr: "Tropikal" },
  φρέσκο: { el: "Φρέσκο", en: "Fresh", de: "Frisch", it: "Fresco", sv: "Färsk", he: "טרי", tr: "Taze" },
  φρουτώδες: { el: "Φρουτώδες", en: "Fruity", de: "Fruchtig", it: "Fruttato", sv: "Fruktig", he: "פירותי", tr: "Meyvemsi" },
  χορτοφαγικό: { el: "Χορτοφαγικό", en: "Vegetarian", de: "Vegetarisch", it: "Vegetariano", sv: "Vegetarisk", he: "צמחוני", tr: "Vejetaryen" },
  "alcohol-free": { el: "Χωρίς αλκοόλ", en: "Alcohol-free", de: "Alkoholfrei", it: "Analcolico", sv: "Alkoholfri", he: "ללא אלכוהול", tr: "Alkolsüz" },
  "comfort food": { el: "Comfort food", en: "Comfort food", de: "Soulfood", it: "Comfort food", sv: "Comfort food", he: "אוכל מנחם", tr: "Comfort food" },
  fermented: { el: "Ζυμωμένο", en: "Fermented", de: "Fermentiert", it: "Fermentato", sv: "Fermenterad", he: "מותסס", tr: "Fermente" },
  healthy: { el: "Υγιεινό", en: "Healthy", de: "Gesund", it: "Sano", sv: "Hälsosam", he: "בריא", tr: "Sağlıklı" },
  indulgent: { el: "Απολαυστικό", en: "Indulgent", de: "Genussvoll", it: "Goloso", sv: "Frossig", he: "מפנק", tr: "Şımartıcı" },
  lounge: { el: "Lounge", en: "Lounge", de: "Lounge", it: "Lounge", sv: "Lounge", he: "לאונג'", tr: "Lounge" },
  signature: { el: "Signature", en: "Signature", de: "Signature", it: "Signature", sv: "Signatur", he: "סיגנצ'ר", tr: "İmza" },
  umami: { el: "Umami", en: "Umami", de: "Umami", it: "Umami", sv: "Umami", he: "אומאמי", tr: "Umami" },
  vegan: { el: "Vegan", en: "Vegan", de: "Vegan", it: "Vegano", sv: "Vegansk", he: "טבעוני", tr: "Vegan" },
  "vegan-friendly": { el: "Vegan-friendly", en: "Vegan-friendly", de: "Vegan-freundlich", it: "Adatto ai vegani", sv: "Veganvänlig", he: "ידידותי לטבעונים", tr: "Vegan dostu" },
};

/** Translate a Greek tag token to the active language, falling back to the token. */
export function translateTag(tag: string, lang: Lang): string {
  const translations = TAG_TRANSLATIONS[tag];
  if (lang === "fr" || lang === "ru") {
    const localized = tagTranslationsFrRu[tag as keyof typeof tagTranslationsFrRu];
    return localized?.[lang] ?? translations?.en ?? tag;
  }
  return translations?.[lang] ?? tag;
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
  fr: {
    suggest: (name, price, desc) => `Bien sûr ! Je vous conseille ${name} (${price} €), ${desc}. Qu’en pensez-vous ?`,
    also: (list) => ` Vous pourriez également apprécier : ${list}.`,
    fallback: "Désolé, je ne suis pas certain de ce que vous recherchez. Préférez-vous des sushis, des nouilles, un burger, un cocktail ou une chicha ? Dites-moi ce que vous aimez et je vous proposerai quelque chose !",
  },
  ru: {
    suggest: (name, price, desc) => `Конечно! Рекомендую ${name} (${price} €), ${desc}. Как вам?`,
    also: (list) => ` Вам также могут понравиться: ${list}.`,
    fallback: "Извините, я не совсем понял, что вы ищете. Вы предпочитаете суши, лапшу, бургеры, коктейли или кальян? Расскажите, что вам нравится, и я что-нибудь порекомендую!",
  },
  he: {
    suggest: (name, price, desc) =>
      `בשמחה! אני ממליץ לנסות את ${name} (${price}€), שהוא ${desc}. איך זה נשמע?`,
    also: (list) => ` אפשר לנסות גם: ${list}.`,
    fallback:
      "סליחה, אני לא בטוח מה בדיוק אתם מחפשים. תעדיפו סושי, נודלס, המבורגרים, קוקטיילים או נרגילה? ספרו לי מה אתם אוהבים ואציע משהו מיוחד!",
  },
  tr: {
    suggest: (name, price, desc) =>
      `Tabii ki! Size ${name} (${price}€) öneririm; ${desc}. Kulağa nasıl geliyor?`,
    also: (list) => ` Şunları da deneyebilirsiniz: ${list}.`,
    fallback:
      "Üzgünüm, tam olarak ne aradığınızdan emin değilim. Suşi, noodle, burger, kokteyl mi yoksa nargile mi tercih edersiniz? Bana nelerden hoşlandığınızı söyleyin, size özel bir şey önereyim!",
  },
};
