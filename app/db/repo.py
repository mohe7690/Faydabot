from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Order,
    OrderStatus,
    OrderType,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        user = User(id=telegram_id, username=username, balance_birr=0)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def create_order(
    session: AsyncSession, user_id: int, order_type: OrderType, amount_birr: int, fan_last4: str | None = None
) -> Order:
    order = Order(
        user_id=user_id,
        order_type=order_type,
        amount_birr=amount_birr,
        status=OrderStatus.PENDING,
        fan_last4=fan_last4,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def charge_user(session: AsyncSession, user: User, amount_birr: int) -> bool:
    """Deduct balance atomically. Returns False if insufficient funds."""
    if user.balance_birr < amount_birr:
        return False
    user.balance_birr -= amount_birr
    session.add(
        Transaction(
            user_id=user.id,
            type=TransactionType.CHARGE,
            status=TransactionStatus.SUCCESS,
            amount_birr=amount_birr,
        )
    )
    await session.commit()
    return True


async def credit_user(session: AsyncSession, user: User, amount_birr: int, provider_ref: str) -> None:
    user.balance_birr += amount_birr
    session.add(
        Transaction(
            user_id=user.id,
            type=TransactionType.TOPUP,
            status=TransactionStatus.SUCCESS,
            amount_birr=amount_birr,
            provider_ref=provider_ref,
        )
    )
    await session.commit()


async def recent_otp_attempt_count(session: AsyncSession, user_id: int, since) -> int:
    result = await session.execute(
        select(Order).where(
            Order.user_id == user_id,
            Order.created_at >= since,
            Order.status.in_([OrderStatus.AWAITING_OTP, OrderStatus.FAILED]),
        )
    )
    return len(result.scalars().all())
