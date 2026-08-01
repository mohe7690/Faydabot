import re
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.config import settings
from app.db.models import Order, OrderStatus, OrderType
from app.db.repo import (
    charge_user,
    create_order,
    get_or_create_user,
    recent_otp_attempt_count,
)
from app.db.session import SessionLocal
from app.keyboards import CANCEL_KB, MAIN_MENU
from app.services.fayda import FaydaVerificationError, fayda_client
from app.services.pdf_generator import build_card_pdf
from app.states import PdfDownloadFlow

router = Router(name="pdf_download")

FAN_PATTERN = re.compile(r"^\d{10,16}$")


@router.callback_query(F.data == "menu:pdf_download")
async def start_pdf_download(callback: CallbackQuery, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        attempts = await recent_otp_attempt_count(session, user.id, since)
        if attempts >= settings.max_otp_attempts_per_hour:
            await callback.message.answer(
                "Too many verification attempts recently. Please try again later.",
                reply_markup=MAIN_MENU,
            )
            await callback.answer()
            return

    await state.set_state(PdfDownloadFlow.waiting_fan)
    await callback.message.answer(
        "Please enter your <b>own</b> FAN (Fayda ID number) to continue.\n"
        "By proceeding you confirm this is your own ID.",
        reply_markup=CANCEL_KB,
    )
    await callback.answer()


@router.message(PdfDownloadFlow.waiting_fan)
async def receive_fan(message: Message, state: FSMContext) -> None:
    fan = message.text.strip()
    if not FAN_PATTERN.match(fan):
        await message.answer("That doesn't look like a valid FAN. Please re-enter, or press Cancel.")
        return

    session_id = await fayda_client.send_otp(fan)

    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        order = await create_order(
            session,
            user_id=user.id,
            order_type=OrderType.PDF_DOWNLOAD,
            amount_birr=settings.price_pdf_download,
            fan_last4=fan[-4:],
        )
        order.status = OrderStatus.AWAITING_OTP
        await session.commit()

    await state.update_data(fan=fan, session_id=session_id, order_id=order.id)
    await state.set_state(PdfDownloadFlow.waiting_otp)
    await message.answer("An OTP was sent to the phone registered to this FAN. Please enter it here.")


@router.message(PdfDownloadFlow.waiting_otp)
async def receive_otp(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    otp_code = message.text.strip()

    try:
        profile = await fayda_client.confirm_otp(data["session_id"], otp_code)
    except FaydaVerificationError as exc:
        async with SessionLocal() as session:
            order = await session.get(Order, data["order_id"])
            if order:
                order.otp_attempts += 1
                order.status = OrderStatus.FAILED
                await session.commit()
        await message.answer(f"❌ {exc}. Please try again or press Cancel.")
        return

    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        price = settings.price_pdf_download

        if user.balance_birr < price:
            await state.clear()
            await message.answer(
                f"✅ Verified, but your balance ({user.balance_birr} Birr) is too low "
                f"(need {price} Birr). Please Topup first.",
                reply_markup=MAIN_MENU,
            )
            return

        charged = await charge_user(session, user, price)
        if not charged:
            await message.answer("Payment failed, please try again.", reply_markup=MAIN_MENU)
            await state.clear()
            return

        order = await session.get(Order, data["order_id"])
        if order:
            order.status = OrderStatus.DELIVERED
            order.delivered_at = datetime.now(timezone.utc)
            await session.commit()

    pdf_bytes = build_card_pdf(profile)
    await message.answer_document(
        BufferedInputFile(pdf_bytes, filename="fayda_id.pdf"),
        caption="✅ Here is your Fayda ID PDF.",
        reply_markup=MAIN_MENU,
    )
    await state.clear()
