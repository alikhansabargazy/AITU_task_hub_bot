"""Localized settings screens using the user-settings database API."""

import asyncio
import secrets
from html import escape
from weakref import WeakValueDictionary
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import BaseMiddleware, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from services.i18n import main_keyboard, register, set_language, tr
from services.settings_translations import CATALOG

from database import db_requests as db
from services.calendar import local_now, week_parity

register(CATALOG)

router = Router()
LANGUAGES = {"ru": "Русский", "en": "Английский", "kk": "Казахский"}
PRESETS = {"almaty": "Asia/Almaty", "utc": "UTC", "moscow": "Europe/Moscow"}
CHOICES = {
    "reminder_minutes": (0, 5, 10, 15, 30, 60),
    "week_parity_offset": (0, 1),
    "dashboard_days": (1, 3, 7, 14),
}
MENU_TEXTS = {
    "🏠 Дашборд",
    "⚙️ Настройки",
    "📅 Расписание",
    "➕ Добавить",
    "📝 Дедлайны",
}


class SettingsState(StatesGroup):
    timezone = State()


class SessionLock(BaseMiddleware):
    """Keep token checks and updates atomic within this router."""

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


def html(value):
    text = str(value)
    return escape(text[:100] + ("…" if len(text) > 100 else ""))


async def screen(message, state, user_id, text, rows, *, edit=False, manual=False):
    token = secrets.token_hex(6)
    # Every screen replaces both the previous buttons and any pending input.
    await state.clear()
    await state.set_data({"settings_token": token, "settings_owner": user_id})
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"settings:{token}:{action}"
                )
                for label, action in row
            ]
            for row in rows
        ]
    )
    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=markup)
            sent = message
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                sent = message
            elif (
                "message can't be edited" in str(exc).lower()
                or "message to edit not found" in str(exc).lower()
            ):
                sent = await message.answer(
                    text, parse_mode="HTML", reply_markup=markup
                )
            else:
                raise
    else:
        sent = await message.answer(text, parse_mode="HTML", reply_markup=markup)
    await state.update_data(
        settings_message=sent.message_id, settings_chat=sent.chat.id
    )
    if manual:
        await state.set_state(SettingsState.timezone)


async def overview(message, state, user_id, *, user=None, edit=False, notice=""):
    if user is None:
        user = await db.get_user(user_id)
    today = local_now(user).date()
    parity = week_parity(today, offset=user.week_parity_offset)
    parity_key = {"numerator": "числитель", "denominator": "знаменатель"}.get(parity)
    parity_label = tr(parity_key) if parity_key else str(parity)
    reminder = (
        tr("в момент начала пары")
        if user.reminder_minutes == 0
        else tr("за {minutes} мин.", minutes=user.reminder_minutes)
    )
    text = tr(
        "⚙️ <b>Настройки</b>\n\n{notice}"
        "🗣 Язык: {language}\n"
        "🌐 Часовой пояс: <code>{timezone}</code>\n"
        "🔔 Уведомления: {notifications}\n"
        "⏰ Напоминание: {reminder}\n"
        "🔁 Смещение чётности: {offset}\n"
        "Сегодня: ISO-неделя {week}, {parity}\n"
        "🏠 Горизонт дедлайнов: {days} дн.\n\n"
        "Недели считаются по ISO: с понедельника, неделя №1 содержит 4 января. "
        "При смещении 0 нечётная неделя — числитель, чётная — знаменатель; "
        "смещение 1 меняет их местами.\n\n"
        "Горизонт дашборда включает сегодня. Просроченные задачи показываются независимо от горизонта.",
        notice=notice,
        language=html(tr(LANGUAGES[user.language])),
        timezone=html(user.timezone),
        notifications=tr("включены" if user.notifications_enabled else "выключены"),
        reminder=html(reminder),
        offset=user.week_parity_offset,
        week=today.isocalendar().week,
        parity=html(parity_label),
        days=user.dashboard_days,
    )
    await screen(
        message,
        state,
        user_id,
        text,
        [
            [(tr("🗣 Язык"), "language")],
            [(tr("🌐 Часовой пояс"), "timezone")],
            [
                (
                    tr(
                        "🔕 Выключить уведомления"
                        if user.notifications_enabled
                        else "🔔 Включить уведомления"
                    ),
                    "toggle",
                )
            ],
            [(tr("⏰ Напоминание"), "choose:reminder_minutes")],
            [(tr("🔁 Чётность недели"), "choose:week_parity_offset")],
            [(tr("🏠 Горизонт дашборда"), "choose:dashboard_days")],
            [(tr("🔄 Обновить"), "home")],
        ],
        edit=edit,
    )


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, state: FSMContext):
    await state.clear()
    await overview(message, state, message.from_user.id)


@router.callback_query(F.data.startswith("settings:"))
async def settings_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    data = await state.get_data()
    message = callback.message
    if (
        len(parts) != 3
        or not isinstance(message, Message)
        or data.get("settings_token") != parts[1]
        or data.get("settings_owner") != callback.from_user.id
        or data.get("settings_message") != message.message_id
        or data.get("settings_chat") != message.chat.id
    ):
        await callback.answer(
            tr("Этот экран устарел. Откройте /settings заново."), show_alert=True
        )
        return
    action = parts[2]
    user_id = callback.from_user.id
    valid = {"home", "timezone", "manual", "toggle", "language"}
    valid.update(f"language:{code}" for code in LANGUAGES)
    valid.update(f"tz:{key}" for key in PRESETS)
    valid.update(f"choose:{field}" for field in CHOICES)
    valid.update(
        f"set:{field}:{value}" for field, values in CHOICES.items() for value in values
    )
    if action not in valid:
        await callback.answer(tr("Неизвестная настройка."), show_alert=True)
        return
    await callback.answer()
    # Navigation or a setting selection cancels a previous manual timezone draft.
    await state.clear()
    if action == "language":
        user = await db.get_user(user_id)
        rows = [
            [
                (
                    tr("✓ {label}", label=tr(label))
                    if code == user.language
                    else tr(label),
                    f"language:{code}",
                )
            ]
            for code, label in LANGUAGES.items()
        ]
        await screen(
            message,
            state,
            user_id,
            tr("🗣 <b>Язык интерфейса</b>\nВыберите язык:"),
            rows + [[(tr("← Назад"), "home")]],
            edit=True,
        )
    elif action.startswith("language:"):
        code = action.split(":")[1]
        user = await db.update_user(user_id, language=code)
        # Middleware will restore the request context; all following UI uses the new language.
        set_language(code)
        await message.answer(
            tr("✅ Язык изменён. Главное меню обновлено."), reply_markup=main_keyboard()
        )
        await overview(message, state, user_id, user=user, edit=True)
    elif action == "timezone":
        await screen(
            message,
            state,
            user_id,
            tr(
                "🌐 <b>Часовой пояс</b>\n\nВыберите IANA-зону или введите её вручную.\n"
                "Алматы и Астана используют <code>Asia/Almaty</code>.\n"
                "Время пар и naive-дедлайнов хранится как местное время: смена зоны не пересчитывает их часы."
            ),
            [
                [(tr("Алматы / Астана"), "tz:almaty")],
                [(tr("UTC"), "tz:utc"), (tr("Москва"), "tz:moscow")],
                [(tr("✍️ Ввести IANA-зону"), "manual")],
                [(tr("← Назад"), "home")],
            ],
            edit=True,
        )
    elif action == "manual":
        # Send a NEW prompt so queued messages predating it cannot change the zone.
        await screen(
            message,
            state,
            user_id,
            tr(
                "✍️ Отправьте текстом IANA-зону, например <code>Asia/Almaty</code>, "
                "<code>Europe/Moscow</code> или <code>Europe/Berlin</code>.\n"
                "Регистр важен. Смещения вида UTC+5 не подходят.\n"
                "Можно ответить на это сообщение. Для отмены нажмите кнопку ниже или /settings."
            ),
            [[(tr("Отмена"), "home")]],
            manual=True,
        )
    elif action.startswith("choose:"):
        field = action.split(":")[1]
        titles = {
            "reminder_minutes": "⏰ За сколько минут до пары напоминать?\n0 — в момент начала, не отключение уведомлений.",
            "week_parity_offset": "🔁 Смещение ISO-чётности\n0: нечётная ISO-неделя — числитель, чётная — знаменатель.\n1: наоборот. ISO-неделя начинается в понедельник; неделя №1 содержит 4 января.",
            "dashboard_days": "🏠 На сколько календарных дней показывать дедлайны, включая сегодня?",
        }
        user = await db.get_user(user_id)
        rows = []
        for value in CHOICES[field]:
            label = str(value)
            if field == "reminder_minutes":
                label = (
                    tr("В момент начала (0)")
                    if value == 0
                    else tr("За {minutes} мин.", minutes=value)
                )
            elif field == "dashboard_days":
                label = tr("{days} дн.", days=value)
            if value == getattr(user, field):
                label = tr("✓ {label}", label=label)
            rows.append([(label, f"set:{field}:{value}")])
        await screen(
            message,
            state,
            user_id,
            tr(titles[field]),
            rows + [[(tr("← Назад"), "home")]],
            edit=True,
        )
    else:
        notice = tr("✅ Настройка сохранена.\n\n")
        if action == "toggle":
            user = await db.get_user(user_id)
            user = await db.update_user(
                user_id, notifications_enabled=not user.notifications_enabled
            )
        elif action.startswith("tz:"):
            zone = PRESETS[action.split(":")[1]]
            try:
                ZoneInfo(zone)
            except ZoneInfoNotFoundError:
                await overview(
                    message,
                    state,
                    user_id,
                    edit=True,
                    notice=tr("⚠️ База часовых поясов недоступна на сервере.\n\n"),
                )
                return
            user = await db.update_user(user_id, timezone=zone)
        elif action.startswith("set:"):
            _, field, value = action.split(":")
            user = await db.update_user(user_id, **{field: int(value)})
        else:
            user = await db.get_user(user_id)
            notice = ""
        await overview(message, state, user_id, user=user, edit=True, notice=notice)


@router.message(
    SettingsState.timezone, ~F.text.startswith("/"), ~F.text.in_(MENU_TEXTS)
)
async def timezone_input(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_id = data.get("settings_message")
    if (
        not prompt_id
        or data.get("settings_owner") != message.from_user.id
        or data.get("settings_chat") != message.chat.id
        or message.message_id <= prompt_id
        or (
            message.reply_to_message
            and message.reply_to_message.message_id != prompt_id
        )
    ):
        await message.answer(
            tr(
                "Это ответ на старый экран. Ответьте на последний запрос часового пояса или откройте /settings."
            )
        )
        return
    if not message.text:
        await message.answer(
            tr(
                "Нужен текст с IANA-зоной, например Asia/Almaty, а не фото, файл или стикер."
            )
        )
        return
    zone = message.text.strip()
    if not zone or len(zone) > 50:
        await message.answer(
            tr("Введите IANA-зону длиной от 1 до 50 символов, например Asia/Almaty.")
        )
        return
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        await message.answer(
            tr(
                "Неизвестная IANA-зона. Проверьте регистр и название, например Europe/Moscow. Если верное имя не принимается, проверьте базу часовых поясов сервера."
            )
        )
        return
    user = await db.update_user(message.from_user.id, timezone=zone)
    await overview(
        message,
        state,
        message.from_user.id,
        user=user,
        notice=tr("✅ Часовой пояс сохранён.\n\n"),
    )
