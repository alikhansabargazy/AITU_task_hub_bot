"""Deadline CRUD. Deadlines are naive datetimes in the user's local timezone."""

import secrets
from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from services.i18n import register, tr

from database import db_requests as db
from handlers.schedule import MENU_TEXTS, session_lock
from services.calendar import local_now
from services.task_translations import CATALOG

register(CATALOG)

router = Router()
router.message.middleware(session_lock)
router.callback_query.middleware(session_lock)

FIELDS = ("text", "deadline", "subject_name", "priority")
LABELS = {
    "text": "Текст",
    "deadline": "Дедлайн",
    "subject_name": "Предмет",
    "priority": "Приоритет",
}
MODES = {"active": False, "done": True, "all": None}
DATE_FORMAT = "%d.%m.%Y %H:%M"


class TaskState(StatesGroup):
    create = State()
    edit = State()
    confirm = State()
    delete = State()


def html(value, limit=255):
    return escape(str(value)[:limit])


def timezone_note(user):
    return tr(
        "Часовой пояс: <b>{timezone}</b>. Сейчас: {now}.\n"
        "Дедлайны вводятся и хранятся в вашем местном времени, без перевода в UTC.",
        timezone=html(user.timezone, 100),
        now=local_now(user).strftime(DATE_FORMAT),
    )


async def screen(message, state, text, rows):
    token = secrets.token_hex(6)
    actions = [action for row in rows for _, action in row]
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label, callback_data=f"task:{token}:{action}")
                for label, action in row
            ]
            for row in rows
        ]
    )
    # Rotate before sending; previous screens cannot mutate the current draft.
    await state.update_data(ui_token=token, ui_message=None, task_actions=actions)
    sent = await message.answer(text, parse_mode="HTML", reply_markup=markup)
    await state.update_data(ui_message=sent.message_id, ui_chat=sent.chat.id)


def navigation():
    return [
        [
            (tr("Активные"), "list:active:0"),
            (tr("Выполненные"), "list:done:0"),
            (tr("Все"), "list:all:0"),
        ],
        [(tr("➕ Добавить"), "new")],
    ]


async def browse(message, state, user_id, mode="active", page=0, notice=""):
    await state.set_state(None)
    tasks = await db.get_tasks(user_id, completed=MODES[mode])
    page = min(max(page, 0), max(len(tasks) - 1, 0))
    await state.update_data(task_mode=mode, task_page=page)
    user = await db.get_user(user_id)
    text = tr("📝 <b>Дедлайны</b>\n") + timezone_note(user) + "\n\n" + notice
    rows = []
    if tasks:
        task = tasks[page]
        text += card(task) + tr(
            "\n\nЗадача {number} из {total}", number=page + 1, total=len(tasks)
        )
        rows = [
            [
                (tr("✏️ {field}", field=tr(LABELS[field])), f"edit:{task.id}:{field}")
                for field in FIELDS[:2]
            ],
            [
                (tr("✏️ {field}", field=tr(LABELS[field])), f"edit:{task.id}:{field}")
                for field in FIELDS[2:]
            ],
            [
                (
                    tr("↩️ Возобновить" if task.is_completed else "✅ Выполнить"),
                    f"complete:{task.id}:{int(not task.is_completed)}",
                ),
                (tr("🗑 Удалить"), f"delete:{task.id}"),
            ],
        ]
        arrows = []
        if page:
            arrows.append((tr("←"), f"list:{mode}:{page - 1}"))
        if page + 1 < len(tasks):
            arrows.append((tr("→"), f"list:{mode}:{page + 1}"))
        if arrows:
            rows.append(arrows)
    else:
        text += tr("Задач нет.")
    await screen(message, state, text, rows + navigation())


def card(task):
    deadline = task.deadline.strftime(DATE_FORMAT) if task.deadline else tr("Не указан")
    return tr(
        "<b>{task_text}</b>\nПредмет: {subject}\nДедлайн: {deadline}\n"
        "Приоритет: {priority}\nСтатус: {status}",
        task_text=html(task.text),
        subject=html(task.subject_name or tr("Не указан"), 100),
        deadline=deadline,
        priority=tr("🔴 Высокий" if task.priority == "high" else "Обычный"),
        status=tr("✅ Выполнена" if task.is_completed else "В работе"),
    )


@router.message(Command("tasks"))
@router.message(F.text == "📝 Дедлайны")
async def tasks_menu(message: Message, state: FSMContext):
    await state.clear()
    if await db.get_user(message.from_user.id) is None:
        await message.answer(tr("Сначала зарегистрируйтесь: /start"))
        return
    await browse(message, state, message.from_user.id)


async def prompt(message, state):
    data = await state.get_data()
    field = data["task_field"]
    texts = {
        "text": "Введите текст задачи (1–255 символов).",
        "deadline": "Введите дедлайн: ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2026 18:00), либо «-» без срока.",
        "subject_name": "Введите предмет (1–100 символов), либо «-» без предмета.",
        "priority": "Выберите приоритет кнопкой ниже.",
    }
    rows = []
    if field == "priority":
        rows.append([(tr("Обычный"), "value:normal"), (tr("🔴 Высокий"), "value:high")])
    elif field in ("deadline", "subject_name"):
        rows.append(
            [(tr("Без срока" if field == "deadline" else "Без предмета"), "value:none")]
        )
    rows.append([(tr("Отмена"), "back")])
    await screen(message, state, tr(texts[field]) + tr("\n/cancel — отменить."), rows)


async def begin(message, state, user):
    await state.clear()
    await state.set_state(TaskState.create)
    await state.update_data(task_field="text", task_draft={})
    await message.answer(timezone_note(user), parse_mode="HTML")
    await prompt(message, state)


async def accept(message, state, user_id, value):
    data = await state.get_data()
    field = data["task_field"]
    if await state.get_state() == TaskState.edit.state:
        # Only this field is written: unrelated changes are not overwritten.
        ok = await db.update_task(user_id, data["task_id"], **{field: value})
        await browse(
            message,
            state,
            user_id,
            data.get("task_mode", "active"),
            data.get("task_page", 0),
            tr("Сохранено.\n\n" if ok else "Задача уже удалена.\n\n"),
        )
        return
    draft = data["task_draft"]
    # FSM data stays JSON-serializable with RedisStorage as well as MemoryStorage.
    draft[field] = value.isoformat() if isinstance(value, datetime) else value
    await state.update_data(task_draft=draft)
    index = FIELDS.index(field) + 1
    if index < len(FIELDS):
        await state.update_data(task_field=FIELDS[index])
        await prompt(message, state)
    else:
        await state.set_state(TaskState.confirm)
        deadline = (
            datetime.fromisoformat(draft["deadline"]).strftime(DATE_FORMAT)
            if draft["deadline"]
            else tr("Не указан")
        )
        await screen(
            message,
            state,
            tr(
                "<b>Создать задачу?</b>\n{task_text}\nПредмет: {subject}\n"
                "Дедлайн: {deadline}\nПриоритет: {priority}",
                task_text=html(draft["text"]),
                subject=html(draft["subject_name"] or tr("Не указан"), 100),
                deadline=deadline,
                priority=tr("Высокий" if draft["priority"] == "high" else "Обычный"),
            ),
            [[(tr("✅ Создать"), "save"), (tr("Отмена"), "back")]],
        )


@router.callback_query(F.data == "task:add")
async def add_task_entry(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message = callback.message
    # The add menu uses an unversioned button; bind it to its tracked message.
    if (
        not isinstance(message, Message)
        or data.get("ui_message") != message.message_id
        or data.get("ui_chat") != message.chat.id
        or await state.get_state() is not None
    ):
        await callback.answer(tr("Меню устарело. Откройте /tasks."))
        return
    user = await db.get_user(callback.from_user.id)
    await callback.answer()
    if user is None:
        await message.answer(tr("Сначала зарегистрируйтесь: /start"))
        return
    await begin(message, state, user)


@router.callback_query(F.data.startswith("task:"))
async def task_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    parts = callback.data.split(":", 2)
    message = callback.message
    if (
        len(parts) != 3
        or not isinstance(message, Message)
        or parts[1] != data.get("ui_token")
        or message.message_id != data.get("ui_message")
        or message.chat.id != data.get("ui_chat")
        or parts[2] not in data.get("task_actions", [])
    ):
        await callback.answer(tr("Эта кнопка устарела. Откройте /tasks."))
        return
    await callback.answer()
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if user is None:
        await state.clear()
        await message.answer(tr("Сначала зарегистрируйтесь: /start"))
        return
    action, *args = parts[2].split(":")
    mode, page = data.get("task_mode", "active"), data.get("task_page", 0)
    if action == "new":
        await begin(message, state, user)
    elif action in ("list", "back"):
        if action == "list":
            mode, page = args[0], int(args[1])
        await browse(message, state, user_id, mode, page)
    elif action == "value":
        await accept(message, state, user_id, None if args[0] == "none" else args[0])
    elif action == "save":
        draft = dict(data["task_draft"])
        if draft["deadline"]:
            draft["deadline"] = datetime.fromisoformat(draft["deadline"])
        await state.update_data(ui_token=None, task_actions=[])
        await db.add_task(user_id, **draft)
        await browse(message, state, user_id, notice=tr("Задача создана.\n\n"))
    else:
        task_id = int(args[0])
        task = await db.get_task(user_id, task_id)
        if task is None:
            await browse(
                message, state, user_id, mode, page, tr("Задача уже удалена.\n\n")
            )
        elif action == "edit":
            await state.set_state(TaskState.edit)
            await state.update_data(task_id=task_id, task_field=args[1])
            await prompt(message, state)
        elif action == "delete":
            await state.set_state(TaskState.delete)
            await screen(
                message,
                state,
                tr("<b>Удалить задачу?</b>\n") + card(task),
                [[(tr("🗑 Да, удалить"), f"remove:{task_id}"), (tr("Нет"), "back")]],
            )
        elif action in ("remove", "complete"):
            await state.update_data(ui_token=None, task_actions=[])
            if action == "remove":
                ok = await db.delete_task(user_id, task_id)
            else:
                ok = await db.update_task(
                    user_id, task_id, is_completed=bool(int(args[1]))
                )
            await browse(
                message,
                state,
                user_id,
                mode,
                page,
                tr("Готово.\n\n" if ok else "Задача уже удалена.\n\n"),
            )


@router.message(
    StateFilter(TaskState),
    lambda message: (
        not message.text
        or (not message.text.startswith("/") and message.text not in MENU_TEXTS)
    ),
)
async def task_input(message: Message, state: FSMContext):
    current = await state.get_state()
    if current not in (TaskState.create.state, TaskState.edit.state):
        await message.answer(tr("Используйте кнопки последнего сообщения или /cancel."))
        return
    if message.text is None:
        await message.answer(tr("Отправьте текст, а не файл, фото или стикер."))
        return
    data = await state.get_data()
    field, value = data["task_field"], message.text.strip()
    if field == "priority":
        await message.answer(tr("Выберите приоритет кнопкой в последнем сообщении."))
        return
    if field == "deadline":
        if value == "-":
            value = None
        else:
            try:
                value = datetime.strptime(value, DATE_FORMAT)
            except ValueError:
                await message.answer(
                    tr("Неверная дата. Формат: ДД.ММ.ГГГГ ЧЧ:ММ, либо «-» без срока.")
                )
                return
    elif field == "subject_name" and value == "-":
        value = None
    elif not 1 <= len(value) <= (255 if field == "text" else 100):
        await message.answer(
            tr("Нужно от 1 до {limit} символов.", limit=255 if field == "text" else 100)
        )
        return
    if await db.get_user(message.from_user.id) is None:
        await state.clear()
        await message.answer(tr("Сначала зарегистрируйтесь: /start"))
        return
    await accept(message, state, message.from_user.id, value)
