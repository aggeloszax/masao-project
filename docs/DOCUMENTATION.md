## Masao Restaurant Chatbot Backend — Technical Documentation

**Version:** 1.0.0
**Last updated:** 2026-06-03
**Author:** PlanAhead Engineering
**Status:** Development

---

### 1. Τι κάνει αυτό το εργαλείο (Plain Greek)

Το backend κρατάει το μενού του Masao, ανοίγει ξεχωριστή συνομιλία για κάθε κινητό και τραπέζι, και αποθηκεύει όλα τα μηνύματα της συνομιλίας. Όταν ο πελάτης γράφει τι θέλει, το API ψάχνει τα διαθέσιμα πιάτα και επιστρέφει μια πρόταση σε μορφή που το Next.js frontend μπορεί να εμφανίσει άμεσα σαν chat bubbles. Η βάση είναι σχεδιασμένη για Supabase/PostgreSQL και για πολλούς πελάτες που σκανάρουν το ίδιο QR τραπεζιού από διαφορετικά κινητά.

---

### 2. Architecture Overview

```text
Next.js client
     │
     │ POST /api/chat
     ▼
api/routers/chat.py
     │
     ▼
api/services/chat_service.py
     │
     ├── get/create active chat_sessions row
     ├── insert user chat_messages row
     ├── fetch available menu_items + menu_categories
     ├── choose menu recommendations
     └── insert assistant chat_messages row
     │
     ▼
Supabase PostgreSQL
     │
     ├── menu_categories
     ├── menu_items
     ├── menu_category_translations
     ├── menu_item_translations
     ├── chat_sessions
     └── chat_messages
```

---

### 3. Prerequisites & Installation

**Python version:** 3.11+

**Install dependencies:**

```bash
cd backend
pip install -r requirements.txt
```

**Environment variables (copy `.env.example` -> `.env` and fill in):**

```text
DATABASE_URL=          # PostgreSQL/Supabase async SQLAlchemy URL
INTERNAL_API_KEY=      # API key reserved for future internal/admin endpoints
ENVIRONMENT=           # development, staging, or production
```

For Supabase, use the pooled PostgreSQL connection string converted to SQLAlchemy async format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
```

`backend/.env` is intentionally gitignored and must never be committed. The committed `backend/.env.example` contains placeholders only.

---

### 4. How to Run

**Apply database schema in Supabase/PostgreSQL:**

```bash
psql "$DATABASE_URL" -f backend/sql/001_init_masao_schema.sql
psql "$DATABASE_URL" -f backend/sql/003_remove_hebrew_translations.sql  # only if old Hebrew-enabled schema exists
psql "$DATABASE_URL" -f backend/sql/002_seed_full_menu_from_frontend.sql
```

If an older schema with Hebrew (`he`) support was already applied, run this cleanup migration before applying the regenerated seed:

```bash
psql "$DATABASE_URL" -f backend/sql/003_remove_hebrew_translations.sql
```

If using the Supabase dashboard, paste the contents of:

```text
backend/sql/001_init_masao_schema.sql
backend/sql/003_remove_hebrew_translations.sql
backend/sql/002_seed_full_menu_from_frontend.sql
```

**Frontend environment for backend chat integration:**

```bash
cd frontend
copy .env.example .env.local
```

Then confirm:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**FastAPI server:**

```bash
cd backend
uvicorn api.main:app --reload --port 8000
# Swagger docs available at: http://localhost:8000/docs
```

**Dry run / config validation:**

```bash
cd backend
python main.py --input sql --dry-run
```

**Health check:**

```bash
curl http://localhost:8000/health
```

---

### 5. Input Data Requirements

#### `POST /api/chat` request body

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| restaurant_slug | str | Yes | Restaurant identifier expected by backend config | "masao" |
| table_number | int | Yes | Physical table number from QR route/query param | 12 |
| device_id | str | Yes | Anonymous client device id from Next.js LocalStorage | "device-018f9a2b" |
| user_message | str | Yes | Customer message | "θέλω κάτι καυτερό με γαρίδα" |
| language_code | str | No | Active frontend language; defaults to Greek | "el" |

**Accepted formats:** JSON over HTTP
**Minimum rows required:** Not applicable for chat request; the database needs at least one available `menu_items` row to recommend an item.
**Expected date format:** PostgreSQL stores timestamps as `timestamp with time zone`; API responses serialize datetimes as ISO 8601.

#### Menu database rows

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| category_id | int | Yes | FK to `menu_categories.id` | 1 |
| name | str | Yes | Menu item name | "Shrimp Tempura" |
| description | text | Yes | Customer-visible description | "Shrimp tempura, avocado..." |
| price | decimal | Yes | Price in EUR | 9.30 |
| tags | text[] | Yes | AI/recommendation labels | `{shrimp,spicy,crispy}` |
| is_available | bool | Yes | Whether item can be recommended | true |

---

### 6. Code Walkthrough — File by File

#### `backend/sql/001_init_masao_schema.sql`

**Purpose:** Creates the PostgreSQL schema for the Masao MVP.

**Main objects:** `menu_categories`, `menu_items`, `menu_category_translations`, `menu_item_translations`, `chat_sessions`, `chat_messages`.

**What it does:** Creates canonical menu tables, normalized translation tables, chat tables, and indexes for menu lookup and chat history.

**Why it works this way:** The app is single-restaurant for now, so there is no `restaurants` table. The frontend still sends `restaurant_slug` and the backend validates it against config, which keeps the API contract ready for a future multi-restaurant migration. Translations are normalized instead of stored as JSONB because production operations need constraints, indexed joins, and clean update history per language.

**Edge cases handled:**
- Duplicate migration execution -> `if not exists` and unique indexes avoid duplicate objects.
- Multiple devices at one table -> `device_id + table_number` identifies the active session.
- Inactive old sessions -> partial unique index only applies where `is_active = true`.

**Key logic explained:**

```sql
create unique index if not exists uq_chat_sessions_active_device_table
    on chat_sessions(device_id, table_number)
    where is_active = true;
```

This keeps one active chat per anonymous mobile device per physical table. Two customers at table 12 can have different `device_id` values and therefore different active sessions.

#### `backend/sql/002_seed_full_menu_from_frontend.sql`

**Purpose:** Imports the full frontend menu into PostgreSQL.

**What it does:** Inserts 24 categories, 130 menu items, category translations and 650 item translation rows generated from `frontend/src/data/menu-mock.json`.

**Why it works this way:** The frontend JSON is used only as a source file for a one-time/generated database import. The backend agent does not read frontend files at runtime; it reads from Supabase/PostgreSQL.

**Edge cases handled:**
- Re-running the seed -> `on conflict` updates categories, items and translations.
- Generated ids -> data joins by stable `external_id`, not by generated serial ids.
- Multilingual category labels -> category translations are stored separately from item translations.

#### `backend/scripts/generate_menu_seed_sql.py`

**Purpose:** Regenerates the full seed migration from the frontend mock menu.

**Main function: `main()`**
- **What it does:** Reads `frontend/src/data/menu-mock.json` and writes `backend/sql/002_seed_full_menu_from_frontend.sql`.
- **Why it works this way:** The import step is deterministic and auditable; changes to menu data can be regenerated without manually editing hundreds of SQL rows.
- **Edge cases handled:**
  - Single-language descriptions -> same text is used as fallback.
  - Greek base descriptions stored as `el` translations.
  - Category translation labels are de-duplicated by category/language.

#### `backend/database.py`

**Purpose:** Owns the async SQLAlchemy engine and session dependency.

**Main function: `get_db_session()`**

**What it does:** Opens an async DB session, yields it to FastAPI, commits on success, and rolls back on failure.

**Why it works this way:** The `/api/chat` endpoint performs several writes in one request: session creation, user message insert, assistant message insert. A per-request transaction keeps those operations consistent.

**Edge cases handled:**
- DB exception during request -> rollback and structured log entry.
- Application shutdown -> async engine is disposed by `close_database()`.

**Key logic explained:**

```python
async with AsyncSessionLocal() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Database session failed and was rolled back")
        raise
```

The session commits only after the endpoint finishes successfully. If a DB write fails, no partial chat turn is committed.

#### `backend/api/config.py`

**Purpose:** Loads YAML defaults and `.env` overrides.

**Main object: `settings`**

**What it does:** Reads `backend/config/settings.yaml`, loads `.env`, and exposes typed settings for database pool, CORS, restaurant slug and chat limits.

**Why it works this way:** CORS origins, pool size and restaurant slug stay configurable without code changes.

**Edge cases handled:**
- Missing YAML file -> empty config fallback.
- Missing `.env` -> local defaults still allow import and tests.

#### `backend/api/main.py`

**Purpose:** FastAPI application factory module.

**Main object: `app`**

**What it does:** Creates FastAPI, registers CORS middleware, includes `/api/chat`, and exposes `/health`.

**Why it works this way:** The Next.js frontend runs on localhost ports during development and Vercel in production; allowed origins live in config.

**Key logic explained:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    allow_credentials=False,
)
```

This explicitly allows Next.js development origins such as `http://localhost:3000` while avoiding `allow_origins=["*"]`.

#### `backend/api/schemas/chat.py`

**Purpose:** Pydantic request/response contracts for the Next.js client.

**Main models:** `ChatRequest`, `ChatResponse`, `ChatMessageResponse`, `MenuItemResponse`.

**What it does:** Validates the incoming JSON and serializes the response into frontend-friendly objects.

**Why it works this way:** The frontend can render `messages.map(...)` directly because every message has `id`, `session_id`, `role`, `content`, and `created_at`. The optional `language_code` lets the Next.js language selector request localized menu names/descriptions without changing endpoint path.

**Edge cases handled:**
- Blank strings -> rejected.
- Too-short `device_id` -> rejected.
- Invalid `table_number` -> rejected.

#### `backend/api/routers/chat.py`

**Purpose:** HTTP boundary for chat.

**Endpoint:** `POST /api/chat`

**What it expects:** `restaurant_slug`, `table_number`, `device_id`, `user_message`, optional `language_code`.

**What it returns:** Session id, assistant message, all recent messages, and recommended menu items.

**Business logic it triggers:** Delegates session/history/menu/recommendation work to `ChatService`.

**Errors it can return:**
- `422` if `restaurant_slug` is unsupported.
- `500` if database operations fail.

#### `backend/api/services/chat_service.py`

**Purpose:** Business logic for chat persistence and menu recommendation.

**Main function: `handle_chat(request)`**

**What it does:** Creates or reuses an active chat session, stores the user message, fetches localized menu items for the requested `language_code`, generates a deterministic recommendation, stores the assistant message, and returns structured JSON.

**Why it works this way:** The MVP does not require an LLM dependency to prove the backend/frontend contract. It uses menu tags and descriptions first, which keeps responses predictable and auditable.

**Edge cases handled:**
- Unknown restaurant slug -> raises `ValueError`.
- Empty/low-signal user message -> fallback assistant reply.
- Unavailable menu item -> excluded from recommendations.
- Long history -> latest `chat_history_limit` messages are returned in chronological order.
- Missing translation row -> falls back to canonical `menu_items` / `menu_categories` fields.

**Key logic explained:**

```python
# Επιλογή πιάτων με βάση overlap σε όνομα, περιγραφή, κατηγορία και AI tags.
scored = [
    (item, score_menu_item(item, terms))
    for item in menu_items
    if item.is_available
]
ranked = sorted(
    ((item, score) for item, score in scored if score > 0),
    key=lambda pair: (-pair[1], pair[0].price, pair[0].name),
)
```

This ranks available menu items by text/tag overlap, then by lower price and stable name ordering. It is intentionally deterministic so test failures are meaningful.

**Business formulas used:**

No financial formulas are used in this backend. Recommendation scoring is:

```text
Menu Match Score = count(search_terms that appear in item name + description + category + tags)
```

Exact Python code:

```python
return sum(1 for term in terms if term and term in haystack)
```

#### `backend/main.py`

**Purpose:** Maintenance CLI with required `--dry-run` support.

**Main function: `main()`**

**What it does:** Validates config and migration input folder, then logs a batch summary.

**Why it works this way:** It gives the backend a lightweight operational entry point without mixing CLI behavior into FastAPI runtime.

---

### 7. API Reference

#### POST /api/chat

**Purpose:** Handle one customer message and return an assistant response for chat bubble rendering.

**Request body:**

```json
{
  "restaurant_slug": "masao",
  "table_number": 12,
  "device_id": "device-018f9a2b",
  "user_message": "θέλω κάτι καυτερό με γαρίδα",
  "language_code": "el"
}
```

**Response:**

```json
{
  "session_id": "2b4c0b7a-0b7a-4c6d-9af6-fbb2ab3d93f1",
  "restaurant_slug": "masao",
  "table_number": 12,
  "device_id": "device-018f9a2b",
  "language_code": "el",
  "assistant_message": {
    "id": 2,
    "session_id": "2b4c0b7a-0b7a-4c6d-9af6-fbb2ab3d93f1",
    "role": "assistant",
    "content": "Σου προτείνω το Shrimp Tempura (9.30€). Shrimp tempura, avocado, spicy mayo and red masago.",
    "created_at": "2026-06-02T20:55:00Z"
  },
  "messages": [
    {
      "id": 1,
      "session_id": "2b4c0b7a-0b7a-4c6d-9af6-fbb2ab3d93f1",
      "role": "user",
      "content": "θέλω κάτι καυτερό με γαρίδα",
      "created_at": "2026-06-02T20:54:59Z"
    },
    {
      "id": 2,
      "session_id": "2b4c0b7a-0b7a-4c6d-9af6-fbb2ab3d93f1",
      "role": "assistant",
      "content": "Σου προτείνω το Shrimp Tempura (9.30€). Shrimp tempura, avocado, spicy mayo and red masago.",
      "created_at": "2026-06-02T20:55:00Z"
    }
  ],
  "recommended_items": [
    {
      "id": 3,
      "external_id": "UR007",
      "category": "Sushi",
      "name": "Shrimp Tempura",
      "description": "Shrimp tempura, avocado, spicy mayo and red masago.",
      "price": 9.3,
      "tags": ["shrimp", "spicy", "crispy", "umami"],
      "is_available": true,
      "language_code": "el"
    }
  ]
}
```

**Errors:**

```text
422 Unprocessable Entity - invalid body or unsupported restaurant_slug
500 Internal Server Error - database unavailable or write failed
```

**Next.js binding:**

The frontend chat sends this request from `frontend/src/lib/chat-api.ts`. It creates a stable anonymous `device_id` in LocalStorage, reads the table number from `?table=12`, and sends the active `LanguageContext` language as `language_code`.

#### GET /health

**Purpose:** Deployment and uptime health check.

**Response:**

```json
{
  "status": "ok",
  "service": "Masao Restaurant Chatbot API",
  "restaurant": "masao"
}
```

---

### 8. Output Files

| File | Location | Format | Description |
|------|----------|--------|-------------|
| 001_init_masao_schema.sql | backend/sql/ | SQL | Supabase/PostgreSQL schema |
| 002_seed_full_menu_from_frontend.sql | backend/sql/ | SQL | Full menu seed generated from frontend JSON |
| 003_remove_hebrew_translations.sql | backend/sql/ | SQL | Cleanup migration that removes old Hebrew rows and constraints |
| generate_menu_seed_sql.py | backend/scripts/ | Python | Deterministic SQL seed generator |
| pipeline/runtime logs | backend/logs/ | Text | Future operational logs; gitignored |
| API responses | HTTP JSON | JSON | Chat messages and recommendations for Next.js |
| DOCUMENTATION.md | docs/ | Markdown | Technical documentation |

---

### 9. Configuration Reference (config/settings.yaml)

| Parameter | Default | Description |
|-----------|---------|-------------|
| app.name | Masao Restaurant Chatbot API | FastAPI service name |
| app.version | 1.0.0 | API version shown in docs |
| app.environment | development | Runtime environment label |
| restaurant.slug | masao | Only accepted restaurant slug for MVP |
| restaurant.display_name | Masao | Human-readable restaurant name |
| database.url | postgresql+asyncpg://postgres:postgres@localhost:5432/masao | Local async database URL; override with `.env` |
| database.pool_size | 10 | Base async DB pool size |
| database.max_overflow | 20 | Extra temporary DB connections under load |
| database.pool_timeout_seconds | 30 | Seconds to wait for a pooled connection |
| cors.allowed_origins | localhost and Vercel Masao URL | Frontend origins allowed by browser CORS |
| cors.allowed_methods | GET, POST, OPTIONS | HTTP methods accepted by CORS |
| chat.history_limit | 20 | Maximum recent messages returned per response |
| chat.max_user_message_chars | 1000 | Pydantic max length for user messages |
| chat.default_table_number | 1 | Reserved default for future QR helpers |

---

### 10. Error Handling Reference

| Error | Location | Cause | What happens |
|-------|----------|-------|--------------|
| ValidationError | schemas/chat.py | Missing/blank field, short device id, invalid table number | FastAPI returns 422 |
| ValueError | services/chat_service.py | Unsupported `restaurant_slug` | Router returns 422 with detail |
| SQLAlchemyError | services/chat_service.py | DB unavailable, failed insert/select | Router returns 500 and logs exception |
| Exception during DB dependency | database.py | Any unhandled request DB failure | Transaction rollback, exception logged, error re-raised |
| FileNotFoundError | main.py | CLI input folder missing | CLI exits loudly with descriptive error |

---

### 11. Testing

**Run all tests:**

```bash
cd backend
pytest tests/ -v
```

**Run with coverage:**

```bash
cd backend
pytest tests/ --cov=api --cov-report=term-missing
```

**Test files:**

| File | What it tests |
|------|---------------|
| tests/test_chat_service.py | Latin/Greek tokenization, recommendation ranking, unavailable items, fallback reply |
| tests/test_chat_schema.py | Next.js payload validation, language_code support and invalid request cases |

Current verification on 2026-06-03:

```text
python -m compileall backend passed
python -m pytest tests -v passed: 10 tests
frontend npm run lint passed
frontend npm run build passed
Supabase project nycfqostjdjaynstaloo contains:
  menu_categories=24
  menu_items=130
  menu_category_translations=120
  menu_item_translations=650
  hebrew_item_translations=0
backend/.env DATABASE_URL uses postgresql+asyncpg:// and connected successfully
GET /health returned 200 ok masao
POST /api/chat returned Shrimp Tempura for a spicy shrimp request
Temporary codex-test-device-001 chat data was cleaned from Supabase
```

---

### 12. Deployment

**Local development:**

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

**Supabase migration:**

Use the SQL editor or Supabase migration tooling to apply:

```text
backend/sql/001_init_masao_schema.sql
backend/sql/002_seed_full_menu_from_frontend.sql
backend/sql/003_remove_hebrew_translations.sql
```

**Staging (Render):**

Connect GitHub repo -> Render auto-deploys on push to `staging` branch.

**Production (DigitalOcean App Platform):**

Connect GitHub repo -> auto-deploy on push to `main` branch.
Set `DATABASE_URL`, `INTERNAL_API_KEY`, and `ENVIRONMENT` in the platform dashboard, not in `.env`.

**Production command:**

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Scheduled runs:**

No scheduled job is required for the MVP chat endpoint. Future analytics rollups can use GitHub Actions or Supabase scheduled functions.

---

### 13. Known Limitations & Future Improvements

**Current limitations:**
- The assistant reply is deterministic and tag-based; it is not yet connected to an LLM.
- The schema is intentionally single-restaurant; adding more restaurants will require a `restaurants` table and FKs.
- The Supabase schema and full menu seed are applied; future menu changes must regenerate and reapply `backend/sql/002_seed_full_menu_from_frontend.sql` or use a future admin CRUD flow.
- The frontend chat is now backend-bound, but the menu page still reads `frontend/src/data/menu-mock.json`.
- No admin endpoint exists yet for menu updates.
- No rate limiting is implemented yet for public chat traffic.

**Planned improvements:**
- Add LLM integration with menu context and strict JSON output.
- Add Supabase Row Level Security policies if direct frontend reads are introduced.
- Add admin-authenticated CRUD endpoints for menu categories and items.
- Add analytics tables for popular requests, unmatched queries and conversion to recommendations.
- Add integration tests against a disposable PostgreSQL/Supabase branch.
