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
