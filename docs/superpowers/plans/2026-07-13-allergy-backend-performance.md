# Allergy Backend Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the backend for the allergy UX (reminder copy, LLM persona) and harden chat/menu so there is no visible delay and the service survives 200+ concurrent users.

**Architecture:** Four independent backend changes on the existing FastAPI service: (1) an in-process TTL/LRU cache for allergy profiles mirroring the existing `MenuCache` pattern with after-commit invalidation, (2) releasing the DB connection before the multi-second LLM call in `ChatService.handle_chat`, (3) per-language single-flight locking on the menu cache miss path, (4) new warning copy + persona instructions. Spec: `docs/superpowers/specs/2026-07-13-allergy-backend-performance-design.md`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async (asyncpg), pytest + pytest-asyncio (strict mode), no new dependencies.

**Working directory:** all commands run from `backend/` (`cd C:\Users\vagel\masao-project\backend`). Tests: `python -m pytest tests -q` must end at 96 passed before you start. If deps are missing: `pip install -r requirements.txt`.

**Commit convention:** repo commits directly to `main`, short imperative subject, body in Greek or English, trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: ProfileCache (TTL + LRU + negative caching)

**Files:**
- Modify: `backend/api/services/allergy_service.py` (add class + singleton at top, after imports)
- Modify: `backend/api/config.py` (new setting after `menu_cache_ttl_seconds`, ~line 85)
- Modify: `backend/config/settings.yaml` (new `allergy:` section)
- Modify: `backend/tests/conftest.py` (reset new cache around every test)
- Create: `backend/tests/test_profile_cache.py`

- [ ] **Step 1.1: Write the failing tests**

Create `backend/tests/test_profile_cache.py`:

```python
from api.services.allergy_service import ProfileCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_profile_cache_returns_stored_allergens_within_ttl() -> None:
    clock = FakeClock()
    cache = ProfileCache(clock=clock)

    cache.store("device-1", {"milk"}, ttl_seconds=60.0)
    clock.now = 59.0

    assert cache.get("device-1", ttl_seconds=60.0) == frozenset({"milk"})


def test_profile_cache_expires_after_ttl() -> None:
    clock = FakeClock()
    cache = ProfileCache(clock=clock)

    cache.store("device-1", {"milk"}, ttl_seconds=60.0)
    clock.now = 61.0

    assert cache.get("device-1", ttl_seconds=60.0) is None


def test_profile_cache_caches_empty_profiles() -> None:
    """Negative caching: οι περισσότεροι πελάτες δεν έχουν προφίλ."""
    cache = ProfileCache(clock=FakeClock())

    cache.store("device-1", set(), ttl_seconds=60.0)

    # frozenset() είναι falsy — γι' αυτό ο caller ελέγχει `is not None`.
    assert cache.get("device-1", ttl_seconds=60.0) == frozenset()


def test_profile_cache_disabled_when_ttl_is_zero() -> None:
    cache = ProfileCache(clock=FakeClock())

    cache.store("device-1", {"milk"}, ttl_seconds=0)

    assert cache.get("device-1", ttl_seconds=60.0) is None


def test_profile_cache_evicts_least_recently_used_beyond_max_entries() -> None:
    cache = ProfileCache(clock=FakeClock(), max_entries=2)

    cache.store("a", {"milk"}, ttl_seconds=60.0)
    cache.store("b", {"eggs"}, ttl_seconds=60.0)
    # Το "a" γίνεται πιο πρόσφατο από το "b" μέσω get...
    assert cache.get("a", ttl_seconds=60.0) == frozenset({"milk"})
    cache.store("c", {"fish"}, ttl_seconds=60.0)

    # ...οπότε πετιέται το "b" (least recently used), όχι το "a".
    assert cache.get("b", ttl_seconds=60.0) is None
    assert cache.get("a", ttl_seconds=60.0) == frozenset({"milk"})
    assert cache.get("c", ttl_seconds=60.0) == frozenset({"fish"})


def test_profile_cache_invalidate_single_device() -> None:
    cache = ProfileCache(clock=FakeClock())
    cache.store("a", {"milk"}, ttl_seconds=60.0)
    cache.store("b", {"eggs"}, ttl_seconds=60.0)

    cache.invalidate("a")

    assert cache.get("a", ttl_seconds=60.0) is None
    assert cache.get("b", ttl_seconds=60.0) == frozenset({"eggs"})


def test_profile_cache_invalidate_all() -> None:
    cache = ProfileCache(clock=FakeClock())
    cache.store("a", {"milk"}, ttl_seconds=60.0)
    cache.store("b", {"eggs"}, ttl_seconds=60.0)

    cache.invalidate()

    assert cache.get("a", ttl_seconds=60.0) is None
    assert cache.get("b", ttl_seconds=60.0) is None
```

- [ ] **Step 1.2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_profile_cache.py -v`
Expected: FAIL — `ImportError: cannot import name 'ProfileCache'`

- [ ] **Step 1.3: Implement ProfileCache**

In `backend/api/services/allergy_service.py`, replace the import block at the top with:

```python
from __future__ import annotations

import logging
import time
from collections import OrderedDict
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.allergy import AllergyProfileResponse
from api.services.allergens import to_canonical_order
from api.utils import device_log_hash

logger = logging.getLogger(__name__)
```

Right after `logger = logging.getLogger(__name__)`, add:

```python
class ProfileCache:
    """In-process TTL/LRU cache των δηλωμένων αλλεργιογόνων ανά συσκευή.

    Το προφίλ διαβάζεται σε κάθε chat μήνυμα και κάθε /api/menu?device_id=,
    ενώ αλλάζει σπάνια· με cross-region βάση το lookup κοστίζει ~0.6-0.9s.
    Κρατάει και κενά προφίλ (negative caching) γιατί οι περισσότεροι πελάτες
    δεν έχουν δηλώσει τίποτα. Φραγμένο μέγεθος ώστε 200+ συσκευές να μη
    φουσκώνουν τη μνήμη· invalidation μετά το commit του upsert, staleness
    σε multi-worker deployments φράσσεται από το TTL (όπως το MenuCache).
    """

    def __init__(self, clock=time.monotonic, max_entries: int = 5000) -> None:
        self._clock = clock
        self._max_entries = max_entries
        self._entries: OrderedDict[str, tuple[float, frozenset[str]]] = OrderedDict()

    def get(self, device_id: str, ttl_seconds: float) -> frozenset[str] | None:
        """Return cached allergens for a device if still fresh.

        Args:
            device_id: Anonymous frontend device id.
            ttl_seconds: Freshness window; 0 disables caching entirely.

        Returns:
            frozenset[str] | None: Cached codes (possibly empty), None on miss.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return None
        entry = self._entries.get(device_id)
        if entry is None:
            return None
        stored_at, allergens = entry
        if self._clock() - stored_at > ttl_seconds:
            self._entries.pop(device_id, None)
            return None
        self._entries.move_to_end(device_id)
        return allergens

    def store(self, device_id: str, allergens: set[str], ttl_seconds: float) -> None:
        """Cache the declared allergens of a device.

        Args:
            device_id: Anonymous frontend device id.
            allergens: Canonical codes; an empty set is cached too.
            ttl_seconds: Cache policy; 0 or less disables storing entirely.

        Returns:
            None.

        Raises:
            None.
        """
        if ttl_seconds <= 0:
            return
        self._entries[device_id] = (self._clock(), frozenset(allergens))
        self._entries.move_to_end(device_id)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def invalidate(self, device_id: str | None = None) -> None:
        """Drop one device entry, or everything when no device is given.

        Args:
            device_id: Device to evict; None clears the whole cache.

        Returns:
            None.

        Raises:
            None.
        """
        if device_id is None:
            self._entries.clear()
        else:
            self._entries.pop(device_id, None)


profile_cache = ProfileCache()
```

- [ ] **Step 1.4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_profile_cache.py -v`
Expected: 7 passed

- [ ] **Step 1.5: Add the TTL setting**

In `backend/api/config.py`, right after the `menu_cache_ttl_seconds` field (ends ~line 85), add:

```python
    # TTL του in-process cache προφίλ αλλεργιών· 0 το απενεργοποιεί (tests).
    allergy_profile_cache_ttl_seconds: float = Field(
        default=float(
            os.getenv(
                "ALLERGY_PROFILE_CACHE_TTL_SECONDS",
                _yaml_config.get("allergy", {}).get("profile_cache_ttl_seconds", 60.0),
            )
        ),
        ge=0,
    )
```

In `backend/config/settings.yaml`, after the `chat:` block, add:

```yaml
allergy:
  profile_cache_ttl_seconds: 60.0
```

- [ ] **Step 1.6: Reset the cache around every test**

Replace the whole body of `backend/tests/conftest.py` with:

```python
import pytest

from api.services.allergy_service import profile_cache
from api.services.menu_service import menu_cache


@pytest.fixture(autouse=True)
def isolate_process_caches():
    """Reset τα process-global caches γύρω από κάθε test.

    Χωρίς αυτό, ένα test που γεμίζει cache (TTL 60s) θα σέρβιρε τα
    δεδομένα του σε επόμενα tests της ίδιας διεργασίας.
    """
    menu_cache.invalidate()
    profile_cache.invalidate()
    yield
    menu_cache.invalidate()
    profile_cache.invalidate()
```

- [ ] **Step 1.7: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 103 passed (96 + 7 new), 0 failed

- [ ] **Step 1.8: Commit**

```bash
git add api/services/allergy_service.py api/config.py config/settings.yaml tests/test_profile_cache.py tests/conftest.py
git commit -m "Add in-process TTL/LRU cache for allergy profiles"
```

---

### Task 2: Wire the cache into the alert lookup + invalidate on upsert commit

**Files:**
- Modify: `backend/api/services/allergy_service.py` (`try_get_customer_allergens`, `upsert_profile`, new listeners)
- Modify: `backend/tests/test_allergy_service.py` (new tests)

- [ ] **Step 2.1: Write the failing tests**

Append to `backend/tests/test_allergy_service.py` (also extend the imports at the top):

```python
import pytest
from sqlalchemy.exc import OperationalError

from api.services.allergy_service import (
    PROFILE_CACHE_DIRTY_KEY,
    AllergyService,
    invalidate_profile_cache_after_commit,
    profile_cache,
)


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def mappings(self):
        return self

    def all(self) -> list[dict]:
        return self._rows

    def one(self) -> dict:
        return self._rows[0]

    def one_or_none(self) -> dict | None:
        return self._rows[0] if self._rows else None


class RecordingSession:
    """Session stub: μετρά τα queries και υποστηρίζει SAVEPOINT context."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.execute_calls = 0
        self.info: dict = {}

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, statement, params=None) -> FakeResult:
        self.execute_calls += 1
        return FakeResult(self.rows)


PROFILE_ROW = {"device_id": "device-12345", "allergens": ["milk"], "updated_at": None}
UPDATED_ROW = {"device_id": "device-12345", "allergens": ["eggs", "milk"], "updated_at": None}


@pytest.mark.asyncio
async def test_try_get_customer_allergens_uses_cache_within_ttl() -> None:
    session = RecordingSession([PROFILE_ROW])
    service = AllergyService(session=session)

    first = await service.try_get_customer_allergens("device-12345")
    second = await service.try_get_customer_allergens("device-12345")

    assert session.execute_calls == 1
    assert first == second == {"milk"}


@pytest.mark.asyncio
async def test_failed_lookup_is_not_cached() -> None:
    failing = AllergyService(session=FailingSession())
    assert await failing.try_get_customer_allergens("device-12345") == set()

    healthy = AllergyService(session=RecordingSession([PROFILE_ROW]))
    assert await healthy.try_get_customer_allergens("device-12345") == {"milk"}


@pytest.mark.asyncio
async def test_upsert_invalidates_cache_only_after_commit() -> None:
    read_session = RecordingSession([PROFILE_ROW])
    reader = AllergyService(session=read_session)
    await reader.try_get_customer_allergens("device-12345")

    write_session = RecordingSession([UPDATED_ROW])
    writer = AllergyService(session=write_session)
    await writer.upsert_profile("device-12345", ["eggs", "milk"])

    # Πριν το commit: το session είναι απλώς σημαδεμένο, το cache άθικτο.
    assert write_session.info[PROFILE_CACHE_DIRTY_KEY] == {"device-12345"}
    stale = await reader.try_get_customer_allergens("device-12345")
    assert stale == {"milk"}
    assert read_session.execute_calls == 1

    # Μετά το commit (after_commit listener): το επόμενο read ξαναπάει στη βάση.
    invalidate_profile_cache_after_commit(write_session)
    read_session.rows = [UPDATED_ROW]
    fresh = await reader.try_get_customer_allergens("device-12345")
    assert fresh == {"eggs", "milk"}
    assert read_session.execute_calls == 2
```

Keep the existing `FailingSession` tests unchanged (`FailingSession` needs one addition — see Step 2.3).

- [ ] **Step 2.2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_allergy_service.py -v`
Expected: FAIL — `ImportError: cannot import name 'PROFILE_CACHE_DIRTY_KEY'`

- [ ] **Step 2.3: Implement cache wiring**

In `backend/api/services/allergy_service.py`:

1. Extend the imports (needed for the event listeners):

```python
from sqlalchemy import event, text
from sqlalchemy.orm import Session as OrmSession

from api.config import settings
```

2. After `profile_cache = ProfileCache()`, add:

```python
# Session.info key: το upsert_profile προσθέτει εδώ τα device_ids που άλλαξαν
# και το cache ακυρώνεται ΜΕΤΑ το commit (ίδιο pattern με το menu cache —
# ακύρωση πριν το commit θα άφηνε race με αναγνώστες που ξαναγεμίζουν stale).
PROFILE_CACHE_DIRTY_KEY = "allergy_profile_cache_dirty"


@event.listens_for(OrmSession, "after_commit")
def invalidate_profile_cache_after_commit(session: OrmSession) -> None:
    """Invalidate cached profiles once a profile upsert actually commits.

    Args:
        session: ORM session that just committed (sync side of AsyncSession).

    Returns:
        None.

    Raises:
        None.
    """
    for device_id in session.info.pop(PROFILE_CACHE_DIRTY_KEY, ()):
        profile_cache.invalidate(device_id)


@event.listens_for(OrmSession, "after_rollback")
def clear_profile_cache_flag_after_rollback(session: OrmSession) -> None:
    """Drop the dirty flag when a profile upsert rolls back.

    Args:
        session: ORM session that just rolled back.

    Returns:
        None.

    Raises:
        None.
    """
    session.info.pop(PROFILE_CACHE_DIRTY_KEY, None)
```

3. Replace `try_get_customer_allergens` with:

```python
    async def try_get_customer_allergens(self, device_id: str) -> set[str]:
        """Fetch declared allergens without letting a failure break the caller.

        Args:
            device_id: Anonymous frontend device id.

        Returns:
            set[str]: Declared allergen codes; empty when the lookup fails.
                Fail-open: το μενού/chat συνεχίζει χωρίς alerts αντί να πέσει
                (π.χ. αν δεν έχει εφαρμοστεί ακόμη το migration 004).

        Raises:
            None.
        """
        ttl_seconds = settings.allergy_profile_cache_ttl_seconds
        cached = profile_cache.get(device_id, ttl_seconds)
        if cached is not None:
            return set(cached)

        try:
            # SAVEPOINT: αποτυχία εδώ δεν πρέπει να αφήσει aborted το
            # transaction για τα επόμενα queries του ίδιου request.
            async with self.session.begin_nested():
                allergens = await self.get_customer_allergens(device_id)
        except SQLAlchemyError:
            logger.warning(
                "Allergy profile lookup failed; continuing without alerts for device_hash=%s",
                device_log_hash(device_id),
                exc_info=True,
            )
            # Οι αποτυχίες ΔΕΝ μπαίνουν στο cache: το επόμενο request ξαναδοκιμάζει.
            return set()

        profile_cache.store(device_id, allergens, ttl_seconds)
        return allergens
```

4. In `upsert_profile`, right before `return self._profile_response(...)`, add:

```python
        # Σημάδεψε το session· το cache ακυρώνεται από τον after_commit listener.
        self.session.info.setdefault(PROFILE_CACHE_DIRTY_KEY, set()).add(device_id)
```

5. In `backend/tests/test_allergy_service.py`, add an `info` attribute to the existing `FailingSession` stub (the fail-open path now runs after a cache miss, and `upsert` paths touch `.info`):

```python
class FailingSession:
    """Session stub: κάθε query αποτυγχάνει (π.χ. πίνακας δεν υπάρχει)."""

    def __init__(self) -> None:
        self.info: dict = {}
```

(keep its existing `begin_nested`/`__aenter__`/`__aexit__`/`execute` methods unchanged).

- [ ] **Step 2.4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_allergy_service.py tests/test_profile_cache.py -v`
Expected: all pass

- [ ] **Step 2.5: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 106 passed, 0 failed

- [ ] **Step 2.6: Commit**

```bash
git add api/services/allergy_service.py tests/test_allergy_service.py
git commit -m "Serve allergy alerts from the profile cache; invalidate after upsert commit"
```

---

### Task 3: Release the DB connection before the LLM call

**Files:**
- Modify: `backend/api/services/chat_service.py` (`handle_chat`, one line)
- Create: `backend/tests/test_chat_connection_release.py`

- [ ] **Step 3.1: Write the failing test**

Create `backend/tests/test_chat_connection_release.py`:

```python
"""Το chat δεν πρέπει να κρατά DB connection όσο τρέχει η κλήση στο LLM.

Το pool έχει pool_size+max_overflow=30 slots και η κλήση στο Claude κρατά
2-6s· χωρίς commit πριν το LLM, ~30 ταυτόχρονα μηνύματα αρκούν για pool
exhaustion (αναμονή pool_timeout=30s και μετά 500).
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from api.schemas.chat import ChatRequest
from api.services import chat_service as chat_service_module
from api.services.chat_service import ChatService
from api.services.llm_service import LlmAnswer

SESSION_ID = uuid4()
NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)

MENU_ROW = {
    "id": 1,
    "external_id": "C001",
    "category_id": 10,
    "category_slug": "sushi",
    "category_name": "Sushi",
    "category_display_order": 1,
    "name": "Salmon Roll",
    "description": "salmon",
    "price": 9.5,
    "tags": ["fresh"],
    "allergens": ["fish"],
    "is_available": True,
    "display_order": 1,
    "language_code": "en",
}


class FakeResult:
    def __init__(self, rows: list[dict], scalar=None) -> None:
        self._rows = rows
        self._scalar = scalar

    def mappings(self):
        return self

    def all(self) -> list[dict]:
        return self._rows

    def one(self) -> dict:
        return self._rows[0]

    def one_or_none(self) -> dict | None:
        return self._rows[0] if self._rows else None

    def scalar_one(self):
        return self._scalar


class ScriptedSession:
    """Δρομολογεί κάθε SQL στο σωστό αποτέλεσμα και καταγράφει τη σειρά κλήσεων."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.info: dict = {}
        self._message_id = 0

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def commit(self) -> None:
        self.calls.append("commit")

    async def execute(self, statement, params=None) -> FakeResult:
        sql = " ".join(str(statement).split())
        if "insert into chat_sessions" in sql:
            return FakeResult([], scalar=SESSION_ID)
        if "insert into chat_messages" in sql:
            self._message_id += 1
            return FakeResult(
                [
                    {
                        "id": self._message_id,
                        "session_id": SESSION_ID,
                        "role": params["role"],
                        "content": params["content"],
                        "created_at": NOW,
                    }
                ]
            )
        if "from chat_messages" in sql:
            return FakeResult(
                [
                    {
                        "id": 1,
                        "session_id": SESSION_ID,
                        "role": "user",
                        "content": "shrimp please",
                        "created_at": NOW,
                    }
                ]
            )
        if "from customer_allergy_profiles" in sql:
            return FakeResult([])
        if "from menu_items" in sql:
            return FakeResult([MENU_ROW])
        raise AssertionError(f"unexpected SQL: {sql}")


@pytest.mark.asyncio
async def test_handle_chat_commits_before_calling_the_llm(monkeypatch) -> None:
    calls: list[str] = []

    class FakeLlm:
        def is_configured(self) -> bool:
            return True

        async def answer(self, history, menu_items, language_code, customer_allergens=None):
            calls.append("llm")
            return LlmAnswer(reply="Enjoy!", recommended_item_ids=[])

    monkeypatch.setattr(chat_service_module, "get_llm_chat_service", lambda: FakeLlm())

    service = ChatService(session=ScriptedSession(calls))
    response = await service.handle_chat(
        ChatRequest(
            restaurant_slug="masao",
            table_number=1,
            device_id="device-12345",
            user_message="shrimp please",
            language_code="en",
        )
    )

    assert "llm" in calls and "commit" in calls
    # Η σύνδεση πρέπει να επιστρέφει στο pool ΠΡΙΝ την αργή κλήση στο LLM.
    assert calls.index("commit") < calls.index("llm")
    assert response.assistant_message.content == "Enjoy!"
```

- [ ] **Step 3.2: Run the test to verify it fails**

Run: `python -m pytest tests/test_chat_connection_release.py -v`
Expected: FAIL — `assert "commit" in calls` (no commit happens before the LLM today)

- [ ] **Step 3.3: Implement commit-before-LLM**

In `backend/api/services/chat_service.py`, inside `handle_chat`, right after
`history = await self._fetch_messages(session_id)` and before the
`assistant_content, recommendations = await self._generate_answer(` line, add:

```python
            # Επιστροφή της σύνδεσης στο pool πριν το LLM: η κλήση κρατά
            # δευτερόλεπτα, το pool έχει 30 slots — με ανοιχτό transaction
            # εδώ, ~30 ταυτόχρονα μηνύματα αρκούν για pool exhaustion. Το
            # insert του assistant message ανοίγει νέο transaction μετά.
            await self.session.commit()
```

- [ ] **Step 3.4: Run the test to verify it passes**

Run: `python -m pytest tests/test_chat_connection_release.py -v`
Expected: PASS

- [ ] **Step 3.5: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 107 passed, 0 failed

- [ ] **Step 3.6: Commit**

```bash
git add api/services/chat_service.py tests/test_chat_connection_release.py
git commit -m "Release the DB connection before the LLM call in chat"
```

---

### Task 4: Single-flight on the menu cache miss path

**Files:**
- Modify: `backend/api/services/menu_service.py` (locks + `fetch_items`)
- Modify: `backend/tests/test_menu_cache.py` (new test)
- Modify: `backend/tests/conftest.py` (clear locks between tests)

- [ ] **Step 4.1: Write the failing test**

Append to `backend/tests/test_menu_cache.py` (add `import asyncio` to its imports):

```python
class SlowSession(FakeSession):
    """FakeSession που αργεί, ώστε όλα τα tasks να προλάβουν το miss path."""

    async def execute(self, statement, params=None) -> FakeResult:
        self.execute_calls += 1
        await asyncio.sleep(0.02)
        return FakeResult(self.rows)


@pytest.mark.asyncio
async def test_concurrent_cold_cache_fetches_run_a_single_query() -> None:
    """Anti-stampede: σε TTL expiry με N ταυτόχρονα requests, 1 query."""
    session = SlowSession([MENU_ROW])
    service = MenuService(session=session)

    results = await asyncio.gather(
        *(service.fetch_items(language_code="en") for _ in range(8))
    )

    assert session.execute_calls == 1
    assert all(result == results[0] for result in results)
```

- [ ] **Step 4.2: Run the test to verify it fails**

Run: `python -m pytest tests/test_menu_cache.py -v`
Expected: the new test FAILS with `assert 8 == 1` (every task runs its own query today); all pre-existing tests still pass

- [ ] **Step 4.3: Implement per-language single-flight**

In `backend/api/services/menu_service.py`:

1. Add `import asyncio` to the imports (top of file, stdlib group with `time`).

2. After `MENU_CACHE_DIRTY_KEY = "menu_cache_dirty"` (and its listeners), add:

```python
# Ένα lock ανά γλώσσα: όταν λήγει το TTL με ταυτόχρονα requests, μόνο ένα
# τρέχει το 4-πινάκων query· τα υπόλοιπα διαβάζουν το φρέσκο cache.
_fetch_locks: dict[str, asyncio.Lock] = {}


def _fetch_lock(language_code: str) -> asyncio.Lock:
    """Return the per-language single-flight lock, creating it lazily.

    Args:
        language_code: Menu translation language (φραγμένο σύνολο — LanguageCode).

    Returns:
        asyncio.Lock: Shared lock for that language's cache fills.

    Raises:
        None.
    """
    lock = _fetch_locks.get(language_code)
    if lock is None:
        lock = _fetch_locks.setdefault(language_code, asyncio.Lock())
    return lock
```

3. Replace the body of `fetch_items` (keep the docstring) so the cache miss runs under the lock with a double-check:

```python
        cached = menu_cache.get(language_code, settings.menu_cache_ttl_seconds)
        if cached is not None:
            return cached

        async with _fetch_lock(language_code):
            # Double-check: όσο περιμέναμε το lock, ο πρώτος miss γέμισε το cache.
            cached = menu_cache.get(language_code, settings.menu_cache_ttl_seconds)
            if cached is not None:
                return cached

            result = await self.session.execute(
                text(
                    """
                    select
                        mi.id,
                        mi.external_id,
                        mc.id as category_id,
                        mc.slug as category_slug,
                        coalesce(mct.name, mc.name) as category_name,
                        mc.display_order as category_display_order,
                        coalesce(mit.name, mi.name) as name,
                        coalesce(mit.description, mi.description) as description,
                        mi.price,
                        mi.tags,
                        mi.allergens,
                        mi.is_available,
                        mi.display_order,
                        :language_code as language_code
                    from menu_items mi
                    join menu_categories mc on mc.id = mi.category_id
                    left join menu_item_translations mit
                        on mit.menu_item_id = mi.id
                       and mit.language_code = :language_code
                    left join menu_category_translations mct
                        on mct.category_id = mc.id
                       and mct.language_code = :language_code
                    order by mc.display_order asc, mi.display_order asc, mi.id asc
                    """
                ),
                {"language_code": language_code},
            )
            items = [self._item_record(row) for row in result.mappings().all()]
            menu_cache.store(language_code, items, settings.menu_cache_ttl_seconds)
            return items
```

(The SQL is byte-for-byte the existing query — only the locking wrapper is new.)

4. In `backend/tests/conftest.py`, extend the autouse fixture so locks never leak across event loops of different tests — final fixture:

```python
import pytest

from api.services import menu_service
from api.services.allergy_service import profile_cache
from api.services.menu_service import menu_cache


@pytest.fixture(autouse=True)
def isolate_process_caches():
    """Reset τα process-global caches/locks γύρω από κάθε test.

    Χωρίς αυτό, ένα test που γεμίζει cache (TTL 60s) θα σέρβιρε τα δεδομένα
    του σε επόμενα tests, και ένα asyncio.Lock δεμένο στο event loop ενός
    test θα διέρρεε στο loop του επόμενου.
    """
    menu_cache.invalidate()
    profile_cache.invalidate()
    menu_service._fetch_locks.clear()
    yield
    menu_cache.invalidate()
    profile_cache.invalidate()
    menu_service._fetch_locks.clear()
```

- [ ] **Step 4.4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_menu_cache.py -v`
Expected: all pass (including the new one)

- [ ] **Step 4.5: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 108 passed, 0 failed

- [ ] **Step 4.6: Commit**

```bash
git add api/services/menu_service.py tests/test_menu_cache.py tests/conftest.py
git commit -m "Add per-language single-flight to the menu cache miss path"
```

---

### Task 5: New allergy warning copy (5 languages)

**Files:**
- Modify: `backend/api/services/chat_service.py` (`FALLBACK_TEXTS[*]["allergy_warning"]`, ~lines 175-260)
- Modify: `backend/tests/test_allergy_alerts.py` (wording assertions + placeholder test)

- [ ] **Step 5.1: Update the failing-first assertions**

In `backend/tests/test_allergy_alerts.py`:

1. In `test_answer_menu_query_warns_on_flagged_recommendation`, replace
   `assert "confirm with the staff" in answer.reply` with:

```python
    assert "leave it out" in answer.reply
```

2. Append a new test at the end of the file:

```python
@pytest.mark.parametrize("lang", ["el", "en", "de", "it", "sv"])
def test_allergy_warning_keeps_format_placeholders(lang: str) -> None:
    from api.services.chat_service import FALLBACK_TEXTS

    text = FALLBACK_TEXTS[lang]["allergy_warning"]
    assert "{name}" in text
    assert "{allergens}" in text
```

- [ ] **Step 5.2: Run to verify the wording test fails**

Run: `python -m pytest tests/test_allergy_alerts.py -v`
Expected: `test_answer_menu_query_warns_on_flagged_recommendation` FAILS (`"leave it out" not in ...`); the placeholder tests pass already

- [ ] **Step 5.3: Replace the five warning strings**

In `backend/api/services/chat_service.py`, `FALLBACK_TEXTS`, replace each
`"allergy_warning"` value:

el (was: `" Προσοχή: το {name} περιέχει {allergens} που έχεις δηλώσει ως αλλεργία. Επιβεβαίωσέ το με το προσωπικό."`):

```python
        "allergy_warning": (
            " Προσοχή: το {name} περιέχει {allergens} που έχεις δηλώσει ως αλλεργία. "
            "Ζήτησε από το προσωπικό να το αφαιρέσουν από το πιάτο αν γίνεται, "
            "αλλιώς προτίμησε κάτι άλλο."
        ),
```

en:

```python
        "allergy_warning": (
            " Warning: {name} contains {allergens}, which you have declared as an allergy. "
            "Ask the staff to leave it out if possible, or choose something else."
        ),
```

de:

```python
        "allergy_warning": (
            " Achtung: {name} enthält {allergens}, was Sie als Allergie angegeben haben. "
            "Bitten Sie das Personal, es nach Möglichkeit wegzulassen, "
            "oder wählen Sie lieber etwas anderes."
        ),
```

it:

```python
        "allergy_warning": (
            " Attenzione: {name} contiene {allergens}, che hai dichiarato come allergia. "
            "Chiedi al personale di toglierlo dal piatto se possibile, "
            "oppure scegli qualcos'altro."
        ),
```

sv:

```python
        "allergy_warning": (
            " Varning: {name} innehåller {allergens}, som du har angett som allergi. "
            "Be personalen ta bort det om det går, eller välj något annat."
        ),
```

- [ ] **Step 5.4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_allergy_alerts.py -v`
Expected: all pass

- [ ] **Step 5.5: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 113 passed, 0 failed

- [ ] **Step 5.6: Commit**

```bash
git add api/services/chat_service.py tests/test_allergy_alerts.py
git commit -m "Allergy warning now suggests removing the ingredient or choosing another dish"
```

---

### Task 6: LLM persona alignment

**Files:**
- Modify: `backend/api/services/llm_service.py` (`build_persona_prompt` allergy bullet, `build_allergy_prompt`)
- Modify: `backend/tests/test_allergy_alerts.py` (`test_build_allergy_prompt_names_codes_and_localized_labels`)

- [ ] **Step 6.1: Extend the failing-first assertion**

In `backend/tests/test_allergy_alerts.py`, in
`test_build_allergy_prompt_names_codes_and_localized_labels`, add one assertion at the end:

```python
    assert "leave the ingredient out" in prompt
```

- [ ] **Step 6.2: Run to verify it fails**

Run: `python -m pytest tests/test_allergy_alerts.py::test_build_allergy_prompt_names_codes_and_localized_labels -v`
Expected: FAIL — `"leave the ingredient out" not in prompt`

- [ ] **Step 6.3: Update both prompt builders**

In `backend/api/services/llm_service.py`:

1. In `build_allergy_prompt`, replace the `return (...)` with:

```python
    return (
        "GUEST ALLERGY PROFILE: the guest has declared allergies to: "
        f"{', '.join(customer_allergens)} ({localized}).\n"
        "Never recommend an item whose [allergens] list includes any of these without "
        "a clear warning naming the allergen. When the guest asks about such an item, "
        "remind them they can ask the kitchen to leave the ingredient out where "
        "possible, or suggest a safe alternative instead. Remind the guest to confirm "
        "with the staff because allergen data may be incomplete."
    )
```

2. In `build_persona_prompt`, replace the allergy bullet (the string starting
`"- Menu items may list allergens in [allergens: ...]"`) with:

```python
        "- Menu items may list allergens in [allergens: ...]. If the guest mentions an "
        "allergy or a GUEST ALLERGY PROFILE is provided, NEVER suggest a dish containing "
        "those allergens without an explicit warning, and always advise confirming with "
        "the staff. Offer to ask the kitchen to leave the ingredient out where possible, "
        "or point to a safe alternative. Items without listed allergens are unverified, "
        "not allergen-free.\n"
```

- [ ] **Step 6.4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_allergy_alerts.py -v`
Expected: all pass

- [ ] **Step 6.5: Run the full suite**

Run: `python -m pytest tests -q`
Expected: 113 passed, 0 failed

- [ ] **Step 6.6: Commit**

```bash
git add api/services/llm_service.py tests/test_allergy_alerts.py
git commit -m "Persona: waiter offers ingredient removal or a safe alternative on allergies"
```

---

### Task 7: Frontend contract documentation for the colleague

**Files:**
- Modify: `docs/FRONTEND_BACKEND_INTEGRATION_GR.md` (append a new section at the end)

- [ ] **Step 7.1: Append the contract section**

Append to `docs/FRONTEND_BACKEND_INTEGRATION_GR.md`:

```markdown
## 10. Allergy UX — συμβόλαιο για το frontend (2026-07-13)

Συμφωνημένο flow (το UI υλοποιείται στο frontend· το backend είναι έτοιμο):

### Bottom-sheet «Έχεις κάποια αλλεργία;» (πρώτο άνοιγμα του μενού)

- Λίστα επιλογών: `GET /api/allergens?language_code=<lang>` →
  `{allergens: [{code, label}]}` στις 5 γλώσσες. Η λίστα είναι τα πάγια 14
  αλλεργιογόνα της ΕΕ — μπορεί να μπει και στατικά στο frontend ώστε το
  sheet να ανοίγει ακαριαία (χωρίς αναμονή σε Render cold start).
- Αποθήκευση: `PUT /api/profile/allergies` με body
  `{"device_id": "<masao-device-id>", "allergens": ["milk", ...]}`.
  Χρησιμοποιήστε το ΙΔΙΟ device_id που ήδη κρατά το chat στο localStorage
  (`masao-device-id`, βλ. getOrCreateDeviceId στο chat-api.ts). Το
  «Δεν έχω αλλεργίες» στέλνει κενή λίστα `[]`.
- Prefill στην επεξεργασία: `GET /api/profile/allergies?device_id=...` →
  `{device_id, allergens, updated_at}` (κενό allergens όταν δεν υπάρχει
  προφίλ). Το endpoint διαβάζει πάντα τη βάση — ποτέ stale μετά από PUT.

### Badges στο μενού — ΧΩΡΙΣ device_id

Το `GET /api/menu` επιστρέφει ήδη `allergens: [...]` σε κάθε πιάτο χωρίς
κανένα επιπλέον παράμετρο. Το ταίριασμα με το προφίλ του χρήστη γίνεται
client-side (τομή των δύο λιστών). ΜΗ στέλνετε device_id στο /api/menu:
θα προσθέσει ένα DB lookup ανά request χωρίς λόγο, ενώ το client-side
ταίριασμα ενημερώνει τα badges στιγμιαία όταν αλλάζει το προφίλ.

### Chat — καμία αλλαγή

Το POST /api/chat δεν αλλάζει. Όταν υπάρχει προφίλ, το backend προσθέτει
αυτόματα την υπενθύμιση («ζήτησε να αφαιρεθεί από το πιάτο αν γίνεται,
αλλιώς προτίμησε κάτι άλλο») σε κάθε απάντηση που αφορά πιάτο με δηλωμένο
αλλεργιογόνο, και τα `recommended_items` έχουν ήδη
`allergens / matched_allergens / allergen_alert` για το ⚠ badge.
```

- [ ] **Step 7.2: Full suite one last time**

Run: `python -m pytest tests -q`
Expected: 113 passed, 0 failed

- [ ] **Step 7.3: Commit**

```bash
git add docs/FRONTEND_BACKEND_INTEGRATION_GR.md
git commit -m "Document the allergy UX frontend contract for the frontend integration guide"
```

---

## Verification (after all tasks)

- [ ] `python -m pytest tests -q` → 113 passed
- [ ] `git log --oneline -8` shows the 7 commits above on `main`
- [ ] Sanity: `python -c "from api.services.allergy_service import profile_cache, ProfileCache, PROFILE_CACHE_DIRTY_KEY"` exits 0 (run from `backend/`)
- [ ] Use superpowers:verification-before-completion before claiming done
