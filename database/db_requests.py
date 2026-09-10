from sqlalchemy import select
from database.models import async_session, User, Schedule

# ==========================================
# 👤 ФУНКЦИИ ПОЛЬЗОВАТЕЛЯ
# ==========================================

async def add_user(user_id: int):
    """
    Добавляет пользователя в БД при первом запуске бота (команда /start).
    Если пользователь уже существует, ничего не делает.
    """
    async with async_session() as session:
        # Пытаемся найти пользователя в базе
        user = await session.scalar(select(User).where(User.user_id == user_id))
        
        # Если пользователя нет (scalar вернул None), создаем его
        if not user:
            session.add(User(user_id=user_id))
            await session.commit() # Сохраняем изменения в базе

# ==========================================
# 📅 ФУНКЦИИ РАСПИСАНИЯ
# ==========================================

async def add_lesson(user_id: int, subject: str, day_of_week: int, start_time, end_time, lesson_type: str = None, location: str = None):
    """
    Добавляет новую пару в расписание студента.
    """
    async with async_session() as session:
        new_lesson = Schedule(
            user_id=user_id,
            subject=subject,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            lesson_type=lesson_type,
            location=location
        )
        session.add(new_lesson)
        await session.commit()

async def get_schedule_by_day(user_id: int, day_of_week: int):
    """
    Достает все пары пользователя на конкретный день недели.
    Пары автоматически сортируются по времени начала.
    """
    async with async_session() as session:
        # Формируем SQL-запрос
        query = (
            select(Schedule)
            .where(Schedule.user_id == user_id)
            .where(Schedule.day_of_week == day_of_week)
            .order_by(Schedule.start_time) # Сортировка по времени
        )
        
        # Выполняем запрос и получаем результат
        result = await session.scalars(query)
        
        # Возвращаем список всех найденных пар
        return result.all()

# Добавить в конец файла database/db_requests.py:

async def get_lessons_for_notification(day_of_week: int, target_time):
    """
    Ищет все пары, которые начинаются в определенное время в заданный день недели.
    """
    async with async_session() as session:
        query = (
            select(Schedule)
            .where(Schedule.day_of_week == day_of_week)
            .where(Schedule.start_time == target_time)
        )
        result = await session.scalars(query)
        return result.all()