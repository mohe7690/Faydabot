from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repo import get_or_create_user
from app.db.session import SessionLocal
from app.keyboards import MAIN_MENU

router = Router(name="start")

WELCOME_TEXT = (
    "Welcome to Fayda Bot! 🇪🇹\n\n"
    "Please use the menu below to get started.\n\n"
    "• 📄 PDF Download: Get digital PDF (10 Birr)\n"
    "• 📄 Print with OTP: Printable cards via OTP (30 Birr)\n"
    "• 🗂️ Print with PDF: Extract from PDF (10 Birr)\n"
    "• 📸 Print with Screenshot: Extract from photo (10 Birr)\n"
    "• 💳 Topup: Add Birr\n"
    "• ℹ️ Help: Support and contact info"
)

HELP_TEXT = (
    "ℹ️ <b>Help & Support</b>\n\n"
    "This bot only processes YOUR OWN Fayda ID — you must confirm ownership and "
    "verify with an OTP sent to your own registered phone before anything is generated.\n\n"
    "Need help? Contact @your_support_handle\n"
    "Balance issues or failed payments? Include your Telegram username and the time of the transaction."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with SessionLocal() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer(WELCOME_TEXT, reply_markup=MAIN_MENU)


@router.message(Command("help"))
@router.callback_query(F.data == "menu:help")
async def show_help(event: Message | CallbackQuery) -> None:
    if isinstance(event, CallbackQuery):
        await event.message.answer(HELP_TEXT)
        await event.answer()
    else:
        await event.answer(HELP_TEXT)


@router.callback_query(F.data == "cancel")
async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Cancelled.", reply_markup=MAIN_MENU)
    await callback.answer()


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(WELCOME_TEXT, reply_markup=MAIN_MENU)
    await callback.answer()


@router.message(Command("balance"))
async def show_balance(message: Message) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer(f"💰 Your balance: {user.balance_birr} Birr")
