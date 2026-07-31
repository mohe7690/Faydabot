import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from app.config import settings
from app.db.models import Base
from app.db.session import engine
from app.handlers import pdf_download, print_otp, print_pdf, print_screenshot, start, topup
from app.webhook import build_webhook_app

logging.basicConfig(level=logging.INFO)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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

    await run_webhook_server()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
