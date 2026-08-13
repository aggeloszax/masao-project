import pytest

from api.services import menu_service
from api.services.menu_service import menu_cache


@pytest.fixture(autouse=True)
def isolate_process_caches():
    """Reset τα process-global caches/locks γύρω από κάθε test.

    Χωρίς αυτό, ένα test που γεμίζει cache (TTL 60s) θα σέρβιρε τα δεδομένα
    του σε επόμενα tests, και ένα asyncio.Lock δεμένο στο event loop ενός
    test θα διέρρεε στο loop του επόμενου.
    """
    menu_cache.invalidate()
    menu_service._fetch_locks.clear()
    yield
    menu_cache.invalidate()
    menu_service._fetch_locks.clear()
