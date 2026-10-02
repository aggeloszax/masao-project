from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.schemas.orders import TakeawayOrderItemRequest, TakeawayOrderLine, TakeawayOrderRequest

logger = logging.getLogger(__name__)


class OrderValidationError(Exception):
    """Raised when the requested lines cannot be turned into a real order."""


def parse_numeric_ref(item_ref: str) -> int | None:
    """Read an item reference as a menu_items primary key, when it is one.

    Το καλάθι κρατά το external_id ('UR001'), αλλά πιάτα που δημιουργήθηκαν
    από το admin δεν έχουν external_id και το frontend πέφτει στο αριθμητικό
    id. Δες `mapItem` στο frontend/src/lib/menu-api.ts.

    Args:
        item_ref: Reference sent by the client.

    Returns:
        int | None: The numeric id, or None when the ref is not numeric.

    Raises:
        None.
    """
    if not item_ref.isdigit():
        return None
    parsed = int(item_ref)
    return parsed if parsed > 0 else None


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve_lines(
        self,
        items: list[TakeawayOrderItemRequest],
        language_code: str,
    ) -> list[TakeawayOrderLine]:
        """Price the requested lines from the menu, in the guest's language.

        Οι τιμές διαβάζονται ΠΑΝΤΑ από τη βάση: ό,τι τιμή κι αν στείλει ο
        client αγνοείται, αλλιώς οποιοσδήποτε θα μπορούσε να παραγγείλει με
        δικό του σύνολο.

        Args:
            items: Requested lines.
            language_code: Language used for the item names in the email.

        Returns:
            list[TakeawayOrderLine]: Priced lines in the requested order.

        Raises:
            OrderValidationError: If a reference is unknown or the item is unavailable.
        """
        if len(items) > settings.order_max_items:
            raise OrderValidationError(f"An order cannot hold more than {settings.order_max_items} items")

        for item in items:
            if item.quantity > settings.order_max_quantity_per_item:
                raise OrderValidationError(
                    f"Quantity for {item.item_ref} exceeds {settings.order_max_quantity_per_item}"
                )

        refs = [item.item_ref for item in items]
        numeric_ids = [parsed for parsed in (parse_numeric_ref(ref) for ref in refs) if parsed is not None]

        result = await self.session.execute(
            text(
                """
                select
                    mi.id,
                    mi.external_id,
                    coalesce(mit.name, mi.name) as name,
                    mi.price,
                    mi.is_available
                from menu_items mi
                left join menu_item_translations mit
                    on mit.menu_item_id = mi.id
                   and mit.language_code = :language_code
                where mi.external_id = any(cast(:refs as text[]))
                   or mi.id = any(cast(:numeric_ids as int[]))
                """
            ),
            {"language_code": language_code, "refs": refs, "numeric_ids": numeric_ids},
        )

        by_ref: dict[str, dict] = {}
        for row in result.mappings().all():
            record = dict(row)
            if record["external_id"]:
                by_ref[record["external_id"]] = record
            by_ref[str(record["id"])] = record

        lines: list[TakeawayOrderLine] = []
        for item in items:
            record = by_ref.get(item.item_ref)
            if record is None:
                raise OrderValidationError(f"Unknown menu item: {item.item_ref}")
            if not record["is_available"]:
                raise OrderValidationError(f"Item is no longer available: {record['name']}")

            unit_price = round(float(record["price"]), 2)
            lines.append(
                TakeawayOrderLine(
                    menu_item_id=record["id"],
                    item_ref=item.item_ref,
                    name=record["name"],
                    unit_price=unit_price,
                    quantity=item.quantity,
                    note=item.note,
                    line_total=round(unit_price * item.quantity, 2),
                )
            )
        return lines

    async def create_order(
        self,
        request: TakeawayOrderRequest,
        lines: list[TakeawayOrderLine],
        total: float,
    ) -> UUID:
        """Persist the order before any email is attempted.

        Args:
            request: Validated guest payload.
            lines: Priced order lines.
            total: Server-computed total.

        Returns:
            UUID: Stored order id.

        Raises:
            SQLAlchemyError: Propagated by SQLAlchemy if persistence fails.
        """
        result = await self.session.execute(
            text(
                """
                insert into takeaway_orders (
                    customer_name, customer_phone, pickup_slot, language_code, items, total
                )
                values (
                    :customer_name, :customer_phone, :pickup_slot, :language_code,
                    cast(:items as jsonb), :total
                )
                returning id
                """
            ),
            {
                "customer_name": request.customer_name,
                "customer_phone": request.customer_phone,
                # Η επιλογή ώρας αφαιρέθηκε· η στήλη είναι not null, οπότε κάθε
                # παραγγελία καταγράφεται ως "το συντομότερο".
                "pickup_slot": "asap",
                "language_code": request.language_code,
                "items": json.dumps([line.model_dump() for line in lines], ensure_ascii=False),
                "total": total,
            },
        )
        return result.scalar_one()

    async def mark_notified(self, order_id: UUID) -> None:
        """Record that the restaurant was emailed about this order."""
        await self.session.execute(
            text("update takeaway_orders set notified_at = now(), email_error = null where id = :order_id"),
            {"order_id": order_id},
        )

    async def mark_email_failed(self, order_id: UUID, reason: str) -> None:
        """Record why the notification could not be delivered."""
        await self.session.execute(
            text("update takeaway_orders set email_error = :reason where id = :order_id"),
            {"order_id": order_id, "reason": reason[:1000]},
        )


def order_total(lines: list[TakeawayOrderLine]) -> float:
    """Sum the priced lines.

    Args:
        lines: Priced order lines.

    Returns:
        float: Order total rounded to cents.

    Raises:
        None.
    """
    return round(sum(line.line_total for line in lines), 2)
