# Allergy Alerts — Backend Design

Date: 2026-07-10
Status: Implemented

## Goal

Ο πελάτης δηλώνει τις αλλεργίες του και το backend επιστρέφει alert σε κάθε
πιάτο του μενού που περιέχει αλλεργιογόνο από τη λίστα του. Το ίδιο σήμα
περνάει και στον AI σερβιτόρο ώστε να προειδοποιεί στις προτάσεις του.

## Constraints & decisions

- **Χωρίς λογαριασμούς**: οι πελάτες ταυτοποιούνται μόνο με το ανώνυμο
  `device_id` που ήδη χρησιμοποιεί το chat (`chat_sessions.device_id`).
  Το allergy profile κλειδώνει στο ίδιο id — μία εγγραφή ανά συσκευή.
- **Κανονικοποιημένα αλλεργιογόνα**: τα 14 αλλεργιογόνα της ΕΕ (Annex II,
  Reg. 1169/2011) ως σταθεροί κωδικοί (`gluten`, `crustaceans`, `eggs`,
  `fish`, `peanuts`, `soybeans`, `milk`, `nuts`, `celery`, `mustard`,
  `sesame`, `sulphites`, `lupin`, `molluscs`). Ελεύθερο κείμενο δεν
  γίνεται δεκτό — τα alerts πρέπει να είναι ντετερμινιστικά.
- **Alert, όχι φιλτράρισμα**: τα πιάτα με αλλεργιογόνο ΔΕΝ κρύβονται·
  επισημαίνονται με `allergen_alert=true` + `matched_allergens=[...]`.
  Την τελική απόφαση την παίρνει ο πελάτης με το προσωπικό.
- **Safety disclaimer**: τα seeded allergens ανά πιάτο προέρχονται από τις
  περιγραφές συστατικών (best effort) και ΠΡΕΠΕΙ να επαληθευτούν από το
  εστιατόριο. Πιάτο χωρίς δηλωμένα allergens σημαίνει «μη αξιολογημένο»,
  όχι «ασφαλές».

## Data model (migration `004_add_allergens.sql`)

- `menu_items.allergens text[] not null default '{}'` + GIN index.
- Νέος πίνακας:

```sql
customer_allergy_profiles (
    id serial primary key,
    device_id varchar(128) not null unique,
    allergens text[] not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
)
```

- Best-effort seed των `menu_items.allergens` με keyword matching πάνω στις
  αγγλικές περιγραφές συστατικών (π.χ. `shrimp|crab → crustaceans`,
  `salmon|tuna|sea bass|kanimi|masago → fish`, `mayo → eggs`,
  `cream cheese|parmesan → milk`, wines/beers → `sulphites` κ.λπ.).

## API surface

| Endpoint | Περιγραφή |
|---|---|
| `GET /api/allergens?language_code=el` | Κατάλογος 14 κωδικών + localized labels για το picker του frontend. |
| `PUT /api/profile/allergies` | Body `{device_id, allergens[]}` — upsert του προφίλ. Άδεια λίστα = καθαρισμός. |
| `GET /api/profile/allergies?device_id=…` | Τρέχον προφίλ (άδεια λίστα αν δεν υπάρχει). |
| `GET /api/menu?…&device_id=…` | Κάθε item αποκτά `allergens`, `matched_allergens`, `allergen_alert`. Χωρίς `device_id` τα alerts είναι απενεργά. |
| `POST /api/chat` | Τα `recommended_items` αποκτούν τα ίδια πεδία· ο LLM prompt ενημερώνεται για τις αλλεργίες του πελάτη. |

Admin: `POST/PATCH /api/admin/menu/items` δέχονται πλέον `allergens`
(validated κωδικούς) ώστε το εστιατόριο να διορθώνει τα δεδομένα.

## Components

- `api/schemas/allergy.py` — `AllergenCode` Literal, request/response models,
  κανονικοποίηση (dedup, lowercase, άγνωστοι κωδικοί → 422).
- `api/services/allergens.py` — registry: κωδικοί + labels ανά γλώσσα +
  `match_allergens(item_allergens, customer_allergens)` pure function.
- `api/services/allergy_service.py` — `get_profile`/`upsert_profile`
  (raw SQL, ίδιο pattern με τα υπόλοιπα services).
- `api/routers/allergy.py` — τα δύο endpoints προφίλ + `GET /allergens`.
- `menu_service` / `chat_service` / `llm_service` — αλλαγές annotation.

## LLM integration

Οι αλλεργίες μπαίνουν σε **τρίτο system block μετά το cached menu block**
ώστε να μη σπάει το prompt caching (persona + menu μένουν σταθερά ανά
γλώσσα). Ο κανόνας: ποτέ πρόταση πιάτου με δηλωμένο αλλεργιογόνο χωρίς
ρητή προειδοποίηση· παρότρυνση επιβεβαίωσης με το προσωπικό.

Στο deterministic fallback, κάθε πρόταση που περιέχει αλλεργιογόνο του
πελάτη παίρνει localized προειδοποίηση στο τέλος του reply.

## Testing

Unit tests χωρίς DB (ίδιο στυλ με τα υπάρχοντα): registry πληρότητα,
schema validation, menu annotation, fallback warning, admin allergens,
route-level tests με dependency overrides για τα profile endpoints.
