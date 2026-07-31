import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.environ["BOT_TOKEN"]
    database_url: str = os.environ["DATABASE_URL"]

    price_pdf_download: int = int(os.getenv("PRICE_PDF_DOWNLOAD", "10"))
    price_print_otp: int = int(os.getenv("PRICE_PRINT_OTP", "30"))
    price_print_from_pdf: int = int(os.getenv("PRICE_PRINT_FROM_PDF", "10"))
    price_print_from_screenshot: int = int(os.getenv("PRICE_PRINT_FROM_SCREENSHOT", "10"))

    fayda_verify_base_url: str = os.getenv("FAYDA_VERIFY_BASE_URL", "")
    fayda_api_key: str = os.getenv("FAYDA_API_KEY", "")

    chapa_secret_key: str = os.getenv("CHAPA_SECRET_KEY", "")
    chapa_base_url: str = os.getenv("CHAPA_BASE_URL", "https://api.chapa.co/v1")
    payment_webhook_secret: str = os.getenv("PAYMENT_WEBHOOK_SECRET", "")

    admin_telegram_ids: list[int] = field(
        default_factory=lambda: _int_list(os.getenv("ADMIN_TELEGRAM_IDS", ""))
    )

    max_otp_attempts_per_hour: int = int(os.getenv("MAX_OTP_ATTEMPTS_PER_HOUR", "3"))


settings = Settings()
