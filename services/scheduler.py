import logging
from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db_requests import get_notification_data
from services.calendar import lesson_occurs, local_now
from services.i18n import reset_language, set_language, tr

logger = logging.getLogger(__name__)


async def check_upcoming_lessons(bot: Bot):
    now = datetime.now(timezone.utc)
    for user, lesson in await get_notification_data():
        target = local_now(user, now) + timedelta(minutes=user.reminder_minutes)
        if not lesson_occurs(lesson, target.date(), user):
            continue
        if (
            lesson.start_time
            != target.replace(second=0, microsecond=0, tzinfo=None).time()
        ):
            continue
        token = set_language(user.language)
        try:
            label = (
                tr("через {minutes} мин.", minutes=user.reminder_minutes)
                if user.reminder_minutes
                else tr("начинается сейчас")
            )
            text = tr(
                "🔔 <b>Пара {label}</b>\n\n📚 {subject}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}",
                label=label,
                subject=escape(lesson.subject),
                start=f"{lesson.start_time:%H:%M}",
                end=f"{lesson.end_time:%H:%M}",
                location=escape(lesson.location or tr("Не указано")),
                teacher=escape(lesson.teacher or tr("Не указан")),
            )
            await bot.send_message(user.user_id, text, parse_mode="HTML")
        except Exception:
            logger.exception(
                "Не удалось отправить напоминание пользователю %s", user.user_id
            )
        finally:
            reset_language(token)


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_upcoming_lessons,
        "cron",
        second=0,
        args=[bot],
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
    scheduler.start()
    return scheduler
