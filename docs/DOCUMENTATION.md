## Masao Restaurant Chatbot Backend — Technical Documentation

**Version:** 1.0.0
**Last updated:** 2026-06-12
**Author:** PlanAhead Engineering
**Status:** Development

---

### 1. Τι κάνει αυτό το εργαλείο (Plain Greek)

Το backend κρατάει το μενού του Masao, ανοίγει ξεχωριστή συνομιλία για κάθε κινητό και τραπέζι, και αποθηκεύει όλα τα μηνύματα της συνομιλίας. Όταν ο πελάτης γράφει τι θέλει, ο AI σερβιτόρος (Claude API) απαντά σαν άνθρωπος «μαθημένος» στο μενού: όλο το μενού (στη γλώσσα του πελάτη) μπαίνει στο system prompt, μαζί με το ιστορικό της συνομιλίας, και το μοντέλο επιστρέφει απάντηση + προτεινόμενα πιάτα (ids) που το Next.js frontend εμφανίζει σαν chat bubbles και κάρτες. Αν δεν υπάρχει `ANTHROPIC_API_KEY` ή το API αποτύχει, το σύστημα πέφτει αυτόματα στο ντετερμινιστικό keyword-matching fallback (πλέον πολυγλωσσικό), ώστε το chat να μη μένει ποτέ χωρίς απάντηση. Η βάση είναι σχεδιασμένη για Supabase/PostgreSQL και για πολλούς πελάτες που σκανάρουν το ίδιο QR τραπεζιού από διαφορετικά κινητά.

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
     ├── ask Claude (menu in system prompt + chat history) via api/services/llm_service.py
     ├── on LLM failure/missing key: deterministic keyword fallback
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
pip install -r requirements.lock
```

**Environment variables (copy `.env.example` -> `.env` and fill in):**

```text
DATABASE_URL=          # PostgreSQL/Supabase async SQLAlchemy URL
INTERNAL_API_KEY=      # API key reserved for future internal/admin endpoints
ANTHROPIC_API_KEY=     # Anthropic API key — enables the Claude-powered AI waiter
ANTHROPIC_MODEL=       # Optional, defaults to claude-opus-4-8
ANTHROPIC_MAX_TOKENS=  # Optional, defaults to 1024
ANTHROPIC_TIMEOUT_SECONDS= # Optional, defaults to 30
ENVIRONMENT=           # development, staging, or production
CORS_ALLOWED_ORIGINS=  # Comma-separated Render/frontend origins allowed by CORS
CORS_ALLOWED_METHODS=  # Comma-separated methods, usually GET,POST,OPTIONS
RATE_LIMIT_BACKEND=    # redis for production, memory for local development
REDIS_URL=             # Managed Redis URL for distributed rate limiting
REDIS_KEY_PREFIX=      # Redis key namespace, e.g. masao
RATE_LIMIT_FAIL_CLOSED= # true blocks chat if Redis is unavailable
REDIS_SOCKET_TIMEOUT_SECONDS= # Redis connect/read timeout
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
psql "$DATABASE_URL" -f backend/sql/004_add_allergens.sql  # allergy alerts: menu allergens + customer profiles
psql "$DATABASE_URL" -f backend/sql/004_hash_device_ids_and_chat_retention.sql
```

> ⚠️ Το `004_add_allergens.sql` κάνει best-effort seed των allergens από τις
> περιγραφές συστατικών. Το εστιατόριο πρέπει να επαληθεύσει τα allergens κάθε
> πιάτου (μέσω `PATCH /api/admin/menu/items/{id}` με πεδίο `allergens`) πριν
> θεωρηθούν αξιόπιστα τα alerts.

If an older schema with Hebrew (`he`) support was already applied, run this cleanup migration before applying the regenerated seed:

```bash
psql "$DATABASE_URL" -f backend/sql/003_remove_hebrew_translations.sql
```

If using the Supabase dashboard, paste the contents of:

```text
backend/sql/001_init_masao_schema.sql
backend/sql/003_remove_hebrew_translations.sql
backend/sql/002_seed_full_menu_from_frontend.sql
backend/sql/004_add_allergens.sql
backend/sql/004_hash_device_ids_and_chat_retention.sql
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

**What it does:** Reads `backend/config/settings.yaml`, loads `.env`, parses Render-friendly comma-separated CORS env vars, and exposes typed settings for database pool, CORS, restaurant slug and chat limits.

**Why it works this way:** CORS origins, pool size and restaurant slug stay configurable without code changes. In production it fails fast if a Render deployment is missing Redis, has a default admin API key, uses wildcard/localhost-only CORS, or tries to use the in-memory rate limiter.

**Edge cases handled:**
- Missing YAML file -> empty config fallback.
- Missing `.env` -> local defaults still allow import and tests.
- `ENVIRONMENT=production` with unsafe defaults -> app startup fails before serving traffic.
- `CORS_ALLOWED_ORIGINS=https://a,https://b` -> parsed into a list for FastAPI CORS middleware.

#### `backend/api/main.py`

**Purpose:** FastAPI application factory module.

**Main object: `app`**

**What it does:** Creates FastAPI, registers CORS middleware, includes `/api/chat`, adds request-id logging, exposes `/health`, and exposes `/ready` for dependency readiness.

**Why it works this way:** The Next.js frontend runs on localhost ports during development and Render/Vercel-style origins in production; allowed origins live in config. `/health` stays lightweight for liveness, while `/ready` checks Supabase/PostgreSQL and Redis before Render routes traffic to the service.

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

```python
@app.get("/ready")
async def ready():
    checks = {"database": "ok", "rate_limiter": "ok"}
    ...
```

The readiness endpoint returns `200` only when the database and configured rate limiter are available. It returns `503` with generic dependency status when either check fails.

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
- `429` if the anonymous chat client exceeds the configured rate limit.
- `422` if `restaurant_slug` is unsupported.
- `500` if database operations fail.

#### `backend/api/services/chat_service.py`

**Purpose:** Business logic for chat persistence and menu recommendation.

**Main function: `handle_chat(request)`**

**What it does:** Creates or reuses an active chat session, stores the user message, fetches localized menu items for the requested `language_code`, classifies the user intent, generates a deterministic answer, stores the assistant message, and returns structured JSON.

**Why it works this way:** The MVP does not require an LLM dependency to prove the backend/frontend contract. It uses menu tags, descriptions, category intent and item-name matching first, which keeps responses predictable and auditable.

**Edge cases handled:**
- Rate limit exceeded -> returns `429` before writing a chat message.
- Unknown restaurant slug -> raises `ValueError`.
- Empty/low-signal user message -> fallback assistant reply.
- Drink/cocktail/wine questions -> scoped to drink categories instead of food.
- Item detail questions such as `τι έχει το long drinks` -> answer from the stored item description.
- Generic item descriptions -> the assistant states that detailed ingredients are unavailable instead of inventing them.
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

This ranks available menu items by text/tag overlap inside the detected menu group, then by lower price and stable name ordering. It is intentionally deterministic so test failures are meaningful.

**Business formulas used:**

No financial formulas are used in this backend. Recommendation logic is:

```text
1. Normalize Greek/Latin text, remove accents and normalize final sigma.
2. Detect intent:
   - item_detail for "τι έχει/τι περιέχει το X"
   - category_overview for "σε ποτά τι έχει"
   - recommendation for "θέλω/πρότεινε X"
3. Detect menu group: cocktails, drinks, wines or shisha when the query mentions those categories.
4. Score only available items inside the detected group.
5. Menu Match Score = count(search_terms that appear in item name + description + category + tags).
```

Exact Python code:

```python
answer = answer_menu_query(request.user_message, menu_items)
recommendations = answer.recommendations
assistant_content = answer.reply
```

#### `backend/api/services/rate_limiter.py`

**Purpose:** Rate limiting for public chat traffic.

**Main function: `check(key)`**

**What it does:** Tracks request timestamps per anonymous key and returns an allow/deny decision with `X-RateLimit-*` and `Retry-After` values.

**Why it works this way:** The production backend should use Redis so all FastAPI workers share one rate-limit state. Limiting by `restaurant_slug`, `table_number`, and anonymous `device_id` blocks rapid repeats before any database write.

**Edge cases handled:**
- Same device repeats too quickly -> `429 Too Many Requests`.
- Different device ids -> separate buckets.
- Old timestamps -> removed after the configured window.
- Redis keys are SHA-256 hashed so raw anonymous ids are not stored in key names.
- Redis failures -> fail closed by default with `503`, configurable for fail-open behavior.

**Key logic explained:**

```python
raw_result = await self.redis.eval(
    REDIS_SLIDING_WINDOW_SCRIPT,
    1,
    self._redis_key(key),
    now_ms,
    window_ms,
    self.limit,
    member,
    ttl_ms,
)
```

The Redis backend uses one atomic Lua script with a sorted set sliding window. Local development can still use the in-process `memory` backend, but production should set `RATE_LIMIT_BACKEND=redis`.

#### `backend/api/routers/menu.py`

**Purpose:** HTTP boundary for public menu reads.

**Endpoint:** `GET /api/menu`

**What it expects:** Optional query parameters: `restaurant_slug`, `language_code`, and `include_unavailable`.

**What it returns:** Restaurant slug, language code, category count, item count, and menu categories with nested items.

**Business logic it triggers:** Delegates Supabase menu reads and grouping to `MenuService`.

**Errors it can return:**
- `422` if `restaurant_slug` is unsupported or `language_code` is outside `el`, `en`, `de`, `it`, `sv`.
- `500` if database operations fail.

#### `backend/api/services/menu_service.py`

**Purpose:** Read-only menu data service for the public menu endpoint and chat recommendations.

**Main function: `get_public_menu(restaurant_slug, language_code, include_unavailable)`**

**What it does:** Fetches localized menu rows from Supabase/PostgreSQL, falls back to canonical names/descriptions when a translation is missing, filters unavailable items by default, and groups rows into frontend-friendly category sections.

**Why it works this way:** The frontend `MenuApp` needs categories with nested items, while the database stores normalized category, item, and translation tables. Grouping in the backend keeps the frontend simple and avoids direct frontend database access.

**Edge cases handled:**
- Unknown restaurant slug -> raises `ValueError`.
- Missing translation row -> falls back to canonical menu/category fields.
- Unavailable items -> excluded by default; returned only with `include_unavailable=true`.
- Category and item ordering -> preserved from database `display_order`.

**Key logic explained:**

```python
for item in items:
    if not include_unavailable and not item.is_available:
        continue

    category = categories.get(item.category_id)
    if category is None:
        category = MenuCategoryPublicResponse(...)
        categories[item.category_id] = category

    category.items.append(MenuItemPublicResponse(...))
```

This turns flat SQL rows into the grouped structure expected by a menu UI.

#### `backend/api/routers/admin_menu.py`

**Purpose:** Authenticated HTTP boundary for menu management.

**Endpoints:** `POST/PATCH /api/admin/menu/categories`, `POST/PATCH /api/admin/menu/items`, and translation upserts.

**What it expects:** `X-API-Key` plus JSON payloads for category, item, or translation changes.

**What it returns:** Canonical category/item rows or translation rows after persistence.

**Business logic it triggers:** Delegates validated menu writes to `AdminMenuService`.

**Errors it can return:**
- `403` if `X-API-Key` is missing or invalid.
- `404` if a patched category or item does not exist.
- `409` if the update conflicts with unique/FK constraints.
- `500` if database operations fail.

#### `backend/api/services/admin_menu_service.py`

**Purpose:** Authenticated menu write service for internal/admin tools.

**Main functions:** `create_category`, `update_category`, `create_item`, `update_item`, `upsert_category_translation`, `upsert_item_translation`.

**What it does:** Writes validated admin changes to normalized Supabase/PostgreSQL menu tables and returns the persisted row.

**Why it works this way:** Daily menu changes should not require editing SQL seed files. Admin writes are kept behind the backend API and `X-API-Key`, while the public frontend continues to use read-only endpoints.

**Edge cases handled:**
- Empty PATCH body -> rejected before SQL.
- `is_available=false` -> accepted as a real update, not treated as missing.
- Unsupported update field -> rejected by a whitelist.
- Duplicate category slug or external id -> returned as `409 Conflict`.

**Key logic explained:**

```python
assignments, params = build_update_statement(
    "item",
    fields,
    {"category_id", "external_id", "name", "description", "price", "tags", "is_available", "display_order"},
)
```

The SQL `SET` clause is built only from validated Pydantic fields and an explicit whitelist. Values are still bound as SQL parameters.

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
429 Too Many Requests - anonymous device exceeded chat request budget
503 Service Unavailable - Redis rate-limit backend unavailable and fail-closed is enabled
422 Unprocessable Entity - invalid body or unsupported restaurant_slug
500 Internal Server Error - database unavailable or write failed
```

**Next.js binding:**

The frontend chat sends this request from `frontend/src/lib/chat-api.ts`. It creates a stable anonymous `device_id` in LocalStorage, reads the table number from `?table=12`, and sends the active `LanguageContext` language as `language_code`.

**Rate-limit response headers:**

```text
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 60
Retry-After: 60       # only when response is 429
```

#### GET /api/menu

**Purpose:** Return the public restaurant menu grouped by category for frontend rendering.

**Query parameters:**

```text
restaurant_slug=masao       # optional, defaults to masao
language_code=en            # optional, defaults to el; allowed: el, en, de, it, sv
include_unavailable=false   # optional, defaults to false
```

**Example request:**

```text
GET /api/menu?language_code=en
```

**Response shape:**

```json
{
  "restaurant_slug": "masao",
  "language_code": "en",
  "total_categories": 24,
  "total_items": 130,
  "categories": [
    {
      "id": 1,
      "slug": "uramaki-hossomaki-6pcs",
      "name": "Uramaki / Hossomaki (6pcs)",
      "display_order": 10,
      "items": [
        {
          "id": 1,
          "external_id": "UR001",
          "category_id": 1,
          "category_slug": "uramaki-hossomaki-6pcs",
          "category_name": "Uramaki / Hossomaki (6pcs)",
          "name": "Cucumber Maki",
          "description": "cucumber",
          "price": 8.0,
          "tags": ["light", "fresh"],
          "is_available": true,
          "display_order": 1,
          "language_code": "en"
        }
      ]
    }
  ]
}
```

**Errors:**

```text
422 Unprocessable Entity - unsupported restaurant_slug or language_code
500 Internal Server Error - database unavailable or read failed
```

**Frontend handoff:**

The backend endpoint is ready. The frontend `MenuApp` has not been changed in this backend-only task; it can now be wired to this endpoint by the frontend owner.

#### POST /api/admin/menu/categories

**Purpose:** Create a menu category.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "name": "Lunch Specials",
  "slug": "lunch-specials",
  "display_order": 250
}
```

**Response:**

```json
{
  "id": 25,
  "name": "Lunch Specials",
  "slug": "lunch-specials",
  "display_order": 250
}
```

#### PATCH /api/admin/menu/categories/{category_id}

**Purpose:** Update category name, slug, or display order.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "display_order": 260
}
```

**Response:**

```json
{
  "id": 25,
  "name": "Lunch Specials",
  "slug": "lunch-specials",
  "display_order": 260
}
```

#### PUT /api/admin/menu/categories/{category_id}/translations/{language_code}

**Purpose:** Create or update a category translation.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "name": "Specials Ημέρας"
}
```

**Response:**

```json
{
  "category_id": 25,
  "language_code": "el",
  "name": "Specials Ημέρας"
}
```

#### POST /api/admin/menu/items

**Purpose:** Create a menu item.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "category_id": 25,
  "external_id": "LS001",
  "name": "Lunch Salmon Bowl",
  "description": "Salmon, rice, avocado, cucumber",
  "price": 14.5,
  "tags": ["salmon", "fresh", "lunch"],
  "is_available": true,
  "display_order": 1
}
```

**Response:**

```json
{
  "id": 131,
  "external_id": "LS001",
  "category_id": 25,
  "name": "Lunch Salmon Bowl",
  "description": "Salmon, rice, avocado, cucumber",
  "price": 14.5,
  "tags": ["salmon", "fresh", "lunch"],
  "is_available": true,
  "display_order": 1
}
```

#### PATCH /api/admin/menu/items/{item_id}

**Purpose:** Update item fields such as price, availability, tags, category, or display order.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "price": 15.0,
  "is_available": false
}
```

**Response:**

```json
{
  "id": 131,
  "external_id": "LS001",
  "category_id": 25,
  "name": "Lunch Salmon Bowl",
  "description": "Salmon, rice, avocado, cucumber",
  "price": 15.0,
  "tags": ["salmon", "fresh", "lunch"],
  "is_available": false,
  "display_order": 1
}
```

#### PUT /api/admin/menu/items/{item_id}/translations/{language_code}

**Purpose:** Create or update an item translation.

**Auth:** Requires `X-API-Key`.

**Request body:**

```json
{
  "name": "Lunch Salmon Bowl",
  "description": "Σολομός, ρύζι, αβοκάντο, αγγούρι"
}
```

**Response:**

```json
{
  "menu_item_id": 131,
  "language_code": "el",
  "name": "Lunch Salmon Bowl",
  "description": "Σολομός, ρύζι, αβοκάντο, αγγούρι"
}
```

**Admin endpoint errors:**

```text
403 Forbidden - missing or invalid X-API-Key
404 Not Found - category or item id does not exist
409 Conflict - unique/FK constraint conflict
422 Unprocessable Entity - invalid payload or empty PATCH body
500 Internal Server Error - database unavailable or write failed
```

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

#### GET /ready

**Purpose:** Render readiness check for dependencies before routing production traffic.

**Healthy response:**

```json
{
  "status": "ready",
  "service": "Masao Restaurant Chatbot API",
  "checks": {
    "database": "ok",
    "rate_limiter": "ok"
  }
}
```

**Unavailable response:**

```json
{
  "status": "not_ready",
  "service": "Masao Restaurant Chatbot API",
  "checks": {
    "database": "unavailable",
    "rate_limiter": "ok"
  }
}
```

**Errors:**

```text
503 Service Unavailable - database or Redis-backed rate limiter is unavailable
```

---

### 8. Output Files

| File | Location | Format | Description |
|------|----------|--------|-------------|
| 001_init_masao_schema.sql | backend/sql/ | SQL | Supabase/PostgreSQL schema |
| 002_seed_full_menu_from_frontend.sql | backend/sql/ | SQL | Full menu seed generated from frontend JSON |
| 003_remove_hebrew_translations.sql | backend/sql/ | SQL | Cleanup migration that removes old Hebrew rows and constraints |
| 004_hash_device_ids_and_chat_retention.sql | backend/sql/ | SQL | Pseudonymizes existing device ids and adds the chat-retention index |
| generate_menu_seed_sql.py | backend/scripts/ | Python | Deterministic SQL seed generator |
| pipeline/runtime logs | backend/logs/ | Text | Future operational logs; gitignored |
| API responses | HTTP JSON | JSON | Public menu, chat messages and recommendations for Next.js |
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
| CORS_ALLOWED_ORIGINS | unset | Comma-separated env override for Render/frontend origins |
| CORS_ALLOWED_METHODS | unset | Comma-separated env override for allowed browser methods |
| chat.history_limit | 20 | Maximum recent messages returned per response |
| chat.max_user_message_chars | 1000 | Pydantic max length for user messages |
| chat.default_table_number | 1 | Reserved default for future QR helpers |
| chat.retention_days / CHAT_RETENTION_DAYS | 30 | Maximum age of stored chat sessions before automatic deletion |
| rate_limit.backend | memory | Use `redis` in production, `memory` only for local development |
| rate_limit.chat_requests | 20 | Allowed `/api/chat` requests per anonymous restaurant/table/device key |
| rate_limit.chat_ip_requests / CHAT_IP_RATE_LIMIT_REQUESTS | 120 | Higher network-wide limit that prevents bypass by rotating device ids |
| rate_limit.window_seconds | 60 | Sliding window in seconds for chat rate limiting |
| rate_limit.max_buckets | 5000 | Maximum in-memory limiter buckets before pruning |
| rate_limit.redis_url | empty | Managed Redis URL, usually supplied by `REDIS_URL` |
| rate_limit.redis_key_prefix | masao | Redis key namespace for this app |
| rate_limit.redis_socket_timeout_seconds | 1.0 | Redis connect/read timeout in seconds |
| rate_limit.fail_closed | true | Return 503 if Redis is unavailable instead of allowing unlimited chat |
| INTERNAL_API_KEY | required in production | Secret for `/api/admin/menu/*`; default placeholder is rejected in production |
| ENVIRONMENT | development | `production` enables startup guardrails for CORS, Redis and secrets |

---

### 10. Error Handling Reference

| Error | Location | Cause | What happens |
|-------|----------|-------|--------------|
| ValidationError | schemas/chat.py | Missing/blank field, short device id, invalid table number | FastAPI returns 422 |
| ValueError | services/chat_service.py | Unsupported `restaurant_slug` | Router returns 422 with detail |
| SQLAlchemyError | services/chat_service.py | DB unavailable, failed insert/select | Router returns 500 and logs exception |
| HTTPException 429 | routers/chat.py | Chat rate limit exceeded | Request is rejected before any DB write; `Retry-After` is returned |
| HTTPException 503 | routers/chat.py | Redis rate-limit backend unavailable with fail-closed enabled | Request is rejected before chat DB writes |
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
| tests/test_menu_service.py | Public menu grouping, unavailable item filtering and include_unavailable behavior |
| tests/test_admin_menu_schema.py | Admin menu payload validation and patch semantics |
| tests/test_admin_menu_service.py | Whitelisted dynamic update statement generation |
| tests/test_config.py | Production startup guardrails and Render CORS env parsing |
| tests/test_health_routes.py | `/health` liveness and `/ready` dependency status |
| tests/test_security.py | Admin API key behavior and redacted device logging |
| tests/test_rate_limiter.py | Memory limiter, Redis limiter, fail-open/fail-closed behavior, key scoping and headers |
| tests/test_chat_rate_limit_route.py | `/api/chat` route returns 429 after configured budget is exceeded |

Regression cases added for the drink/chat bug:

```text
θέλω ένα φρουτώδες cocktail -> cocktail items only, no soft drink/sushi fallback
σε ποτά τι έχει -> category overview for cocktails/drinks/wines, no food recommendation
τι έχει το long drinks -> Long Drinks detail, no Tea recommendation
τι περιέχει το cucumber maki -> Cucumber Maki detail, no Shrimp Tempura recommendation
```

Current verification on 2026-06-12:

```text
python -m compileall . exited 0
  note: existing .pytest_cache could not be listed because of local permissions
python -m pytest -p no:cacheprovider tests -v passed: 46 tests
python main.py --input sql --dry-run passed with batch summary success:1 failed:0 skipped:0
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
backend/sql/004_hash_device_ids_and_chat_retention.sql
```

**Staging (Render):**

Connect GitHub repo -> Render auto-deploys on push to `staging` branch.

Render production environment variables:

```text
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
INTERNAL_API_KEY=<long random secret>
CORS_ALLOWED_ORIGINS=https://masao.onrender.com,https://masao.vercel.app
CORS_ALLOWED_METHODS=GET,POST,OPTIONS
RATE_LIMIT_BACKEND=redis
REDIS_URL=rediss://USER:PASSWORD@HOST:PORT/0
REDIS_KEY_PREFIX=masao
RATE_LIMIT_FAIL_CLOSED=true
REDIS_SOCKET_TIMEOUT_SECONDS=1.0
```

Render health checks should use `/health` for liveness and `/ready` when the platform needs dependency readiness.

**Production (DigitalOcean App Platform):**

Connect GitHub repo -> auto-deploy on push to `main` branch.
Set `DATABASE_URL`, `INTERNAL_API_KEY`, and `ENVIRONMENT` in the platform dashboard, not in `.env`.

**Production command:**

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Cloudflare edge rate limiting:**

The production API should also be protected before traffic reaches FastAPI. The repository includes Terraform config for a Cloudflare WAF rate limiting rule:

```text
infra/cloudflare/
```

Default edge rule:

```text
POST /api/chat
60 requests / 60 seconds
key: cf.colo.id + ip.src
response: 429 application/json
```

Apply flow:

```bash
cd infra/cloudflare
cp terraform.tfvars.example terraform.tfvars
# Set cloudflare_zone_id and api_hostname.
terraform init
terraform plan
terraform apply
```

Use a Cloudflare API token with `Zone WAF Write`. Do not commit `terraform.tfvars` or Terraform state.

Important: Cloudflare supports one zone entry point ruleset per `http_ratelimit` phase. If the zone already has rate limiting rules, import the existing ruleset into Terraform and merge this rule before applying.

**Scheduled runs:**

No scheduled job is required for the MVP chat endpoint. Future analytics rollups can use GitHub Actions or Supabase scheduled functions.

---

### 13. Known Limitations & Future Improvements

**Current limitations:**
- The assistant reply is deterministic and tag-based; it is not yet connected to an LLM.
- Drink/category intent is deterministic and rule-based; it handles known menu groups but does not understand arbitrary natural-language menu taxonomy.
- Generic menu rows such as `Long Drinks = Classic Long Drinks` are answered factually as generic because the backend must not invent missing ingredients.
- The schema is intentionally single-restaurant; adding more restaurants will require a `restaurants` table and FKs.
- The Supabase schema and full menu seed are applied; future menu changes can use the protected `/api/admin/menu/*` endpoints instead of regenerating the seed.
- Backend `GET /api/menu` is ready, but the frontend menu page still reads `frontend/src/data/menu-mock.json` until the frontend owner wires it.
- Admin menu endpoints exist, but there is no browser admin UI yet.
- `/api/chat` supports Redis-backed distributed rate limiting, but production deployment must provide managed Redis and set `RATE_LIMIT_BACKEND=redis`.
- Cloudflare edge rate limiting IaC exists under `infra/cloudflare/`, but it has not been applied to a live Cloudflare zone from this workspace because no zone id/API token is configured here.

**Planned improvements:**
- Wire frontend `MenuApp` to `GET /api/menu`.
- Build a small internal admin UI on top of the protected `/api/admin/menu/*` endpoints.
- Add LLM integration with menu context and strict JSON output.
- Apply `infra/cloudflare/` Terraform against the production Cloudflare zone and tune thresholds from Cloudflare analytics.
- Add Supabase Row Level Security policies if direct frontend reads are introduced.
- Add admin-authenticated CRUD endpoints for menu categories and items.
- Add analytics tables for popular requests, unmatched queries and conversion to recommendations.
- Add integration tests against a disposable PostgreSQL/Supabase branch.
