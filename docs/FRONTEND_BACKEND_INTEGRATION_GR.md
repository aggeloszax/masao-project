# Masao MVP - Τεκμηρίωση Σύνδεσης Frontend με Backend

**Ημερομηνία:** 2026-06-03
**Κατάσταση:** Development
**Στόχος:** Να εξηγήσει τι έχει γίνει ώστε το Next.js frontend να μιλάει με το FastAPI/Supabase backend για το AI restaurant chatbot.

---

## 1. Τι υλοποιήθηκε

Το chat του frontend δεν απαντάει πλέον τοπικά από το `menu-mock.json`. Πλέον στέλνει HTTP request στο FastAPI endpoint `POST /api/chat`, μαζί με τα στοιχεία που χρειάζεται το backend για να ανοίξει/συνεχίσει σωστή συνομιλία ανά τραπέζι και συσκευή.

Το menu display της σελίδας παραμένει προσωρινά static από `frontend/src/data/menu-mock.json`. Αυτό είναι συνειδητή επιλογή για το MVP: πρώτα δένουμε το chat με backend, μετά περνάμε όλο το menu page σε DB-driven endpoint.

---

## 2. Νέα Frontend Αρχεία

### `frontend/src/lib/chat-api.ts`

Αυτό είναι το νέο API client layer.

Κάνει:

- Διαβάζει το backend URL από `NEXT_PUBLIC_API_BASE_URL`.
- Δημιουργεί/κρατάει anonymous `device_id` στο LocalStorage.
- Διαβάζει `table_number` από το URL query string.
- Στέλνει request στο backend `/api/chat`.
- Επιστρέφει typed response για να το κάνει render το `Chat.tsx`.

Παράδειγμα URL τραπεζιού:

```text
http://localhost:3000/?table=12
```

Αν δεν υπάρχει `table`, το frontend στέλνει default `table_number = 1`.

---

## 3. Αλλαγές στο `Chat.tsx`

Το παλιό local chatbot logic αφαιρέθηκε:

```text
findMatches()
buildReply()
```

Το νέο flow είναι:

```text
User γράφει μήνυμα
      │
      ▼
Chat.tsx παίρνει:
- restaurant_slug = "masao"
- table_number από URL
- device_id από LocalStorage
- language_code από LanguageContext
      │
      ▼
POST /api/chat
      │
      ▼
Backend αποθηκεύει session/messages και επιστρέφει messages[]
      │
      ▼
Chat.tsx κάνει render τα returned messages σαν chat bubbles
```

Το request που στέλνει το frontend είναι:

```json
{
  "restaurant_slug": "masao",
  "table_number": 12,
  "device_id": "generated-localstorage-id",
  "user_message": "θέλω κάτι καυτερό",
  "language_code": "el"
}
```

---

## 4. Γλώσσες

Το frontend ήδη έχει `LanguageContext`. Το chat πλέον στέλνει το ενεργό `lang` ως `language_code`.

Υποστηριζόμενες τιμές:

```text
el, en, de, it, sv
```

Το backend χρησιμοποιεί αυτό το `language_code` για να κάνει `LEFT JOIN` στα translation tables:

- `menu_item_translations`
- `menu_category_translations`

Αν λείπει translation, κάνει fallback στα canonical menu fields.

---

## 5. Supabase / Database

Το schema έχει εφαρμοστεί στο Supabase project:

```text
nycfqostjdjaynstaloo
```

Το cleanup migration για αφαίρεση Hebrew (`backend/sql/003_remove_hebrew_translations.sql`) έχει επίσης εφαρμοστεί στο Supabase. Τα constraints των translation tables δέχονται πλέον μόνο:

```text
el, en, de, it, sv
```

Τα production tables είναι:

```text
menu_categories
menu_items
menu_category_translations
menu_item_translations
chat_sessions
chat_messages
```

Το full menu seed έχει μπει στη βάση και έχει γίνει verification. Το καθαρό SQL αρχείο, χωρίς Hebrew, είναι εδώ:

```text
backend/sql/002_seed_full_menu_from_frontend.sql
```

Verified counts στο Supabase:

```text
menu_categories: 24
menu_items: 130
menu_category_translations: 120
menu_item_translations: 650
hebrew_item_translations: 0
```

Αν αλλάξει το `frontend/src/data/menu-mock.json`, πρέπει να ξανατρέξει ο generator και να εφαρμοστεί ξανά το seed:

```bash
python backend/scripts/generate_menu_seed_sql.py
```

---

## 6. Environment Variables

Στο frontend χρειάζεται:

```text
frontend/.env.local
```

με:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Υπάρχει template:

```text
frontend/.env.example
```

Στο backend χρειάζεται:

```text
backend/.env
```

με Supabase database URL:

```text
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
INTERNAL_API_KEY=change-this
ENVIRONMENT=development
```

---

## 7. Πώς το δοκιμάζουμε τοπικά

### Backend

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### Frontend

```bash
cd frontend
npm run dev
```

Άνοιγμα με table number:

```text
http://localhost:3000/?table=12
```

Μετά άνοιξε το chat και γράψε:

```text
θέλω κάτι καυτερό με γαρίδα
```

Αν η βάση έχει seed data, το backend θα επιστρέψει recommendation. Αν η βάση είναι άδεια, θα γυρίσει fallback ή database-dependent αποτέλεσμα.

---

## 8. Τι δεν έχει γίνει ακόμα

Δεν έχει γίνει ακόμα DB-driven menu page.

Το frontend menu εξακολουθεί να διαβάζει:

```text
frontend/src/data/menu-mock.json
```

Για production θα πρέπει να προστεθεί backend endpoint:

```text
GET /api/menu?language_code=el
```

και μετά το `MenuApp` να φορτώνει menu groups από Supabase αντί από mock JSON.

---

## 9. Verification που έγινε

Πέρασαν:

```text
python -m compileall backend
backend python -m pytest tests -v
frontend npm run lint
frontend npm run build
GET http://localhost:8000/health -> 200 ok masao
POST http://localhost:8000/api/chat -> recommendation: Shrimp Tempura
```

Το frontend lint πέρασε μετά τη διόρθωση των React 19 setState-in-effect θεμάτων.

Έγινε πραγματικό backend API test με seeded Supabase menu. Το προσωρινό test chat session για `codex-test-device-001` καθαρίστηκε από τα `chat_sessions` / `chat_messages`.

Εγκαταστάθηκαν τα frontend dependencies με:

```bash
npm install
```

Υπάρχουν 2 moderate npm audit findings. Δεν εφαρμόστηκε `npm audit fix --force`, γιατί μπορεί να αλλάξει dependency versions με breaking changes.

---

## 10. Επόμενη σωστή κίνηση

Η επόμενη σωστή κίνηση δεν είναι πια το seed. Αυτό έχει ολοκληρωθεί. Το επόμενο βήμα είναι να συνδεθεί και το menu page με Supabase αντί για το mock JSON:

```text
Next.js MenuApp -> FastAPI GET /api/menu -> Supabase menu_items/translations -> rendered menu groups
```

Μετά, μπορεί να μπει LLM layer πάνω από το deterministic recommendation logic, με αυστηρό JSON output και fallback στα ίδια menu rows.
