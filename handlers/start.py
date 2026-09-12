from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db_requests import add_user
from services.i18n import main_keyboard, tr

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user(message.from_user.id)
    await message.answer(
        tr(
            "Привет, {name}! 👋\nЯ помогу управлять расписанием и дедлайнами. Язык можно изменить в настройках.",
            name=message.from_user.first_name,
        ),
        reply_markup=main_keyboard(),
    )
    from handlers.dashboard import show_dashboard

    await show_dashboard(message, message.from_user.id)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(tr("Действие отменено."), reply_markup=main_keyboard())


@router.message(Command("help"))
async def help_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        tr("Выберите раздел в меню. /cancel — отменить ввод."),
        reply_markup=main_keyboard(),
    )
