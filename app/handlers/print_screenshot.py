from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.config import settings
from app.db.models import OrderStatus, OrderType
from app.db.repo import charge_user, create_order, get_or_create_user
from app.db.session import SessionLocal
from app.keyboards import CANCEL_KB, MAIN_MENU
from app.services.extract import extract_from_image
from app.services.pdf_generator import build_print_sheet_pdf
from app.states import PrintFromScreenshotFlow

router = Router(name="print_screenshot")


@router.callback_query(F.data == "menu:print_screenshot")
async def start_print_screenshot(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrintFromScreenshotFlow.waiting_photo)
    await callback.message.answer(
        "Please send a clear photo/screenshot of your Fayda ID.",
        reply_markup=CANCEL_KB,
    )
    await callback.answer()


@router.message(PrintFromScreenshotFlow.waiting_photo, F.photo)
async def receive_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]  # highest resolution
    file = await message.bot.get_file(photo.file_id)
    buffer = await message.bot.download_file(file.file_path)
    image_bytes = buffer.read()

    try:
        profile = extract_from_image(image_bytes)
    except Exception:
        await message.answer("Couldn't read text from that image. Please try a clearer photo.")
        return

    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        price = settings.price_print_from_screenshot

        if user.balance_birr < price:
            await state.clear()
            await message.answer(
                f"Your balance ({user.balance_birr} Birr) is too low (need {price} Birr). "
                "Please Topup first.",
                reply_markup=MAIN_MENU,
            )
            return

        order = await create_order(
            session, user_id=user.id, order_type=OrderType.PRINT_FROM_SCREENSHOT, amount_birr=price
        )
        charged = await charge_user(session, user, price)
        if not charged:
            await message.answer("Payment failed, please try again.", reply_markup=MAIN_MENU)
            await state.clear()
            return
        order.status = OrderStatus.DELIVERED
        await session.commit()

    sheet_bytes = build_print_sheet_pdf(profile)
    await message.answer_document(
        BufferedInputFile(sheet_bytes, filename="print_sheet.pdf"),
        caption="✅ Print-ready sheet generated.",
        reply_markup=MAIN_MENU,
    )
    await state.clear()


@router.message(PrintFromScreenshotFlow.waiting_photo)
async def wrong_content_type(message: Message) -> None:
    await message.answer("Please send a photo, or press Cancel.")
