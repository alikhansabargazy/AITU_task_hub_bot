"""Schedule/add-menu catalog. Russian keys are the default-locale templates."""

CATALOG = {
    "Понедельник": {"en": "Monday", "kk": "Дүйсенбі"},
    "Вторник": {"en": "Tuesday", "kk": "Сейсенбі"},
    "Среда": {"en": "Wednesday", "kk": "Сәрсенбі"},
    "Четверг": {"en": "Thursday", "kk": "Бейсенбі"},
    "Пятница": {"en": "Friday", "kk": "Жұма"},
    "Суббота": {"en": "Saturday", "kk": "Сенбі"},
    "Воскресенье": {"en": "Sunday", "kk": "Жексенбі"},
    "Каждую неделю": {"en": "Every week", "kk": "Әр апта"},
    "Числитель": {"en": "Numerator (odd week)", "kk": "Алым (тақ апта)"},
    "Знаменатель": {"en": "Denominator (even week)", "kk": "Бөлім (жұп апта)"},
    "Предмет": {"en": "Subject", "kk": "Пән"},
    "День недели": {"en": "Day of the week", "kk": "Апта күні"},
    "Чётность": {"en": "Week parity", "kk": "Аптаның жұп/тақтығы"},
    "Начало и конец": {
        "en": "Start and end times",
        "kk": "Басталу және аяқталу уақыты",
    },
    "Аудитория / место": {"en": "Room / location", "kk": "Аудитория / орын"},
    "Преподаватель": {"en": "Teacher", "kk": "Оқытушы"},
    "Тип занятия": {"en": "Lesson type", "kk": "Сабақ түрі"},
    "Не указано": {"en": "Not specified", "kk": "Көрсетілмеген"},
    "Не указан": {"en": "Not specified", "kk": "Көрсетілмеген"},
    "<b>{subject}</b>\n{day} · {parity}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}\nТип: {lesson_type}": {
        "en": "<b>{subject}</b>\n{day} · {parity}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}\nType: {lesson_type}",
        "kk": "<b>{subject}</b>\n{day} · {parity}\n⏰ {start}–{end}\n📍 {location}\n👤 {teacher}\nТүрі: {lesson_type}",
    },
    "Сегодня": {"en": "Today", "kk": "Бүгін"},
    "Завтра": {"en": "Tomorrow", "kk": "Ертең"},
    "Дни недели": {"en": "Days of the week", "kk": "Апта күндері"},
    "Вся неделя": {"en": "Full week", "kk": "Толық апта"},
    "➕ Добавить пару": {"en": "➕ Add lesson", "kk": "➕ Сабақ қосу"},
    "📅 <b>Расписание</b>": {
        "en": "📅 <b>Schedule</b>",
        "kk": "📅 <b>Сабақ кестесі</b>",
    },
    "Сначала зарегистрируйтесь: /start": {
        "en": "Please register first: /start",
        "kk": "Алдымен тіркеліңіз: /start",
    },
    "{day} {date} · {parity}": {
        "en": "{day} {date} · {parity}",
        "kk": "{day} {date} · {parity}",
    },
    "Вся неделя · обе чётности": {
        "en": "Full week · odd and even weeks",
        "kk": "Толық апта · тақ және жұп апталар",
    },
    "{day} · обе чётности": {
        "en": "{day} · odd and even weeks",
        "kk": "{day} · тақ және жұп апталар",
    },
    "<b>{title}</b>\n\n": {"en": "<b>{title}</b>\n\n", "kk": "<b>{title}</b>\n\n"},
    "{lesson}\n\nПара {page} из {total}": {
        "en": "{lesson}\n\nLesson {page} of {total}",
        "kk": "{lesson}\n\nСабақ {page} / {total}",
    },
    "✏️ Редактировать": {"en": "✏️ Edit", "kk": "✏️ Өңдеу"},
    "🗑 Удалить": {"en": "🗑 Delete", "kk": "🗑 Жою"},
    "←": {"en": "←", "kk": "←"},
    "→": {"en": "→", "kk": "→"},
    "Пар нет.": {"en": "No lessons.", "kk": "Сабақ жоқ."},
    "Выберите день недели:": {
        "en": "Choose a day of the week:",
        "kk": "Апта күнін таңдаңыз:",
    },
    "Выберите чётность недели:": {
        "en": "Choose the week parity:",
        "kk": "Аптаның жұп/тақтығын таңдаңыз:",
    },
    "Введите начало и конец: <b>08:30-10:05</b>. Конец должен быть позже начала.": {
        "en": "Enter start and end times: <b>08:30-10:05</b>. The end must be after the start.",
        "kk": "Басталу және аяқталу уақытын енгізіңіз: <b>08:30-10:05</b>. Аяқталу уақыты басталу уақытынан кейін болуы керек.",
    },
    "{field}: введите текст (до {limit} символов).": {
        "en": "{field}: enter text (up to {limit} characters).",
        "kk": "{field}: мәтін енгізіңіз ({limit} таңбаға дейін).",
    },
    " Для пустого значения отправьте <b>-</b>.": {
        "en": " Send <b>-</b> to leave it empty.",
        "kk": " Бос қалдыру үшін <b>-</b> жіберіңіз.",
    },
    "Не указывать": {"en": "Leave empty", "kk": "Көрсетпеу"},
    "Отменить": {"en": "Cancel", "kk": "Болдырмау"},
    "<b>Проверьте перед сохранением</b>\n\n{lesson}": {
        "en": "<b>Review before saving</b>\n\n{lesson}",
        "kk": "<b>Сақтау алдында тексеріңіз</b>\n\n{lesson}",
    },
    "❌ {error}\n\n{review}": {
        "en": "❌ {error}\n\n{review}",
        "kk": "❌ {error}\n\n{review}",
    },
    "✅ Сохранить": {"en": "✅ Save", "kk": "✅ Сақтау"},
    "✏️ Изменить поля": {"en": "✏️ Edit fields", "kk": "✏️ Өрістерді өзгерту"},
    "Выберите поле:": {"en": "Choose a field:", "kk": "Өрісті таңдаңыз:"},
    "К подтверждению": {"en": "Review changes", "kk": "Растауға өту"},
    "Отправьте текст, а не файл или стикер.": {
        "en": "Send text, not a file or sticker.",
        "kk": "Файл немесе стикер емес, мәтін жіберіңіз.",
    },
    "Выберите день кнопкой или введите число от 1 до 7.": {
        "en": "Choose a day using a button or enter a number from 1 to 7.",
        "kk": "Күнді батырмамен таңдаңыз немесе 1-ден 7-ге дейінгі санды енгізіңіз.",
    },
    "Выберите чётность кнопкой.": {
        "en": "Choose the week parity using a button.",
        "kk": "Аптаның жұп/тақтығын батырмамен таңдаңыз.",
    },
    "Формат времени: 08:30-10:05.": {
        "en": "Time format: 08:30-10:05.",
        "kk": "Уақыт пішімі: 08:30-10:05.",
    },
    "Часы: 00–23, минуты: 00–59.": {
        "en": "Hours: 00–23, minutes: 00–59.",
        "kk": "Сағат: 00–23, минут: 00–59.",
    },
    "Конец должен быть позже начала в пределах одного дня.": {
        "en": "The end must be after the start within the same day.",
        "kk": "Аяқталу уақыты сол күннің ішінде басталу уақытынан кейін болуы керек.",
    },
    "Нужно от 1 до {limit} символов.": {
        "en": "Enter between 1 and {limit} characters.",
        "kk": "1-ден {limit} таңбаға дейін енгізіңіз.",
    },
    "Уберите управляющие и невидимые символы.": {
        "en": "Remove control and invisible characters.",
        "kk": "Басқарушы және көрінбейтін таңбаларды алып тастаңыз.",
    },
    "Эта кнопка устарела. Откройте меню заново.": {
        "en": "This button has expired. Open the menu again.",
        "kk": "Бұл батырма ескірген. Мәзірді қайта ашыңыз.",
    },
    "Действие недоступно.": {
        "en": "This action is unavailable.",
        "kk": "Бұл әрекет қолжетімсіз.",
    },
    "Действие отменено. Расписание:": {
        "en": "Action cancelled. Schedule:",
        "kk": "Әрекет болдырылмады. Сабақ кестесі:",
    },
    "Выберите день (обе чётности):": {
        "en": "Choose a day (odd and even weeks):",
        "kk": "Күнді таңдаңыз (тақ және жұп апталар):",
    },
    "Пара больше не существует.": {
        "en": "This lesson no longer exists.",
        "kk": "Бұл сабақ енді жоқ.",
    },
    "<b>Удалить пару?</b>\n\n{lesson}": {
        "en": "<b>Delete this lesson?</b>\n\n{lesson}",
        "kk": "<b>Сабақты жою керек пе?</b>\n\n{lesson}",
    },
    "🗑 Да, удалить": {"en": "🗑 Yes, delete", "kk": "🗑 Иә, жою"},
    "✅ Пара удалена.": {"en": "✅ Lesson deleted.", "kk": "✅ Сабақ жойылды."},
    "Пара уже удалена или недоступна.": {
        "en": "The lesson has already been deleted or is unavailable.",
        "kk": "Сабақ бұрын жойылған немесе қолжетімсіз.",
    },
    "Конфликт расписания.": {
        "en": "Schedule conflict.",
        "kk": "Сабақ кестесінде қайшылық бар.",
    },
    "✅ Пара сохранена.": {"en": "✅ Lesson saved.", "kk": "✅ Сабақ сақталды."},
    "Что хотите добавить?": {
        "en": "What would you like to add?",
        "kk": "Не қосқыңыз келеді?",
    },
    "📅 Добавить пару": {"en": "📅 Add lesson", "kk": "📅 Сабақ қосу"},
    "📝 Добавить задачу": {"en": "📝 Add task", "kk": "📝 Тапсырма қосу"},
}
