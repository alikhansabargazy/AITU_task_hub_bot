from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.db_requests import get_lessons_for_notification

async def check_upcoming_lessons(bot: Bot):
    now = datetime.now()
    current_weekday = now.isoweekday()
    target_time = (now + timedelta(minutes=15)).replace(second=0, microsecond=0).time()
    
    # ПРИНТ ДЛЯ ОТЛАДКИ: Посмотрим, что ищет бот прямо сейчас
    print(f"[DEBUG] Ищу пары на день {current_weekday} со временем старта: {target_time}")
    
    lessons = await get_lessons_for_notification(current_weekday, target_time)
    print(f"[DEBUG] Найдено пар: {len(lessons)}")
    
    for lesson in lessons:
        start_str = lesson.start_time.strftime('%H:%M')
        end_str = lesson.end_time.strftime('%H:%M')
        location = lesson.location if lesson.location else "Не указана"
        
        text = (
            f"🔔 <b>СКОРО ПАРА (через 15 минут)!</b>\n\n"
            f"📚 Предмет: <b>{lesson.subject}</b>\n"
            f"⏰ Время: {start_str} – {end_str}\n"
            f"📍 Где: {location}\n\n"
            f"<i>Пора собираться! 🏃‍♂️</i>"
        )
        
        try:
            await bot.send_message(lesson.user_id, text, parse_mode="HTML")
            print(f"[DEBUG] Уведомление успешно отправлено юзеру {lesson.user_id}!")
        except Exception as e:
            print(f"[ERROR] Не удалось отправить: {e}")
def setup_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty") # Укажи свой часовой пояс
    
    # Добавляем задачу: запускать функцию check_upcoming_lessons каждую минуту (* * * * *)
    scheduler.add_job(check_upcoming_lessons, 'interval', minutes=1, args=[bot])
    
    scheduler.start()
    print("⏰ Планировщик уведомлений успешно запущен!")
