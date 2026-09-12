"""Add-menu entry; lesson wizard lives in schedule, tasks use their own router."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from services.i18n import tr

from handlers.schedule import screen, session_lock

router = Router()
router.message.middleware(session_lock)


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def add_menu(message: Message, state: FSMContext):
    await state.clear()
    await screen(
        message,
        state,
        tr("Что хотите добавить?"),
        [
            [(tr("📅 Добавить пару"), "new")],
            [(tr("📝 Добавить задачу"), "task:add")],
        ],
    )
