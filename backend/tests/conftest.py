import pytest

from api.services.menu_service import menu_cache


@pytest.fixture(autouse=True)
def isolate_menu_cache():
    """Reset the process-global menu cache around every test.

    Χωρίς αυτό, ένα test που γεμίζει το cache (TTL 60s) θα σέρβιρε τα rows
    του σε επόμενα tests της ίδιας διεργασίας.
    """
    menu_cache.invalidate()
    yield
    menu_cache.invalidate()
