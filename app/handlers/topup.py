import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.db.models import Transaction, TransactionStatus, TransactionType
from app.db.repo import get_or_create_user
from app.db.session import SessionLocal
from app.keyboards import MAIN_MENU, topup_amounts_kb
from app.services.payment import payment_client
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
    tx_ref = f"topup-{callback.from_user.id}-{uuid.uuid4().hex[:8]}"

    async with SessionLocal() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        session.add(
            Transaction(
                user_id=user.id,
                type=TransactionType.TOPUP,
                status=TransactionStatus.PENDING,
                amount_birr=amount,
                provider_ref=tx_ref,
            )
        )
        await session.commit()

    checkout = await payment_client.create_checkout(callback.from_user.id, amount, tx_ref)

    await state.clear()
    await callback.message.answer(
        f"Tap below to pay {amount} Birr. Your balance updates automatically once payment completes.\n\n"
        f"{checkout.checkout_url}",
        reply_markup=MAIN_MENU,
    )
    await callback.answer()
