from aiogram.fsm.state import State, StatesGroup


class PdfDownloadFlow(StatesGroup):
    waiting_fan = State()
    waiting_otp = State()


class PrintOtpFlow(StatesGroup):
    waiting_fan = State()
    waiting_otp = State()


class PrintFromPdfFlow(StatesGroup):
    waiting_file = State()


class PrintFromScreenshotFlow(StatesGroup):
    waiting_photo = State()


class TopupFlow(StatesGroup):
    waiting_amount = State()
