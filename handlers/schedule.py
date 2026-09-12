"""Schedule screens and lesson drafts; database writes require confirmation."""

import asyncio
import re
import secrets
import unicodedata
from datetime import time, timedelta
from html import escape
from weakref import WeakValueDictionary

from aiogram import BaseMiddleware, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import db_requests as db
from services.calendar import local_now, week_parity
from services.i18n import register, tr
from services.schedule_translations import CATALOG

register(CATALOG)

router = Router()
DAYS = {
    1: "Понедельник",
    2: "Вторник",
    3: "Среда",
    4: "Четверг",
    5: "Пятница",
    6: "Суббота",
    7: "Воскресенье",
}
PARITIES = {
    "all": "Каждую неделю",
    "numerator": "Числитель",
    "denominator": "Знаменатель",
}
FIELDS = {
    "subject": "Предмет",
    "day_of_week": "День недели",
    "parity": "Чётность",
    "time": "Начало и конец",
    "location": "Аудитория / место",
    "teacher": "Преподаватель",
    "lesson_type": "Тип занятия",
}
LIMITS = {"subject": 100, "location": 100, "teacher": 100, "lesson_type": 50}
# Incoming menu labels are normalized to Russian by the i18n middleware.
MENU_TEXTS = {
    "📅 Расписание",
    "➕ Добавить",
    "📝 Дедлайны",
    "⚙️ Настройки",
    "🏠 Дашборд",
}
INPUT = ~F.text.startswith("/") & ~F.text.in_(MENU_TEXTS)


class LessonState(StatesGroup):
    subject = State()
    day_of_week = State()
    parity = State()
    time = State()
    location = State()
    teacher = State()
    lesson_type = State()
    confirm = State()
    delete = State()
    edit = State()


class SessionLock(BaseMiddleware):
    """Serialize menu/input/confirmation even without Dispatcher event isolation."""

    def __init__(self):
        self.locks = WeakValueDictionary()

    async def __call__(self, handler, event, data):
        state = data.get("state")
        if state is None:
            return await handler(event, data)
        lock = self.locks.setdefault(state.key, asyncio.Lock())
        async with lock:
            return await handler(event, data)


session_lock = SessionLock()
router.message.middleware(session_lock)
router.callback_query.middleware(session_lock)


def html(value, limit=100):
    # Bound even legacy DB values; escape AFTER truncation to preserve entities.
    text = str(value)
    return escape(text[:limit] + ("…" if len(text) > limit else ""))


def snapshot(lesson):
    fields = [key for key in FIELDS if key != "time"] + ["start_time", "end_time"]
    result = {key: getattr(lesson, key) for key in fields}
    for key in ("start_time", "end_time"):
        if isinstance(result[key], time):
            result[key] = result[key].strftime("%H:%M")
    return result


def lesson_text(draft):
    return tr(
        "<b>{subject}</b>\n{day} · {parity}\n⏰ {start}–{end}\n"
        "📍 {location}\n👤 {teacher}\nТип: {lesson_type}",
        subject=html(draft["subject"]),
        day=tr(DAYS[draft["day_of_week"]]),
        parity=tr(PARITIES[draft["parity"]]),
        start=html(draft["start_time"], 5),
        end=html(draft["end_time"], 5),
        location=html(draft.get("location") or tr("Не указано")),
        teacher=html(draft.get("teacher") or tr("Не указан")),
        lesson_type=html(draft.get("lesson_type") or tr("Не указан"), 50),
    )


def navigation():
    return [
        [(tr("Сегодня"), "view:today:0"), (tr("Завтра"), "view:tomorrow:0")],
        [(tr("Дни недели"), "days"), (tr("Вся неделя"), "view:week:0")],
        [(tr("➕ Добавить пару"), "new")],
    ]


async def screen(message, state, text, rows, *, edit=False):
    token = secrets.token_hex(6)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=(
                        action if action == "task:add" else f"schedule:{token}:{action}"
                    ),
                )
                for label, action in row
            ]
            for row in rows
        ]
    )
    # Invalidate the previous screen before any network await.
    await state.update_data(ui_token=token, ui_message=None)
    if edit:
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                raise
        sent = message
    else:
        sent = await message.answer(text, reply_markup=markup, parse_mode="HTML")
    await state.update_data(ui_message=sent.message_id, ui_chat=sent.chat.id)


@router.message(Command("schedule"))
@router.message(F.text == "📅 Расписание")
async def schedule_menu(message: Message, state: FSMContext):
    await state.clear()
    await screen(message, state, tr("📅 <b>Расписание</b>"), navigation())


async def browse(message, state, user_id, mode, page):
    if mode in ("today", "tomorrow"):
        user = await db.get_user(user_id)
        if user is None:
            await screen(
                message,
                state,
                tr("Сначала зарегистрируйтесь: /start"),
                navigation(),
                edit=True,
            )
            return
        date = local_now(user).date() + timedelta(days=mode == "tomorrow")
        parity = week_parity(date, offset=user.week_parity_offset)
        lessons = await db.get_schedule_by_day(
            user_id, date.isoweekday(), parity=parity
        )
        title = tr(
            "{day} {date} · {parity}",
            day=tr(DAYS[date.isoweekday()]),
            date=date.strftime("%d.%m.%Y"),
            parity=tr(PARITIES[parity]),
        )
    elif mode == "week":
        lessons = await db.get_week_schedule(user_id)
        title = tr("Вся неделя · обе чётности")
    else:
        day = int(mode)
        lessons = await db.get_schedule_by_day(user_id, day, parity=None)
        title = tr("{day} · обе чётности", day=tr(DAYS[day]))
    lessons = sorted(
        lessons, key=lambda item: (item.day_of_week, str(item.start_time), item.id)
    )
    page = min(max(page, 0), max(len(lessons) - 1, 0))
    rows = []
    text = tr("<b>{title}</b>\n\n", title=title)
    if lessons:
        lesson = lessons[page]
        text += tr(
            "{lesson}\n\nПара {page} из {total}",
            lesson=lesson_text(snapshot(lesson)),
            page=page + 1,
            total=len(lessons),
        )
        rows.append(
            [
                (tr("✏️ Редактировать"), f"edit:{lesson.id}"),
                (tr("🗑 Удалить"), f"delete:{lesson.id}"),
            ]
        )
        arrows = []
        if page:
            arrows.append((tr("←"), f"view:{mode}:{page - 1}"))
        if page + 1 < len(lessons):
            arrows.append((tr("→"), f"view:{mode}:{page + 1}"))
        if arrows:
            rows.append(arrows)
    else:
        text += tr("Пар нет.")
    # One bounded card per page stays comfortably below Telegram's text/button limits.
    await screen(message, state, text, rows + navigation(), edit=True)


async def prompt(message, state, field, *, edit=False):
    await state.set_state(getattr(LessonState, field))
    rows = []
    if field == "day_of_week":
        text = tr("Выберите день недели:")
        rows = [[(tr(name), f"pick:day_of_week:{day}")] for day, name in DAYS.items()]
    elif field == "parity":
        text = tr("Выберите чётность недели:")
        rows = [
            [(tr(name), f"pick:parity:{value}")] for value, name in PARITIES.items()
        ]
    elif field == "time":
        text = tr(
            "Введите начало и конец: <b>08:30-10:05</b>. Конец должен быть позже начала."
        )
    else:
        text = tr(
            "{field}: введите текст (до {limit} символов).",
            field=tr(FIELDS[field]),
            limit=LIMITS[field],
        )
        if field != "subject":
            text += tr(" Для пустого значения отправьте <b>-</b>.")
            rows = [[(tr("Не указывать"), f"pick:{field}:none")]]
    await screen(message, state, text, rows + [[(tr("Отменить"), "cancel")]], edit=edit)


async def review(message, state, *, edit=False, error=None):
    data = await state.get_data()
    await state.set_state(LessonState.confirm)
    text = tr(
        "<b>Проверьте перед сохранением</b>\n\n{lesson}",
        lesson=lesson_text(data["draft"]),
    )
    if error:
        text = tr("❌ {error}\n\n{review}", error=html(error, 200), review=text)
    await screen(
        message,
        state,
        text,
        [
            [(tr("✅ Сохранить"), "save")],
            [(tr("✏️ Изменить поля"), "fields")],
            [(tr("Отменить"), "cancel")],
        ],
        edit=edit,
    )


async def fields_menu(message, state):
    await state.set_state(LessonState.edit)
    await screen(
        message,
        state,
        tr("Выберите поле:"),
        [[(tr(label), f"field:{field}")] for field, label in FIELDS.items()]
        + [[(tr("К подтверждению"), "review")], [(tr("Отменить"), "cancel")]],
        edit=True,
    )


def validate(field, text):
    if text is None:
        raise ValueError(tr("Отправьте текст, а не файл или стикер."))
    text = text.strip()
    if field == "day_of_week":
        if text not in {str(day) for day in DAYS}:
            raise ValueError(tr("Выберите день кнопкой или введите число от 1 до 7."))
        return {field: int(text)}
    if field == "parity":
        if text not in PARITIES:
            raise ValueError(tr("Выберите чётность кнопкой."))
        return {field: text}
    if field == "time":
        match = re.fullmatch(r"(\d{2}:\d{2})\s*[-–—]\s*(\d{2}:\d{2})", text)
        if not match:
            raise ValueError(tr("Формат времени: 08:30-10:05."))
        try:
            start, end = (time.fromisoformat(value) for value in match.groups())
        except ValueError:
            raise ValueError(tr("Часы: 00–23, минуты: 00–59.")) from None
        if start >= end:
            raise ValueError(
                tr("Конец должен быть позже начала в пределах одного дня.")
            )
        return {
            "start_time": start.strftime("%H:%M"),
            "end_time": end.strftime("%H:%M"),
        }
    if field != "subject" and text == "-":
        return {field: None}
    if not text or len(text) > LIMITS[field]:
        raise ValueError(tr("Нужно от 1 до {limit} символов.", limit=LIMITS[field]))
    if any(unicodedata.category(char).startswith("C") for char in text):
        raise ValueError(tr("Уберите управляющие и невидимые символы."))
    return {field: text}


async def accept(message, state, field, values, *, edit=False):
    data = await state.get_data()
    draft = {**data["draft"], **values}
    changes = {**data.get("changes", {}), **values}
    await state.update_data(draft=draft, changes=changes)
    if data["wizard"] and field != "lesson_type":
        next_field = list(FIELDS)[list(FIELDS).index(field) + 1]
        await prompt(message, state, next_field, edit=edit)
    else:
        await state.update_data(wizard=False)
        await review(message, state, edit=edit)


@router.message(StateFilter(*(getattr(LessonState, field) for field in FIELDS)), INPUT)
async def lesson_input(message: Message, state: FSMContext):
    field = (await state.get_state()).rsplit(":", 1)[-1]
    try:
        values = validate(field, message.text)
    except ValueError as exc:
        await message.answer(str(exc), parse_mode=None)
        return
    await accept(message, state, field, values)


@router.callback_query(F.data.startswith("schedule:"))
async def schedule_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    parts = callback.data.split(":")
    if (
        len(parts) < 3
        or parts[1] != data.get("ui_token")
        or not isinstance(callback.message, Message)
        or callback.message.message_id != data.get("ui_message")
        or callback.message.chat.id != data.get("ui_chat")
    ):
        await callback.answer(
            tr("Эта кнопка устарела. Откройте меню заново."), show_alert=True
        )
        return
    action, args = parts[2], parts[3:]
    current = await state.get_state()
    # Validate both payload and state before acknowledging or changing the session.
    valid = (
        (action in {"new", "cancel", "days"} and not args)
        or (
            action == "view"
            and len(args) == 2
            and args[0] in {"today", "tomorrow", "week", *map(str, DAYS)}
            and args[1].isascii()
            and args[1].isdigit()
            and len(args[1]) <= 9
        )
        or (
            action in {"edit", "delete"}
            and current is None
            and len(args) == 1
            and args[0].isascii()
            and args[0].isdigit()
            and len(args[0]) <= 19
        )
        or (
            action in {"save", "fields"}
            and not args
            and current == LessonState.confirm.state
        )
        or (action == "review" and not args and current == LessonState.edit.state)
        or (
            action == "field"
            and len(args) == 1
            and args[0] in FIELDS
            and current == LessonState.edit.state
        )
        or (action == "yes" and not args and current == LessonState.delete.state)
        or (
            action == "pick"
            and len(args) == 2
            and args[0] in FIELDS
            and current == getattr(LessonState, args[0]).state
            and (
                (args[0] == "day_of_week" and args[1] in set(map(str, DAYS)))
                or (args[0] == "parity" and args[1] in PARITIES)
                or (
                    args[0] in {"location", "teacher", "lesson_type"}
                    and args[1] == "none"
                )
            )
        )
    )
    if not valid:
        await callback.answer(tr("Действие недоступно."), show_alert=True)
        return
    await callback.answer()
    message, user_id = callback.message, callback.from_user.id
    if action in {"cancel", "days", "view", "new"}:
        await state.clear()
        if action == "cancel":
            await screen(
                message,
                state,
                tr("Действие отменено. Расписание:"),
                navigation(),
                edit=True,
            )
        elif action == "days":
            await screen(
                message,
                state,
                tr("Выберите день (обе чётности):"),
                [[(tr(name), f"view:{day}:0")] for day, name in DAYS.items()]
                + navigation(),
                edit=True,
            )
        elif action == "view":
            await browse(message, state, user_id, args[0], int(args[1]))
        else:
            await state.update_data(draft={}, changes={}, wizard=True, lesson_id=None)
            await prompt(message, state, "subject", edit=True)
    elif action in {"edit", "delete"}:
        lesson = await db.get_lesson(user_id, int(args[0]))
        if lesson is None:
            await screen(
                message,
                state,
                tr("Пара больше не существует."),
                navigation(),
                edit=True,
            )
            return
        await state.update_data(
            lesson_id=lesson.id, draft=snapshot(lesson), changes={}, wizard=False
        )
        if action == "edit":
            await fields_menu(message, state)
        else:
            await state.set_state(LessonState.delete)
            await screen(
                message,
                state,
                tr(
                    "<b>Удалить пару?</b>\n\n{lesson}",
                    lesson=lesson_text(snapshot(lesson)),
                ),
                [
                    [(tr("🗑 Да, удалить"), "yes"), (tr("Отменить"), "cancel")],
                ],
                edit=True,
            )
    elif action == "fields":
        await fields_menu(message, state)
    elif action == "field":
        await prompt(message, state, args[0], edit=True)
    elif action == "review":
        await review(message, state, edit=True)
    elif action == "pick":
        values = validate(args[0], "-" if args[1] == "none" else args[1])
        await accept(message, state, args[0], values, edit=True)
    elif action in {"save", "yes"}:
        # Consume confirmation before awaiting the DB: duplicate clicks cannot write twice.
        await state.update_data(ui_token=None)
        if action == "yes":
            ok = await db.delete_lesson(user_id, data["lesson_id"])
            text = (
                tr("✅ Пара удалена.") if ok else tr("Пара уже удалена или недоступна.")
            )
        else:
            values = dict(
                data["draft"] if data["lesson_id"] is None else data["changes"]
            )
            for key in ("start_time", "end_time"):
                if key in values:
                    values[key] = time.fromisoformat(values[key])
            try:
                if data["lesson_id"] is None:
                    await db.add_lesson(user_id=user_id, **values)
                    ok = True
                else:
                    ok = await db.update_lesson(user_id, data["lesson_id"], **values)
            except ValueError as exc:
                await review(
                    message,
                    state,
                    edit=True,
                    error=str(exc) or tr("Конфликт расписания."),
                )
                return
            text = (
                tr("✅ Пара сохранена.")
                if ok
                else tr("Пара уже удалена или недоступна.")
            )
        await state.clear()
        await screen(message, state, text, navigation(), edit=True)
