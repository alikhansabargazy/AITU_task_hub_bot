"""Local-time dashboard; naive task deadlines are user-local wall times."""

from datetime import datetime, time, timedelta
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from services.i18n import register, tr

from database import db_requests as db
from services.calendar import lesson_occurs, local_now, week_parity
from services.settings_translations import CATALOG

register(CATALOG)

router = Router()
PARITIES = {"numerator": "числитель", "denominator": "знаменатель"}
WEEKDAYS = (
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
)
MAX_MESSAGE_UNITS = 3800


def html(value, limit=60):
    text = str(value)
    return escape(text[:limit] + ("…" if len(text) > limit else ""))


def units(text):
    # Count even markup/entities, conservatively, and account for astral emoji.
    return len(text.encode("utf-16-le")) // 2


def local_deadline(task, now):
    deadline = task.deadline
    if deadline is None:
        return None
    if deadline.tzinfo is not None:
        return deadline.astimezone(now.tzinfo).replace(tzinfo=None)
    # Do NOT interpret the existing naive database representation as UTC.
    return deadline


def lesson_line(occurrence):
    start, end, lesson = occurrence
    location = (
        tr(" · {location}", location=html(lesson.location, 35))
        if lesson.location
        else ""
    )
    end_label = (
        end.strftime("%H:%M")
        if start.date() == end.date()
        else end.strftime("%d.%m %H:%M")
    )
    return tr(
        "{start:%d.%m %H:%M}–{end} · <b>{subject}</b>{location}",
        start=start,
        end=end_label,
        subject=html(lesson.subject),
        location=location,
    )


def render_dashboard(user, lessons, tasks, *, now=None):
    now = local_now(user, now=now)
    today = now.date()
    wall_now = now.replace(tzinfo=None)
    days = user.dashboard_days
    horizon = datetime.combine(today + timedelta(days=days), time.min)
    parity = week_parity(today, offset=user.week_parity_offset)

    occurrences = []
    today_count = 0
    # Include yesterday solely for a lesson that runs across midnight.
    # The forward search covers today and the next 13 local dates.
    for delta in range(-1, 14):
        date = today + timedelta(days=delta)
        for lesson in lessons:
            if not lesson_occurs(lesson, date, user):
                continue
            if delta == 0:
                today_count += 1
            start = datetime.combine(date, lesson.start_time, tzinfo=now.tzinfo)
            end = datetime.combine(date, lesson.end_time, tzinfo=now.tzinfo)
            if lesson.end_time < lesson.start_time:
                end += timedelta(days=1)
            occurrences.append((start, end, lesson))
    occurrences.sort(key=lambda item: (item[0], item[1], item[2].id))
    current = [item for item in occurrences if item[0] <= now < item[1]]
    upcoming_lesson = next((item for item in occurrences if item[0] > now), None)

    active = [task for task in tasks if not task.is_completed]
    overdue, upcoming, undated = [], [], []
    later_count = 0
    for task in active:
        deadline = local_deadline(task, now)
        if deadline is None:
            undated.append(task)
        elif deadline < wall_now:
            overdue.append((deadline, task))
        elif deadline < horizon:
            upcoming.append((deadline, task))
        else:
            later_count += 1
    overdue.sort(key=lambda item: (item[0], item[1].id))
    upcoming.sort(key=lambda item: (item[0], item[1].id))
    undated.sort(key=lambda task: task.id)

    parity_label = tr(PARITIES[parity]) if parity in PARITIES else str(parity)
    lines = [
        tr("🏠 <b>Дашборд</b>"),
        tr(
            "📅 {now:%d.%m.%Y %H:%M} · {weekday}",
            now=now,
            weekday=tr(WEEKDAYS[today.weekday()]),
        ),
        tr(
            "🌐 <code>{timezone}</code> · UTC{now:%z}",
            timezone=html(user.timezone, 100),
            now=now,
        ),
        tr(
            "ISO-неделя {week} · {parity}",
            week=today.isocalendar().week,
            parity=html(parity_label),
        ),
        "",
        tr("🎓 <b>Пар сегодня: {count}</b>", count=today_count),
        tr(
            "Сейчас: {lesson}",
            lesson=lesson_line(current[0]) if current else tr("пары нет."),
        ),
    ]
    if len(current) > 1:
        lines.append(tr("Ещё одновременно идут пары: {count}.", count=len(current) - 1))
    lines.append(
        tr(
            "Следующая: {lesson}",
            lesson=lesson_line(upcoming_lesson)
            if upcoming_lesson
            else tr("нет в ближайшие 14 дней (включая сегодня)."),
        )
    )
    lines.extend(
        [
            "",
            tr("📝 <b>Активных задач: {count}</b>", count=len(active)),
            tr(
                "Просрочено: {overdue} · В горизонте: {upcoming} · Без срока: {undated}",
                overdue=len(overdue),
                upcoming=len(upcoming),
                undated=len(undated),
            ),
            tr(
                "Горизонт: {start:%d.%m.%Y}–{end:%d.%m.%Y} ({days} дн., включая сегодня).",
                start=today,
                end=horizon.date() - timedelta(days=1),
                days=days,
            ),
            tr("За горизонтом: {count}. Все сроки — местное время.", count=later_count),
        ]
    )
    # Give each category its own budget, leaving room for all headings/counts.
    for title, items, has_deadline in (
        ("🔥 Просроченные", overdue, True),
        ("⏳ Ближайшие дедлайны", upcoming, True),
        ("📌 Без срока", undated, False),
    ):
        lines.extend(["", tr("<b>{title}</b>", title=tr(title))])
        if not items:
            lines.append(tr("Нет."))
            continue
        shown, used = 0, 0
        for item in items[:3]:
            if has_deadline:
                deadline, task = item
                line = tr(
                    "• {deadline:%d.%m.%Y %H:%M} — {task_text}",
                    deadline=deadline,
                    task_text=html(task.text, 70),
                )
            else:
                line = tr("• {task_text}", task_text=html(item.text, 70))
            cost = units(line) + 1
            if used + cost > 650:
                break
            lines.append(line)
            used += cost
            shown += 1
        if shown < len(items):
            lines.append(
                tr(
                    "Ещё: {count}. Полный список — в «📝 Дедлайны».",
                    count=len(items) - shown,
                )
            )
    text = "\n".join(lines)
    # Do not slice HTML: entities/tags must remain intact even with legacy data.
    if units(text) > MAX_MESSAGE_UNITS:
        return tr(
            "🏠 <b>Дашборд</b>\n📅 {now:%d.%m.%Y %H:%M}\n"
            "🌐 <code>{timezone}</code>\n"
            "Пар сегодня: {lessons}\nАктивных задач: {active}\n"
            "Просрочено: {overdue}\nВ ближайшие {days} дн.: {upcoming}\n"
            "Без срока: {undated}\nЗа горизонтом: {later}\n"
            "Подробности — в «📅 Расписание» и «📝 Дедлайны».",
            now=now,
            timezone=html(user.timezone, 50),
            lessons=today_count,
            active=len(active),
            overdue=len(overdue),
            days=days,
            upcoming=len(upcoming),
            undated=len(undated),
            later=later_count,
        )
    return text


async def show_dashboard(message, user_id, *, edit=False):
    user = await db.get_user(user_id)
    lessons = await db.get_week_schedule(user_id)
    tasks = await db.get_tasks(user_id, completed=None)
    text = render_dashboard(user, lessons, tasks)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr("🔄 Обновить"), callback_data=f"dashboard:refresh:{user_id}"
                )
            ]
        ]
    )
    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=markup)
            return
        except TelegramBadRequest as exc:
            error = str(exc).lower()
            if "message is not modified" in error:
                return
            if (
                "message can't be edited" not in error
                and "message to edit not found" not in error
            ):
                raise
    await message.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(Command("dashboard"))
@router.message(F.text == "🏠 Дашборд")
async def dashboard_menu(message: Message, state: FSMContext):
    await state.clear()
    await show_dashboard(message, message.from_user.id)


@router.callback_query(F.data.startswith("dashboard:"))
async def dashboard_refresh(callback: CallbackQuery, state: FSMContext):
    if callback.data != f"dashboard:refresh:{callback.from_user.id}":
        await callback.answer(
            tr("Откройте свой дашборд командой /dashboard."), show_alert=True
        )
        return
    if not isinstance(callback.message, Message):
        await callback.answer(
            tr("Сообщение недоступно. Откройте /dashboard."), show_alert=True
        )
        return
    # Refreshing an old dashboard must not discard a newer settings/lesson draft.
    await callback.answer()
    await show_dashboard(callback.message, callback.from_user.id, edit=True)
