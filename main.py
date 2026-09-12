import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import CallbackQuery, Message

from config import BOT_TOKEN
from database.models import async_main, engine
from handlers.add_menu import router as add_menu_router
from handlers.dashboard import router as dashboard_router
from handlers.schedule import router as schedule_router
from handlers.settings import router as settings_router
from handlers.start import router as start_router
from handlers.tasks import router as tasks_router
from services.i18n import LocaleMiddleware, main_keyboard, tr
from services.scheduler import setup_scheduler


def create_dispatcher():
    dp = Dispatcher(events_isolation=SimpleEventIsolation())
    dp.message.outer_middleware(LocaleMiddleware())
    dp.callback_query.outer_middleware(LocaleMiddleware())
    # Global commands and menu navigation must run before wizard input handlers.
    dp.include_routers(
        start_router,
        dashboard_router,
        settings_router,
        add_menu_router,
        schedule_router,
        tasks_router,
    )
    from aiogram import Router

    fallback = Router()

    @fallback.message()
    async def unknown_message(message: Message):
        await message.answer(
            tr("Выберите раздел в меню. /cancel — отменить ввод."),
            reply_markup=main_keyboard(),
        )

    @fallback.callback_query()
    async def stale_callback(callback: CallbackQuery):
        await callback.answer(
            tr("Эта кнопка устарела. Откройте раздел заново."), show_alert=True
        )

    dp.include_router(fallback)
    return dp


async def main():
    await async_main()
    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()
    scheduler = setup_scheduler(bot)
    try:
        logging.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
