"""
Payment gateway client (Chapa example). Swap base_url/payload shape for
Telebirr/Santimpay if you use those instead - the interface (create_checkout /
verify_webhook) is what the rest of the bot depends on, so keep that stable.
"""

import hashlib
import hmac
from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class CheckoutSession:
    checkout_url: str
    tx_ref: str


class PaymentClient:
    def __init__(self) -> None:
        self._secret_key = settings.chapa_secret_key
        self._base_url = settings.chapa_base_url

    async def create_checkout(self, user_id: int, amount_birr: int, tx_ref: str) -> CheckoutSession:
        if not self._secret_key:
            # Dev/mock mode - no real gateway configured yet.
            return CheckoutSession(checkout_url=f"https://mock-checkout.example/{tx_ref}", tx_ref=tx_ref)

        async with httpx.AsyncClient(base_url=self._base_url, timeout=15) as client:
            resp = await client.post(
                "/transaction/initialize",
                headers={"Authorization": f"Bearer {self._secret_key}"},
                json={
                    "amount": str(amount_birr),
                    "currency": "ETB",
                    "tx_ref": tx_ref,
                    "customization": {"title": "Fayda Bot Topup"},
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return CheckoutSession(checkout_url=data["checkout_url"], tx_ref=tx_ref)

    def verify_webhook_signature(self, payload_body: bytes, signature_header: str) -> bool:
        expected = hmac.new(
            settings.payment_webhook_secret.encode(), payload_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header or "")


payment_client = PaymentClient()
