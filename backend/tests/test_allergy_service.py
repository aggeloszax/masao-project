import pytest
from sqlalchemy.exc import OperationalError

from api.services.allergy_service import AllergyService


class FailingSession:
    """Session stub: κάθε query αποτυγχάνει (π.χ. πίνακας δεν υπάρχει)."""

    def begin_nested(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def execute(self, statement, params=None):
        raise OperationalError("select 1", {}, Exception("relation does not exist"))


@pytest.mark.asyncio
async def test_try_get_customer_allergens_fails_open_on_db_error() -> None:
    service = AllergyService(session=FailingSession())

    allergens = await service.try_get_customer_allergens("device-12345")

    assert allergens == set()


@pytest.mark.asyncio
async def test_get_customer_allergens_propagates_db_error() -> None:
    service = AllergyService(session=FailingSession())

    with pytest.raises(OperationalError):
        await service.get_customer_allergens("device-12345")
