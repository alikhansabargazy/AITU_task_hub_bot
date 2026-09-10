from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime
from database.db_requests import get_schedule_by_day

router = Router()

# Этот хэндлер сработает только тогда, когда текст сообщения совпадет с названием кнопки
@router.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    user_id = message.from_user.id
    
    # Узнаем текущий день недели (1 - Понедельник, 7 - Воскресенье)
    today_weekday = datetime.now().isoweekday()
    
    # Идем в базу данных за парами на сегодня
    lessons = await get_schedule_by_day(user_id, today_weekday)
    
    # Если список пуст (пар нет или еще не добавили)
    if not lessons:
        await message.answer(
            "📅 <b>На сегодня пар нет!</b> (или они еще не добавлены)\n\n"
            "Добавь их через меню «➕ Добавить».", 
            parse_mode="HTML"
        )
        return

    # Если пары есть, красиво их оформляем
    text = "📅 <b>Твое расписание на сегодня:</b>\n\n"
    
    for i, lesson in enumerate(lessons, 1):
        # Если тип пары или аудитория не указаны, ставим заглушку
        lesson_type = lesson.lesson_type if lesson.lesson_type else 'Пара'
        location = lesson.location if lesson.location else 'Не указано'
        
        # Форматируем время в удобный вид Часы:Минуты
        start = lesson.start_time.strftime('%H:%M')
        end = lesson.end_time.strftime('%H:%M')
        
        text += (
            f"<b>{i}️⃣ {start} - {end}</b> | <b>{lesson.subject}</b> ({lesson_type})\n"
            f"📍 {location}\n"
            f"──────────────\n"
        )
        
    await message.answer(text, parse_mode="HTML")
