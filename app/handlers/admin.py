from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import settings
from app.db.repo import approve_topup, get_pending_transaction, reject_topup
from app.db.session import SessionLocal

router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_telegram_ids


@router.callback_query(F.data.startswith("admin_approve:"))
async def handle_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Not authorized.", show_alert=True)
        return

    tx_id = int(callback.data.split(":")[1])
    async with SessionLocal() as session:
        tx = await get_pending_transaction(session, tx_id)
        if tx is None:
            await callback.answer("Already handled or not found.", show_alert=True)
            return
        await approve_topup(session, tx, callback.from_user.id)
        user_id = tx.user_id
        amount = tx.amount_birr

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Approved")
    else:
        await callback.message.edit_text((callback.message.text or "") + "\n\n✅ Approved")
    await callback.answer("Approved.")

    try:
        await callback.bot.send_message(
            user_id, f"✅ Your topup of {amount} Birr has been confirmed and added to your balance."
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_reject:"))
async def handle_reject(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Not authorized.", show_alert=True)
        return

    tx_id = int(callback.data.split(":")[1])
    async with SessionLocal() as session:
        tx = await get_pending_transaction(session, tx_id)
        if tx is None:
            await callback.answer("Already handled or not found.", show_alert=True)
            return
        await reject_topup(session, tx, callback.from_user.id)
        user_id = tx.user_id

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rejected")
    else:
        await callback.message.edit_text((callback.message.text or "") + "\n\n❌ Rejected")
    await callback.answer("Rejected.")

    try:
        await callback.bot.send_message(
            user_id, "❌ We couldn't verify your recent transfer. Please try again or contact support."
        )
    except Exception:
        pass
