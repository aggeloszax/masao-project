import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.dependencies import get_order_rate_limiter, get_order_service
from api.main import app
from api.schemas.orders import TakeawayOrderItemRequest, TakeawayOrderLine, TakeawayOrderRequest
from api.services.email_service import (
    build_order_html,
    build_order_subject,
    build_order_text,
    EmailUnavailableError,
    is_email_configured,
    send_takeaway_order_email,
)
from api.services.order_service import OrderValidationError, order_total, parse_numeric_ref
from api.services.rate_limiter import InMemoryRateLimiter


def line(**overrides) -> TakeawayOrderLine:
    values = {
        "menu_item_id": 1,
        "item_ref": "UR001",
        "name": "Cucumber Maki",
        "unit_price": 8.0,
        "quantity": 2,
        "note": "",
        "line_total": 16.0,
    }
    values.update(overrides)
    return TakeawayOrderLine(**values)


def test_parse_numeric_ref_accepts_positive_integers() -> None:
    assert parse_numeric_ref("131") == 131


def test_parse_numeric_ref_rejects_external_ids_and_zero() -> None:
    assert parse_numeric_ref("UR001") is None
    assert parse_numeric_ref("0") is None
    assert parse_numeric_ref("-3") is None
    assert parse_numeric_ref("") is None


def test_order_total_rounds_to_cents() -> None:
    lines = [line(unit_price=8.0, quantity=2, line_total=16.0), line(unit_price=3.33, quantity=3, line_total=9.99)]

    assert order_total(lines) == 25.99


def test_request_rejects_a_blank_name() -> None:
    with pytest.raises(ValidationError):
        TakeawayOrderRequest(
            customer_name="   ",
            customer_phone="6900000000",
            items=[TakeawayOrderItemRequest(item_ref="UR001", quantity=1)],
        )


def test_request_rejects_an_implausible_phone() -> None:
    with pytest.raises(ValidationError):
        TakeawayOrderRequest(
            customer_name="Άννα",
            customer_phone="abcdef",
            items=[TakeawayOrderItemRequest(item_ref="UR001", quantity=1)],
        )


def test_request_accepts_an_international_phone() -> None:
    request = TakeawayOrderRequest(
        customer_name="  Anna   Smith ",
        customer_phone=" +49 (30) 123-4567 ",
        items=[TakeawayOrderItemRequest(item_ref="UR001", quantity=1)],
    )

    assert request.customer_name == "Anna Smith"
    assert request.customer_phone == "+49 (30) 123-4567"


def test_request_rejects_duplicate_item_refs() -> None:
    with pytest.raises(ValidationError):
        TakeawayOrderRequest(
            customer_name="Άννα",
            customer_phone="6900000000",
            items=[
                TakeawayOrderItemRequest(item_ref="UR001", quantity=1),
                TakeawayOrderItemRequest(item_ref="UR001", quantity=2),
            ],
        )


def test_request_rejects_an_empty_order() -> None:
    with pytest.raises(ValidationError):
        TakeawayOrderRequest(
            customer_name="Άννα",
            customer_phone="6900000000",
            items=[],
        )


def test_request_ignores_a_pickup_slot_from_older_clients() -> None:
    # Η επιλογή ώρας αφαιρέθηκε· ένα frontend που δεν έχει ανανεωθεί ακόμα δεν πρέπει να σπάει.
    request = TakeawayOrderRequest(
        customer_name="Άννα",
        customer_phone="6900000000",
        pickup_slot="in_30",
        items=[TakeawayOrderItemRequest(item_ref="UR001", quantity=1)],
    )

    assert not hasattr(request, "pickup_slot")


def test_email_is_not_configured_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.services.email_service.settings.brevo_api_key", None)
    monkeypatch.setattr("api.services.email_service.settings.order_from_email", "me@example.com")
    monkeypatch.setattr("api.services.email_service.settings.order_notification_email", "owner@example.com")

    assert is_email_configured() is False


def test_email_is_not_configured_without_a_recipient(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.services.email_service.settings.brevo_api_key", "xkeysib-test")
    monkeypatch.setattr("api.services.email_service.settings.order_from_email", "me@example.com")
    monkeypatch.setattr("api.services.email_service.settings.order_notification_email", None)

    assert is_email_configured() is False


def test_email_is_not_configured_without_a_sender(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.services.email_service.settings.brevo_api_key", "xkeysib-test")
    monkeypatch.setattr("api.services.email_service.settings.order_from_email", None)
    monkeypatch.setattr("api.services.email_service.settings.order_notification_email", "owner@example.com")

    assert is_email_configured() is False


def configure_brevo(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    monkeypatch.setattr("api.services.email_service.settings.brevo_api_key", "xkeysib-test")
    monkeypatch.setattr("api.services.email_service.settings.order_from_email", "me@example.com")
    monkeypatch.setattr("api.services.email_service.settings.order_from_name", "Masao")
    monkeypatch.setattr("api.services.email_service.settings.order_notification_email", "owner@example.com")
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "api.services.email_service.httpx.AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )


@pytest.mark.asyncio
async def test_send_uses_the_brevo_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("api-key")
        seen["body"] = __import__("json").loads(request.content)
        return httpx.Response(201, json={"messageId": "<abc@brevo>"})

    configure_brevo(monkeypatch, handler)
    await send_takeaway_order_email("Άννα", "6900000000", [line()], 16.0)

    assert seen["url"] == "https://api.brevo.com/v3/smtp/email"
    assert seen["key"] == "xkeysib-test"
    assert seen["body"]["sender"] == {"name": "Masao", "email": "me@example.com"}
    assert seen["body"]["to"] == [{"email": "owner@example.com"}]
    assert seen["body"]["replyTo"] == {"email": "me@example.com"}
    assert "Cucumber Maki" in seen["body"]["textContent"]
    assert "Cucumber Maki" in seen["body"]["htmlContent"]


@pytest.mark.asyncio
async def test_send_notifies_every_comma_separated_recipient(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = __import__("json").loads(request.content)
        return httpx.Response(201, json={"messageId": "<abc@brevo>"})

    configure_brevo(monkeypatch, handler)
    monkeypatch.setattr(
        "api.services.email_service.settings.order_notification_email",
        " owner@example.com, kitchen@example.com ,,owner@example.com",
    )
    await send_takeaway_order_email("Άννα", "6900000000", [line()], 16.0)

    assert seen["body"]["to"] == [{"email": "owner@example.com"}, {"email": "kitchen@example.com"}]


@pytest.mark.asyncio
async def test_send_raises_when_brevo_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_brevo(monkeypatch, lambda request: httpx.Response(401, json={"code": "unauthorized"}))

    with pytest.raises(EmailUnavailableError, match="401"):
        await send_takeaway_order_email("Άννα", "6900000000", [line()], 16.0)


def test_order_subject_carries_the_name_and_total() -> None:
    assert build_order_subject("Άννα", 25.5) == "Νέα παραγγελία take-away — Άννα — 25.50€"


def test_order_text_lists_quantities_notes_and_total() -> None:
    body = build_order_text(
        "Άννα",
        "6900000000",
        [line(quantity=2, note="χωρίς κρεμμύδι")],
        16.0,
    )

    assert "Παραλαβή" not in body
    assert "2x  Cucumber Maki" in body
    assert "Σημείωση: χωρίς κρεμμύδι" in body
    assert "ΣΥΝΟΛΟ: 16.00€" in body


def test_order_html_escapes_guest_supplied_text() -> None:
    html = build_order_html(
        "<script>alert(1)</script>",
        "6900000000",
        [line(note="<b>bold</b>")],
        16.0,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html


def test_order_html_builds_a_dialable_phone_link() -> None:
    html = build_order_html("Άννα", "+30 (210) 123-4567", [line()], 16.0)

    assert 'href="tel:+302101234567"' in html


class FakeOrderService:
    """Stands in for the DB-backed service; records what the route did."""

    def __init__(self, lines=None, resolve_error: Exception | None = None) -> None:
        self.lines = lines if lines is not None else [line()]
        self.resolve_error = resolve_error
        self.created: list[tuple] = []
        self.notified: list = []
        self.email_failures: list[tuple] = []
        self.session = FakeSession()

    async def resolve_lines(self, items, language_code):
        if self.resolve_error is not None:
            raise self.resolve_error
        return self.lines

    async def create_order(self, request, lines, total):
        from uuid import UUID

        self.created.append((request.customer_name, total, len(lines)))
        return UUID("11111111-1111-1111-1111-111111111111")

    async def mark_notified(self, order_id):
        self.notified.append(order_id)

    async def mark_email_failed(self, order_id, reason):
        self.email_failures.append((order_id, reason))


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


def order_client(service: FakeOrderService, limiter: InMemoryRateLimiter | None = None) -> TestClient:
    app.dependency_overrides[get_order_service] = lambda: service
    app.dependency_overrides[get_order_rate_limiter] = lambda: limiter or InMemoryRateLimiter(
        limit=50, window_seconds=600, max_buckets=100
    )
    return TestClient(app)


def valid_payload(**overrides) -> dict:
    payload = {
        "customer_name": "Άννα",
        "customer_phone": "6900000000",
        "language_code": "el",
        "items": [{"item_ref": "UR001", "quantity": 2, "note": ""}],
    }
    payload.update(overrides)
    return payload


def test_order_route_stores_and_notifies(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict] = []

    async def fake_send(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr("api.routers.orders.send_takeaway_order_email", fake_send)
    service = FakeOrderService()
    try:
        with order_client(service) as client:
            response = client.post("/api/orders/takeaway", json=valid_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 16.0
    assert body["notified"] is True
    assert service.created == [("Άννα", 16.0, 1)]
    assert len(service.notified) == 1
    assert sent[0]["total"] == 16.0


def test_order_route_ignores_any_client_supplied_price(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_send(**kwargs):
        return None

    monkeypatch.setattr("api.routers.orders.send_takeaway_order_email", fake_send)
    service = FakeOrderService()
    payload = valid_payload()
    payload["items"][0]["unit_price"] = 0.01
    payload["total"] = 0.01

    try:
        with order_client(service) as client:
            response = client.post("/api/orders/takeaway", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    # Το σύνολο προκύπτει από τη βάση, όχι από το σώμα του request.
    assert response.json()["total"] == 16.0


def test_order_route_saves_the_order_before_the_email_is_attempted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api.services.email_service import EmailUnavailableError

    async def failing_send(**kwargs):
        raise EmailUnavailableError("domain not verified")

    monkeypatch.setattr("api.routers.orders.send_takeaway_order_email", failing_send)
    service = FakeOrderService()
    try:
        with order_client(service) as client:
            response = client.post("/api/orders/takeaway", json=valid_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert service.created, "the order must be persisted even when the email fails"
    assert service.email_failures[0][1] == "domain not verified"
    assert service.notified == []


def test_order_route_rejects_unknown_items(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeOrderService(resolve_error=OrderValidationError("Unknown menu item: XX999"))
    try:
        with order_client(service) as client:
            response = client.post("/api/orders/takeaway", json=valid_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert service.created == []


def test_order_route_rate_limits_repeated_submissions(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_send(**kwargs):
        return None

    monkeypatch.setattr("api.routers.orders.send_takeaway_order_email", fake_send)
    limiter = InMemoryRateLimiter(limit=1, window_seconds=600, max_buckets=100)
    service = FakeOrderService()
    try:
        with order_client(service, limiter) as client:
            first = client.post("/api/orders/takeaway", json=valid_payload())
            second = client.post("/api/orders/takeaway", json=valid_payload())
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert second.status_code == 429
    assert len(service.created) == 1
