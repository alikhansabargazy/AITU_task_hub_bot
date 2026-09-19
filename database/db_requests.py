from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select

from database.models import Schedule, Task, User, async_session
from services.i18n import tr


async def get_user(user_id):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            # SQLite upsert also handles concurrent first requests.
            from sqlalchemy.dialects.sqlite import insert

            await session.execute(
                insert(User).values(user_id=user_id).on_conflict_do_nothing()
            )
            await session.commit()
            user = await session.get(User, user_id)
        return user


async def add_user(user_id):
    return await get_user(user_id)


async def update_user(user_id, **fields):
    allowed = {
        "timezone",
        "language",
        "notifications_enabled",
        "reminder_minutes",
        "week_parity_offset",
        "dashboard_days",
    }
    if not fields.keys() <= allowed:
        raise ValueError("Неизвестная настройка.")
    if "timezone" in fields:
        ZoneInfo(fields["timezone"])
    for key, choices in [
        ("language", ("ru", "en", "kk")),
        ("reminder_minutes", (0, 5, 10, 15, 30, 60)),
        ("week_parity_offset", (0, 1)),
        ("dashboard_days", (1, 3, 7, 14)),
    ]:
        if key in fields and fields[key] not in choices:
            raise ValueError("Недопустимое значение настройки.")
    if "notifications_enabled" in fields and not isinstance(
        fields["notifications_enabled"], bool
    ):
        raise ValueError("Недопустимое значение уведомлений.")
    await get_user(user_id)
    async with async_session() as session:
        user = await session.get(User, user_id)
        for key, value in fields.items():
            setattr(user, key, value)
        await session.commit()
        return user


def _string(value, limit, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(tr("Введите текст от 1 до {limit} символов.", limit=limit))
    return value.strip()


async def _validate_lesson(session, lesson):
    lesson.subject = _string(lesson.subject, 100, True)
    for field, limit in [("location", 100), ("teacher", 100), ("lesson_type", 50)]:
        setattr(lesson, field, _string(getattr(lesson, field), limit))
    if lesson.day_of_week not in range(1, 8) or lesson.parity not in (
        "all",
        "numerator",
        "denominator",
    ):
        raise ValueError(tr("Проверьте день недели и чётность."))
    if (
        not isinstance(lesson.start_time, time)
        or not isinstance(lesson.end_time, time)
        or lesson.end_time <= lesson.start_time
    ):
        raise ValueError(tr("Конец пары должен быть позже начала в тот же день."))
    with session.no_autoflush:
        others = await session.scalars(
            select(Schedule).where(
                Schedule.user_id == lesson.user_id,
                Schedule.day_of_week == lesson.day_of_week,
            )
        )
        for other in others:
            if other.id == lesson.id:
                continue
            if (
                (
                    lesson.parity == "all"
                    or other.parity == "all"
                    or other.parity == lesson.parity
                )
                and lesson.start_time < other.end_time
                and other.start_time < lesson.end_time
            ):
                raise ValueError(
                    tr(
                        "Время пересекается с парой «{subject}» ({start}–{end}).",
                        subject=other.subject,
                        start=f"{other.start_time:%H:%M}",
                        end=f"{other.end_time:%H:%M}",
                    )
                )


async def add_lesson(
    user_id,
    subject,
    day_of_week,
    start_time,
    end_time,
    lesson_type=None,
    location=None,
    teacher=None,
    parity="all",
):
    await get_user(user_id)
    async with async_session() as session:
        lesson = Schedule(
            user_id=user_id,
            subject=subject,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            lesson_type=lesson_type,
            location=location,
            teacher=teacher,
            parity=parity,
        )
        await _validate_lesson(session, lesson)
        session.add(lesson)
        await session.commit()
        return lesson


async def get_schedule_by_day(user_id, day_of_week, parity=None):
    async with async_session() as session:
        query = select(Schedule).where(
            Schedule.user_id == user_id, Schedule.day_of_week == day_of_week
        )
        if parity is not None:
            query = query.where(Schedule.parity.in_(("all", parity)))
        return list(
            await session.scalars(query.order_by(Schedule.start_time, Schedule.id))
        )


async def get_week_schedule(user_id):
    async with async_session() as session:
        return list(
            await session.scalars(
                select(Schedule)
                .where(Schedule.user_id == user_id)
                .order_by(Schedule.day_of_week, Schedule.start_time, Schedule.id)
            )
        )


async def _get(model, user_id, item_id):
    async with async_session() as session:
        return await session.scalar(
            select(model).where(model.user_id == user_id, model.id == item_id)
        )


async def get_lesson(user_id, lesson_id):
    return await _get(Schedule, user_id, lesson_id)


async def update_lesson(user_id, lesson_id, **fields):
    allowed = {
        "subject",
        "day_of_week",
        "start_time",
        "end_time",
        "lesson_type",
        "location",
        "teacher",
        "parity",
    }
    if not fields.keys() <= allowed:
        raise ValueError("Неизвестное поле пары.")
    async with async_session() as session:
        lesson = await session.scalar(
            select(Schedule).where(
                Schedule.user_id == user_id, Schedule.id == lesson_id
            )
        )
        if lesson is None:
            return False
        for key, value in fields.items():
            setattr(lesson, key, value)
        await _validate_lesson(session, lesson)
        await session.commit()
        return True


async def _delete(model, user_id, item_id):
    async with async_session() as session:
        item = await session.scalar(
            select(model).where(model.user_id == user_id, model.id == item_id)
        )
        if item is None:
            return False
        await session.delete(item)
        await session.commit()
        return True


async def delete_lesson(user_id, lesson_id):
    return await _delete(Schedule, user_id, lesson_id)


async def get_tasks(user_id, completed=None):
    async with async_session() as session:
        query = select(Task).where(Task.user_id == user_id)
        if completed is not None:
            query = query.where(Task.is_completed == completed)
        return list(
            await session.scalars(
                query.order_by(Task.deadline.is_(None), Task.deadline, Task.id)
            )
        )


async def get_task(user_id, task_id):
    return await _get(Task, user_id, task_id)


def _validate_task(task):
    task.text = _string(task.text, 255, True)
    task.subject_name = _string(task.subject_name, 100)
    if task.priority not in ("normal", "high"):
        raise ValueError("Неизвестный приоритет.")
    if task.deadline is not None and (
        not isinstance(task.deadline, datetime) or task.deadline.tzinfo is not None
    ):
        raise ValueError("Дедлайн должен быть локальной датой без часового пояса.")
    if not isinstance(task.is_completed, bool):
        raise ValueError("Некорректный статус задачи.")


async def add_task(user_id, text, subject_name=None, deadline=None, priority="normal"):
    await get_user(user_id)
    async with async_session() as session:
        task = Task(
            user_id=user_id,
            text=text,
            subject_name=subject_name,
            deadline=deadline,
            priority=priority,
            is_completed=False,
        )
        _validate_task(task)
        session.add(task)
        await session.commit()
        return task


async def update_task(user_id, task_id, **fields):
    if not fields.keys() <= {
        "text",
        "subject_name",
        "deadline",
        "priority",
        "is_completed",
    }:
        raise ValueError("Неизвестное поле задачи.")
    async with async_session() as session:
        task = await session.scalar(
            select(Task).where(Task.user_id == user_id, Task.id == task_id)
        )
        if task is None:
            return False
        for key, value in fields.items():
            setattr(task, key, value)
        _validate_task(task)
        await session.commit()
        return True


async def delete_task(user_id, task_id):
    return await _delete(Task, user_id, task_id)


async def get_notification_data():
    async with async_session() as session:
        result = await session.execute(
            select(User, Schedule)
            .join(Schedule, Schedule.user_id == User.user_id)
            .where(User.notifications_enabled.is_(True), User.user_id > 0)
        )
        return result.all()
