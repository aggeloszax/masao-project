from __future__ import annotations

import logging
from html import escape

import httpx

from api.config import settings
from api.schemas.orders import TakeawayOrderLine

logger = logging.getLogger(__name__)

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
EMAIL_TIMEOUT_SECONDS = 15.0



class EmailUnavailableError(Exception):
    """Raised when the take-away notification could not be delivered."""


def notification_recipients() -> list[str]:
    """Split ORDER_NOTIFICATION_EMAIL into individual addresses.

    Args:
        None.

    Returns:
        list[str]: Every non-empty, comma-separated address, without duplicates.

    Raises:
        None.
    """
    raw = settings.order_notification_email or ""
    return list(dict.fromkeys(address.strip() for address in raw.split(",") if address.strip()))


def is_email_configured() -> bool:
    """Report whether outgoing order email is fully configured.

    Args:
        None.

    Returns:
        bool: True when an API key, a sender and a recipient all exist.

    Raises:
        None.
    """
    return (
        bool(settings.brevo_api_key)
        and bool(settings.order_from_email)
        and bool(notification_recipients())
    )


def build_order_subject(customer_name: str, total: float) -> str:
    """Build the notification subject line.

    Args:
        customer_name: Name the guest supplied.
        total: Order total in euro.

    Returns:
        str: Subject line for the restaurant inbox.

    Raises:
        None.
    """
    return f"Νέα παραγγελία take-away — {customer_name} — {total:.2f}€"


def build_order_text(
    customer_name: str,
    customer_phone: str,
    items: list[TakeawayOrderLine],
    total: float,
) -> str:
    """Render the plain-text body, which is what most phones show first.

    Args:
        customer_name: Name the guest supplied.
        customer_phone: Phone the guest supplied.
        items: Priced order lines.
        total: Order total in euro.

    Returns:
        str: Plain-text email body.

    Raises:
        None.
    """
    lines = [
        "ΝΕΑ ΠΑΡΑΓΓΕΛΙΑ TAKE-AWAY",
        "",
        f"Όνομα:    {customer_name}",
        f"Τηλέφωνο: {customer_phone}",
        "",
        "ΠΑΡΑΓΓΕΛΙΑ",
    ]
    for item in items:
        lines.append(f"  {item.quantity}x  {item.name}  —  {item.line_total:.2f}€")
        if item.note:
            lines.append(f"       Σημείωση: {item.note}")
    lines += ["", f"ΣΥΝΟΛΟ: {total:.2f}€"]
    return "\n".join(lines)


def build_order_html(
    customer_name: str,
    customer_phone: str,
    items: list[TakeawayOrderLine],
    total: float,
) -> str:
    """Render the HTML body.

    Args:
        customer_name: Name the guest supplied.
        customer_phone: Phone the guest supplied.
        items: Priced order lines.
        total: Order total in euro.

    Returns:
        str: HTML email body with guest input escaped.

    Raises:
        None.
    """
    rows = []
    for item in items:
        note = (
            f'<br><span style="color:#8b0000;font-size:13px">Σημείωση: {escape(item.note)}</span>'
            if item.note
            else ""
        )
        rows.append(
            '<tr>'
            f'<td style="padding:8px 0;border-bottom:1px solid #e5e7eb">'
            f'<strong>{item.quantity}×</strong> {escape(item.name)}{note}</td>'
            f'<td style="padding:8px 0;border-bottom:1px solid #e5e7eb;text-align:right;white-space:nowrap">'
            f'{item.line_total:.2f}€</td>'
            '</tr>'
        )

    # Ο τηλεφωνικός αριθμός είναι tel: link ώστε να καλείται με ένα άγγιγμα.
    phone_href = "".join(character for character in customer_phone if character.isdigit() or character == "+")

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#fafafa;font-family:system-ui,-apple-system,sans-serif;color:#111">
  <div style="max-width:520px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:24px">
    <p style="margin:0;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#8b0000">Masao</p>
    <h1 style="margin:6px 0 20px;font-size:22px">Νέα παραγγελία take-away</h1>

    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr><td style="padding:4px 0;color:#555">Όνομα</td>
          <td style="padding:4px 0;text-align:right"><strong>{escape(customer_name)}</strong></td></tr>
      <tr><td style="padding:4px 0;color:#555">Τηλέφωνο</td>
          <td style="padding:4px 0;text-align:right">
            <a href="tel:{escape(phone_href)}" style="color:#722f37"><strong>{escape(customer_phone)}</strong></a>
          </td></tr>
    </table>

    <table style="width:100%;border-collapse:collapse">{"".join(rows)}</table>

    <table style="width:100%;border-collapse:collapse;margin-top:16px;border-top:2px solid #111">
      <tr><td style="padding:12px 0;font-size:17px"><strong>Σύνολο</strong></td>
          <td style="padding:12px 0;text-align:right;font-size:22px;color:#722f37"><strong>{total:.2f}€</strong></td></tr>
    </table>
  </div>
</body></html>"""


async def send_takeaway_order_email(
    customer_name: str,
    customer_phone: str,
    items: list[TakeawayOrderLine],
    total: float,
) -> None:
    """Send the take-away notification to the restaurant.

    Args:
        customer_name: Name the guest supplied.
        customer_phone: Phone the guest supplied.
        items: Priced order lines.
        total: Order total in euro.

    Returns:
        None.

    Raises:
        EmailUnavailableError: If email is not configured or the provider rejects the send.
    """
    if not is_email_configured():
        raise EmailUnavailableError("BREVO_API_KEY, ORDER_FROM_EMAIL and ORDER_NOTIFICATION_EMAIL must all be set")

    payload = {
        "sender": {"name": settings.order_from_name, "email": settings.order_from_email},
        "to": [{"email": address} for address in notification_recipients()],
        "subject": build_order_subject(customer_name, total),
        "textContent": build_order_text(customer_name, customer_phone, items, total),
        "htmlContent": build_order_html(customer_name, customer_phone, items, total),
        # Το Brevo ξαναγράφει αποστολείς Gmail σε @...t-sender-sib.com, οπότε οι
        # απαντήσεις πρέπει να γυρίζουν στην πραγματική διεύθυνση.
        "replyTo": {"email": settings.order_from_email},
    }

    try:
        async with httpx.AsyncClient(timeout=EMAIL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                BREVO_ENDPOINT,
                headers={"api-key": settings.brevo_api_key, "accept": "application/json"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise EmailUnavailableError(f"Email provider unreachable: {exc}") from exc

    if response.status_code >= 400:
        # Το σώμα του Brevo εξηγεί τι έφταιξε (π.χ. μη επαληθευμένος αποστολέας, μπλοκαρισμένη IP).
        raise EmailUnavailableError(f"Email provider returned {response.status_code}: {response.text[:300]}")
