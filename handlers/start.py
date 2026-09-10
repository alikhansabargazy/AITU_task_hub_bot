from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database.db_requests import add_user

# Создаем роутер
router = Router()

# Главное меню бота (кнопки)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📝 Дедлайны")],
        [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие в меню..."
)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Записываем юзера в базу данных
    await add_user(user_id)
    
    welcome_text = (
        f"Привет, {user_name}! 👋\n\n"
        f"Я твой личный университетский ассистент AITU. "
        f"Помогу не забыть про пары и вовремя сдать все дедлайны.\n\n"
        f"👇 Выбери нужное действие в меню ниже."
    )
    
    await message.answer(welcome_text, reply_markup=main_keyboard)
