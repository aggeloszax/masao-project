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
