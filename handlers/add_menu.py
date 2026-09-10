from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from database.db_requests import add_lesson

router = Router()

# 1. Создаем "состояния" (шаги), по которым будем вести пользователя
class AddLessonState(StatesGroup):
    subject = State()
    day = State()
    time = State()
    location = State()

# 2. Ловим кнопку главного меню "➕ Добавить"
@router.message(F.text == "➕ Добавить")
async def add_menu(message: Message):
    # Рисуем кнопку под сообщением
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Добавить пару", callback_data="add_lesson_btn")]
    ])
    await message.answer("Что именно хочешь добавить?", reply_markup=kb)

# 3. Ловим нажатие на Inline-кнопку и запускаем первый шаг FSM
@router.callback_query(F.data == "add_lesson_btn")
async def start_adding_lesson(callback: CallbackQuery, state: FSMContext):
    await callback.answer() # Убираем "часики" загрузки на кнопке
    await state.set_state(AddLessonState.subject) # Включаем состояние
    await callback.message.answer("📚 Введи название предмета (например: Высшая математика):")

# 4. Шаг 1: Сохраняем предмет, спрашиваем день недели
@router.message(AddLessonState.subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text) # Запоминаем текст
    
    # Делаем сетку кнопок с днями недели
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пн", callback_data="day_1"),
            InlineKeyboardButton(text="Вт", callback_data="day_2"),
            InlineKeyboardButton(text="Ср", callback_data="day_3")
        ],
        [
            InlineKeyboardButton(text="Чт", callback_data="day_4"),
            InlineKeyboardButton(text="Пт", callback_data="day_5"),
            InlineKeyboardButton(text="Сб", callback_data="day_6")
        ]
    ])
    await state.set_state(AddLessonState.day)
    await message.answer("🗓 Выбери день недели:", reply_markup=kb)

# 5. Шаг 2: Сохраняем день, спрашиваем время
@router.callback_query(AddLessonState.day, F.data.startswith("day_"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Вытаскиваем цифру из callback_data (например, из "day_1" достанем 1)
    day_number = int(callback.data.split("_")[1])
    await state.update_data(day=day_number)
    
    await state.set_state(AddLessonState.time)
    await callback.message.answer("⏰ Введи время начала и конца через дефис\n(например: <b>08:30-10:05</b>):", parse_mode="HTML")

# 6. Шаг 3: Сохраняем время, спрашиваем локацию
@router.message(AddLessonState.time)
async def process_time(message: Message, state: FSMContext):
    try:
        # Пытаемся разбить текст "08:30-10:05" на два куска и превратить во время
        start_str, end_str = message.text.split("-")
        start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
        end_time = datetime.strptime(end_str.strip(), "%H:%M").time()
        
        await state.update_data(start_time=start_time, end_time=end_time)
        await state.set_state(AddLessonState.location)
        await message.answer("📍 Где будет пара и какой тип? (например: Ауд. 302, Лекция):")
    except ValueError:
        # Если юзер ввел бред, FSM не переключится, а просто попросит ввести еще раз
        await message.answer("❌ Ошибка формата! Напиши точно так: 08:30-10:05")

# 7. Шаг 4: Сохраняем локацию и записываем всё в Базу Данных!
@router.message(AddLessonState.location)
async def process_location(message: Message, state: FSMContext):
    # Достаем всё, что бот запомнил на предыдущих шагах
    data = await state.get_data()
    
    # Отправляем в нашу базу
    await add_lesson(
        user_id=message.from_user.id,
        subject=data['subject'],
        day_of_week=data['day'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        location=message.text
    )
    
    # Обязательно выключаем FSM, чтобы бот снова начал реагировать на обычные кнопки
    await state.clear()
    await message.answer("✅ <b>Пара успешно добавлена в расписание!</b>", parse_mode="HTML")
