from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Document, Message

from app.config import settings
from app.db.models import OrderStatus, OrderType
from app.db.repo import charge_user, create_order, get_or_create_user
from app.db.session import SessionLocal
from app.keyboards import CANCEL_KB, MAIN_MENU
from app.services.extract import extract_from_pdf
from app.services.pdf_generator import build_print_sheet_pdf
from app.states import PrintFromPdfFlow

router = Router(name="print_pdf")

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.callback_query(F.data == "menu:print_pdf")
async def start_print_pdf(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PrintFromPdfFlow.waiting_file)
    await callback.message.answer(
        "Please upload the PDF you'd like formatted for printing.",
        reply_markup=CANCEL_KB,
    )
    await callback.answer()


@router.message(PrintFromPdfFlow.waiting_file, F.document)
async def receive_pdf(message: Message, state: FSMContext) -> None:
    document: Document = message.document
    if document.mime_type != "application/pdf":
        await message.answer("Please upload a valid PDF file.")
        return
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer("File too large (max 10MB). Please upload a smaller PDF.")
        return

    file = await message.bot.get_file(document.file_id)
    buffer = await message.bot.download_file(file.file_path)
    pdf_bytes = buffer.read()

    try:
        profile = extract_from_pdf(pdf_bytes)
    except Exception:
        await message.answer("Couldn't read that PDF. Please make sure it's not corrupted or encrypted.")
        return

    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        price = settings.price_print_from_pdf

        if user.balance_birr < price:
            await state.clear()
            await message.answer(
                f"Your balance ({user.balance_birr} Birr) is too low (need {price} Birr). "
                "Please Topup first.",
                reply_markup=MAIN_MENU,
            )
            return

        order = await create_order(
            session, user_id=user.id, order_type=OrderType.PRINT_FROM_PDF, amount_birr=price
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


@router.message(PrintFromPdfFlow.waiting_file)
async def wrong_content_type(message: Message) -> None:
    await message.answer("Please upload the file as a PDF document, or press Cancel.")
