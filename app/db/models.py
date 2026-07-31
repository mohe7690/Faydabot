import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OrderType(str, enum.Enum):
    PDF_DOWNLOAD = "pdf_download"
    PRINT_OTP = "print_otp"
    PRINT_FROM_PDF = "print_from_pdf"
    PRINT_FROM_SCREENSHOT = "print_from_screenshot"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    AWAITING_OTP = "awaiting_otp"
    VERIFIED = "verified"
    DELIVERED = "delivered"
    FAILED = "failed"


class TransactionType(str, enum.Enum):
    TOPUP = "topup"
    CHARGE = "charge"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # telegram user id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance_birr: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    amount_birr: Mapped[int] = mapped_column(Integer)

    # Deliberately NOT storing raw FAN numbers or ID data long-term.
    # fan_last4 lets support staff reference an order without holding the full number.
    fan_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)

    otp_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    amount_birr: Mapped[int] = mapped_column(Integer)
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")
