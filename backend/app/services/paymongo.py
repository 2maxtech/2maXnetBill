"""PayMongo API client for Checkout Sessions."""

import base64
import hashlib
import hmac
import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)

PAYMONGO_BASE_URL = "https://api.paymongo.com/v1"


def _auth_header(secret_key: str) -> dict:
    """Basic auth header for PayMongo API."""
    encoded = base64.b64encode(f"{secret_key}:".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def calculate_fee(amount: Decimal, fee_percent: Decimal, fee_flat: Decimal) -> Decimal:
    """Calculate convenience fee."""
    return (amount * fee_percent / Decimal("100")) + fee_flat


def calculate_total(amount: Decimal, fee_mode: str, fee_percent: Decimal, fee_flat: Decimal) -> tuple[Decimal, Decimal]:
    """Calculate total checkout amount and fee.
    Returns (total, fee). If absorb mode, fee is 0 and total = amount.
    """
    if fee_mode == "pass_to_customer":
        fee = calculate_fee(amount, fee_percent, fee_flat)
        return amount + fee, fee
    return amount, Decimal("0")


async def create_checkout_session(
    secret_key: str,
    amount_centavos: int,
    description: str,
    reference_number: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Create a PayMongo Checkout Session.

    Args:
        amount_centavos: Amount in centavos (e.g., 79900 for PHP 799.00)

    Returns:
        dict with 'checkout_url' and 'checkout_session_id'
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMONGO_BASE_URL}/checkout_sessions",
            headers={**_auth_header(secret_key), "Content-Type": "application/json"},
            json={
                "data": {
                    "attributes": {
                        "line_items": [
                            {
                                "name": description,
                                "amount": amount_centavos,
                                "currency": "PHP",
                                "quantity": 1,
                            }
                        ],
                        "payment_method_types": ["gcash", "paymaya", "card"],
                        "reference_number": reference_number,
                        "description": description,
                        "send_email_receipt": False,
                        "success_url": success_url,
                        "cancel_url": cancel_url,
                    }
                }
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return {
            "checkout_url": data["attributes"]["checkout_url"],
            "checkout_session_id": data["id"],
        }


def verify_webhook_signature(payload: bytes, signature_header: str, webhook_secret: str) -> bool:
    """Verify PayMongo webhook signature.

    PayMongo sends signatures in format: t=timestamp,te=test_signature,li=live_signature
    We verify against the appropriate signature using HMAC-SHA256.
    """
    try:
        parts = {}
        for part in signature_header.split(","):
            key, value = part.split("=", 1)
            parts[key] = value

        timestamp = parts.get("t", "")
        # Use live signature if available, otherwise test
        sig = parts.get("li") or parts.get("te", "")

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload.decode()}"
        expected = hmac.new(
            webhook_secret.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, sig)
    except Exception:
        logger.exception("Failed to verify PayMongo webhook signature")
        return False


async def test_connection(secret_key: str) -> bool:
    """Test if the PayMongo API key is valid."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYMONGO_BASE_URL}/payment_methods",
                headers=_auth_header(secret_key),
                timeout=10.0,
            )
            return response.status_code == 200
    except Exception:
        return False
