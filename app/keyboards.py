from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📄 PDF Download (10 Birr)", callback_data="menu:pdf_download")],
        [InlineKeyboardButton(text="📄 Print with OTP (30 Birr)", callback_data="menu:print_otp")],
        [InlineKeyboardButton(text="🗂️ Print with PDF (10 Birr)", callback_data="menu:print_pdf")],
        [InlineKeyboardButton(text="📸 Print with Screenshot (10 Birr)", callback_data="menu:print_screenshot")],
        [InlineKeyboardButton(text="💳 Topup", callback_data="menu:topup")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="menu:help")],
    ]
)

CANCEL_KB = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]]
)


def topup_amounts_kb() -> InlineKeyboardMarkup:
    amounts = [50, 100, 200, 500]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{a} Birr", callback_data=f"topup:{a}") for a in amounts],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")],
        ]
    )
