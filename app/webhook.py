"""
HTTP endpoint for the payment gateway's success callback.
Runs as a small aiohttp web app alongside the bot's polling loop (see main.py).
"""

from aiohttp import web
from sqlalchemy import select

from app.db.models import Transaction, TransactionStatus, User
from app.db.session import SessionLocal
from app.db.repo import credit_user
from app.services.payment import payment_client


async def handle_payment_webhook(request: web.Request) -> web.Response:
    body = await request.read()
    signature = request.headers.get("Chapa-Signature", "")

    if not payment_client.verify_webhook_signature(body, signature):
        return web.json_response({"error": "invalid signature"}, status=401)

    payload = await request.json()
    tx_ref = payload.get("tx_ref")
    status = payload.get("status")

    if not tx_ref or status != "success":
        return web.json_response({"ok": True})  # acknowledge, nothing to do

    async with SessionLocal() as session:
        result = await session.execute(
            select(Transaction).where(Transaction.provider_ref == tx_ref)
        )
        transaction = result.scalar_one_or_none()

        if transaction is None or transaction.status == TransactionStatus.SUCCESS:
            return web.json_response({"ok": True})  # unknown or already processed

        user = await session.get(User, transaction.user_id)
        transaction.status = TransactionStatus.SUCCESS
        await credit_user(session, user, transaction.amount_birr, tx_ref)

    return web.json_response({"ok": True})


def build_webhook_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/payment/webhook", handle_payment_webhook)
    return app
