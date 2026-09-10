import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.models import async_main

from handlers.start import router as start_router
from handlers.schedule import router as schedule_router
from handlers.add_menu import router as add_menu_router
from services.scheduler import setup_scheduler  # <-- Импортируем планировщик

async def main():
    await async_main()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(start_router)
    dp.include_router(schedule_router)
    dp.include_router(add_menu_router)
    
    # Запускаем фоновый планировщик уведомлений
    setup_scheduler(bot)
    
    print("Бот успешно запущен и ждет сообщений...")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
