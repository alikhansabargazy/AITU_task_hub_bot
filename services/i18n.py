"""Explicit template translations; never translate user-provided content."""

from contextvars import ContextVar

from aiogram import BaseMiddleware
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

_language = ContextVar("language", default="en")
_catalog = {}


def register(catalog):
    _catalog.update(catalog)


def set_language(code):
    return _language.set(code if code in ("ru", "en", "kk") else "en")


def reset_language(token):
    _language.reset(token)


def tr(text, **kwargs):
    template = _catalog.get(text, {}).get(_language.get(), text)
    return template.format(**kwargs) if kwargs else template


register(
    {
        "🏠 Дашборд": {"en": "🏠 Dashboard", "kk": "🏠 Шолу"},
        "📅 Расписание": {"en": "📅 Schedule", "kk": "📅 Сабақ кестесі"},
        "📝 Дедлайны": {"en": "📝 Deadlines", "kk": "📝 Тапсырмалар"},
        "➕ Добавить": {"en": "➕ Add", "kk": "➕ Қосу"},
        "⚙️ Настройки": {"en": "⚙️ Settings", "kk": "⚙️ Баптаулар"},
        "Выберите действие": {"en": "Choose an action", "kk": "Әрекетті таңдаңыз"},
        "Привет, {name}! 👋\nЯ помогу управлять расписанием и дедлайнами. Язык можно изменить в настройках.": {
            "en": "Hi, {name}! 👋\nI can help manage your schedule and deadlines. Change your language in Settings.",
            "kk": "Сәлем, {name}! 👋\nСабақ кестесі мен тапсырмаларды басқаруға көмектесемін. Тілді баптаулардан өзгертуге болады.",
        },
        "Действие отменено.": {"en": "Action cancelled.", "kk": "Әрекет тоқтатылды."},
        "Выберите раздел в меню. /cancel — отменить ввод.": {
            "en": "Choose a section from the menu. /cancel cancels input.",
            "kk": "Мәзірден бөлімді таңдаңыз. /cancel — енгізуді тоқтату.",
        },
        "Используйте бота в личном чате.": {
            "en": "Please use the bot in a private chat.",
            "kk": "Ботты жеке чатта пайдаланыңыз.",
        },
        "Эта кнопка устарела. Откройте раздел заново.": {
            "en": "This button has expired. Open the section again.",
            "kk": "Бұл батырма ескірген. Бөлімді қайта ашыңыз.",
        },
        "Не указано": {"en": "Not specified", "kk": "Көрсетілмеген"},
        "Не указан": {"en": "Not specified", "kk": "Көрсетілмеген"},
        "через {minutes} мин.": {
            "en": "in {minutes} min.",
            "kk": "{minutes} минуттан кейін",
        },
        "начинается сейчас": {"en": "starts now", "kk": "қазір басталады"},
        "🔔 <b>Пара {label}</b>\n\n📚 {subject}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}": {
            "en": "🔔 <b>Class {label}</b>\n\n📚 {subject}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}",
            "kk": "🔔 <b>Сабақ {label}</b>\n\n📚 {subject}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}",
        },
        "Введите текст от 1 до {limit} символов.": {
            "en": "Enter text between 1 and {limit} characters.",
            "kk": "1–{limit} таңбадан тұратын мәтін енгізіңіз.",
        },
        "Время пересекается с парой «{subject}» ({start}–{end}).": {
            "en": "Time overlaps with “{subject}” ({start}–{end}).",
            "kk": "Уақыт «{subject}» сабағымен қабаттасады ({start}–{end}).",
        },
        "Конец пары должен быть позже начала в тот же день.": {
            "en": "The class must end after it starts on the same day.",
            "kk": "Сабақ сол күні басталу уақытынан кейін аяқталуы тиіс.",
        },
        "Проверьте день недели и чётность.": {
            "en": "Check the weekday and week parity.",
            "kk": "Апта күні мен апта кезектесуін тексеріңіз.",
        },
    }
)

MENU = ("🏠 Дашборд", "📅 Расписание", "📝 Дедлайны", "➕ Добавить", "⚙️ Настройки")


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(MENU[0]))],
            [KeyboardButton(text=tr(item)) for item in MENU[1:3]],
            [KeyboardButton(text=tr(item)) for item in MENU[3:]],
        ],
        resize_keyboard=True,
        input_field_placeholder=tr("Выберите действие"),
    )


class LocaleMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        from database.db_requests import get_user

        user = data.get("event_from_user") or getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)
        profile = await get_user(user.id)
        token = set_language(profile.language)
        try:
            # Normalize only exact menu labels, before aiogram evaluates filters.
            if isinstance(event, Message) and event.text:
                aliases = {
                    label: source
                    for source in MENU
                    for label in (source, *_catalog.get(source, {}).values())
                }
                if event.text in aliases:
                    event = event.model_copy(update={"text": aliases[event.text]})
            chat = (
                event.chat
                if isinstance(event, Message)
                else getattr(getattr(event, "message", None), "chat", None)
            )
            if chat and chat.type != "private":
                if isinstance(event, Message):
                    await event.answer(tr("Используйте бота в личном чате."))
                else:
                    await event.answer(
                        tr("Используйте бота в личном чате."), show_alert=True
                    )
                return
            return await handler(event, data)
        finally:
            reset_language(token)
