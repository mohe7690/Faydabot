import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from sqlalchemy import text

from app.config import settings
from app.db.models import Base
from app.db.session import engine
from app.handlers import admin, pdf_download, print_otp, print_pdf, print_screenshot, start, topup
from app.webhook import build_webhook_app

logging.basicConfig(level=logging.INFO)

# Lightweight, additive-only "migration" list. Each entry is safe to re-run
# every startup (IF NOT EXISTS guards it) and only ever adds columns, never
# drops or alters existing data. This isn't a substitute for real migrations
# long-term, but avoids needing shell/psql access for now.
_STARTUP_COLUMN_PATCHES = [
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS proof_photo_file_id VARCHAR(256)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS proof_note VARCHAR(256)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS reviewed_by BIGINT",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ",
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for statement in _STARTUP_COLUMN_PATCHES:
            await conn.execute(text(statement))


async def run_webhook_server() -> None:
    app = build_webhook_app()
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logging.info("Payment webhook server listening on :%s", port)


async def main() -> None:
    await init_db()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(pdf_download.router)
    dp.include_router(print_otp.router)
    dp.include_router(print_pdf.router)
    dp.include_router(print_screenshot.router)
    dp.include_router(topup.router)
    dp.include_router(admin.router)

    await run_webhook_server()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
