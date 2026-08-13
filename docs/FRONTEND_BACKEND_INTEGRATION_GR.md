# Masao MVP - Τεκμηρίωση Σύνδεσης Frontend με Backend

**Ημερομηνία:** 2026-06-06
**Κατάσταση:** Development
**Στόχος:** Να εξηγήσει τι έχει γίνει ώστε το Next.js frontend να μιλάει με το FastAPI/Supabase backend για το AI restaurant chatbot.

---

## 1. Τι υλοποιήθηκε

Το chat του frontend δεν απαντάει πλέον τοπικά από το `menu-mock.json`. Πλέον στέλνει HTTP request στο FastAPI endpoint `POST /api/chat`, μαζί με τα στοιχεία που χρειάζεται το backend για να ανοίξει/συνεχίσει σωστή συνομιλία ανά τραπέζι και συσκευή.

Το menu display της σελίδας παραμένει προσωρινά static από `frontend/src/data/menu-mock.json`, αλλά το backend endpoint για DB-driven menu είναι πλέον έτοιμο: `GET /api/menu`. Ο συνεργάτης στο frontend μπορεί να το συνδέσει χωρίς να χρειαστεί νέο backend contract.

Υπάρχει επίσης protected backend admin API για αλλαγές στο menu με `X-API-Key`:

```text
POST  /api/admin/menu/categories
PATCH /api/admin/menu/categories/{category_id}
PUT   /api/admin/menu/categories/{category_id}/translations/{language_code}
POST  /api/admin/menu/items
PATCH /api/admin/menu/items/{item_id}
PUT   /api/admin/menu/items/{item_id}/translations/{language_code}
```

Το `POST /api/chat` έχει πλέον rate limiting ανά `restaurant_slug`, `table_number` και anonymous `device_id`. Αν ο πελάτης στείλει πολλά μηνύματα πολύ γρήγορα, το backend γυρίζει:

```text
429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 60
```

Το frontend μπορεί να δείξει ένα ήπιο μήνυμα τύπου "Περίμενε λίγο πριν στείλεις ξανά".

Για production, το rate limiting δεν πρέπει να μείνει σε local memory. Το backend υποστηρίζει Redis-backed limiter:

```text
RATE_LIMIT_BACKEND=redis
REDIS_URL=rediss://...
RATE_LIMIT_FAIL_CLOSED=true
```

Έτσι όλοι οι FastAPI workers μοιράζονται το ίδιο limit state. Το `memory` backend μένει μόνο για local development.

Προστέθηκε και Cloudflare edge rate limiting config:

```text
infra/cloudflare/
```

Default rule:

```text
POST /api/chat
60 requests / 60 seconds
key: cf.colo.id + ip.src
response: 429 application/json
```

Αυτό κόβει abuse πριν φτάσει στο FastAPI. Αν το frontend λάβει `429`, δεν χρειάζεται να ξέρει αν ήρθε από Cloudflare ή από FastAPI. Δείχνει το ίδιο μήνυμα αναμονής.

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
el, en, de, it, sv, fr, ru, he, tr
```

Τα εβραϊκά (`he`) είναι RTL γλώσσα: το frontend γυρίζει αυτόματα το layout σε
`dir="rtl"` μέσω του `isRtl()` στο `frontend/src/i18n/config.ts`. Τα τουρκικά
(`tr`) είναι LTR όπως οι υπόλοιπες γλώσσες.

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

Το παλιό cleanup migration αφαίρεσης Hebrew (`backend/sql/003_remove_hebrew_translations.sql`) είναι πλέον κενό (superseded no-op). Σε υπάρχουσες βάσεις που δεν έχουν τις νέες γλώσσες τρέχουν τα migrations `backend/sql/005_add_hebrew_translations.sql`, `backend/sql/006_add_french_russian_languages.sql` και `backend/sql/007_add_turkish_language.sql`. Το 007 είναι αυτόνομο: περιέχει και τα constraints και τα translation rows με `ON CONFLICT DO NOTHING`, ώστε να μη χρειάζεται re-run του 002 seed και να μην πειράζονται δεδομένα που έχουν αλλάξει μέσω admin API. Τα constraints των translation tables δέχονται πλέον:

```text
el, en, de, it, sv, fr, ru, he, tr
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

Το full menu seed έχει μπει στη βάση και έχει γίνει verification. Το SQL αρχείο (7 γλώσσες, μαζί με Hebrew και Turkish) είναι εδώ:

```text
backend/sql/002_seed_full_menu_from_frontend.sql
```

Αναμενόμενα counts στο Supabase (130 items × 9 γλώσσες, 24 κατηγορίες × 9):

```text
menu_categories: 24
menu_items: 130
menu_category_translations: 216
menu_item_translations: 1170
hebrew_item_translations: 130
turkish_item_translations: 130
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

Δεν έχει γίνει ακόμα frontend wiring για DB-driven menu page.

Το frontend menu εξακολουθεί να διαβάζει:

```text
frontend/src/data/menu-mock.json
```

Το backend endpoint έχει πλέον προστεθεί:

```text
GET /api/menu?language_code=el
```

Επιστρέφει grouped response ανά category:

```text
restaurant_slug
language_code
total_categories
total_items
categories[] -> items[]
```

Verified backend result:

```text
GET /api/menu?language_code=en -> 200
total_categories: 24
total_items: 130
```

Το μόνο που μένει εδώ είναι το `MenuApp` να φορτώνει menu groups από αυτό το endpoint αντί από mock JSON.

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
POST /api/chat route-level rate limit test -> 429 on second request with test limiter
Redis rate limiter unit tests -> allow/block/fail-closed/fail-open passed
GET /api/menu?language_code=en -> 200, categories: 24, items: 130
PATCH /api/admin/menu/items/1 without X-API-Key -> 403
Cloudflare Terraform config added under infra/cloudflare/
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

Η επόμενη σωστή κίνηση δεν είναι πια backend για public menu. Το backend endpoint υπάρχει. Το επόμενο βήμα είναι frontend wiring:

```text
Next.js MenuApp -> FastAPI GET /api/menu -> Supabase menu_items/translations -> rendered menu groups
```

Μετά, μπορεί να μπει LLM layer πάνω από το deterministic recommendation logic, με αυστηρό JSON output και fallback στα ίδια menu rows.
