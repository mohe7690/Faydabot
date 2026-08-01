import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.models import Transaction, TransactionStatus, TransactionType
from app.db.repo import get_or_create_user
from app.db.session import SessionLocal
from app.keyboards import CANCEL_KB, MAIN_MENU, admin_review_kb, topup_amounts_kb
from app.states import TopupFlow

router = Router(name="topup")


@router.callback_query(F.data == "menu:topup")
async def start_topup(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TopupFlow.waiting_amount)
    await callback.message.answer("How much would you like to top up?", reply_markup=topup_amounts_kb())
    await callback.answer()


@router.callback_query(TopupFlow.waiting_amount, F.data.startswith("topup:"))
async def choose_amount(callback: CallbackQuery, state: FSMContext) -> None:
    amount = int(callback.data.split(":")[1])
    await state.update_data(amount=amount)
    await state.set_state(TopupFlow.waiting_proof)

    lines = [f"To top up {amount} Birr, transfer that amount to one of:"]
    if settings.telebirr_number:
        lines.append(f"\n📱 <b>Telebirr:</b> {settings.telebirr_number}")
        if settings.telebirr_name:
            lines.append(f"   Name: {settings.telebirr_name}")
    if settings.cbe_account_number:
        lines.append(f"\n🏦 <b>CBE:</b> {settings.cbe_account_number}")
        if settings.cbe_account_name:
            lines.append(f"   Name: {settings.cbe_account_name}")
    lines.append(
        "\nAfter transferring, send a screenshot of the confirmation "
        "(or type the transaction reference) here. Your balance will be "
        "credited once we verify the transfer — usually within a few minutes."
    )

    await callback.message.answer("\n".join(lines), reply_markup=CANCEL_KB)
    await callback.answer()


async def _record_pending_topup(
    message: Message, amount: int, proof_photo_file_id: str | None, proof_note: str | None
) -> Transaction:
    tx_ref = f"manual-{message.from_user.id}-{uuid.uuid4().hex[:8]}"
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        tx = Transaction(
            user_id=user.id,
            type=TransactionType.TOPUP,
            status=TransactionStatus.PENDING,
            amount_birr=amount,
            provider_ref=tx_ref,
            proof_photo_file_id=proof_photo_file_id,
            proof_note=proof_note,
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
    return tx


async def _notify_admins(message: Message, tx: Transaction, amount: int) -> None:
    if not settings.admin_telegram_ids:
        return
    caption = (
        f"💳 New topup request #{tx.id}\n"
        f"User: @{message.from_user.username or message.from_user.id} (id {message.from_user.id})\n"
        f"Amount: {amount} Birr"
    )
    if tx.proof_note:
        caption += f"\nNote: {tx.proof_note}"

    for admin_id in settings.admin_telegram_ids:
        try:
            if tx.proof_photo_file_id:
                await message.bot.send_photo(
                    admin_id, tx.proof_photo_file_id, caption=caption, reply_markup=admin_review_kb(tx.id)
                )
            else:
                await message.bot.send_message(admin_id, caption, reply_markup=admin_review_kb(tx.id))
        except Exception:
            # Don't let one admin's blocked/invalid chat break the flow for others.
            continue


@router.message(TopupFlow.waiting_proof, F.photo)
async def receive_proof_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    amount = data["amount"]
    photo_file_id = message.photo[-1].file_id
    note = message.caption

    tx = await _record_pending_topup(message, amount, photo_file_id, note)
    await _notify_admins(message, tx, amount)

    await state.clear()
    await message.answer(
        "✅ Received. We'll verify your transfer and credit your balance shortly.",
        reply_markup=MAIN_MENU,
    )


@router.message(TopupFlow.waiting_proof, F.text)
async def receive_proof_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    amount = data["amount"]
    note = message.text.strip()

    tx = await _record_pending_topup(message, amount, None, note)
    await _notify_admins(message, tx, amount)

    await state.clear()
    await message.answer(
        "✅ Received. We'll verify your transfer and credit your balance shortly.",
        reply_markup=MAIN_MENU,
    )


@router.message(TopupFlow.waiting_proof)
async def wrong_proof_type(message: Message) -> None:
    await message.answer("Please send a screenshot of the transfer, or type the transaction reference.")
