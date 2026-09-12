"""Task UI translations; Russian templates are the canonical keys."""

CATALOG = {
    "Часовой пояс: <b>{timezone}</b>. Сейчас: {now}.\nДедлайны вводятся и хранятся в вашем местном времени, без перевода в UTC.": {
        "en": "Time zone: <b>{timezone}</b>. Now: {now}.\nDeadlines are entered and stored in your local time, without conversion to UTC.",
        "kk": "Уақыт белдеуі: <b>{timezone}</b>. Қазір: {now}.\nТапсыру мерзімдері UTC-ге ауыстырылмай, жергілікті уақытыңызбен енгізіледі және сақталады.",
    },
    "Текст": {"en": "Text", "kk": "Мәтін"},
    "Дедлайн": {"en": "Deadline", "kk": "Тапсыру мерзімі"},
    "Предмет": {"en": "Subject", "kk": "Пән"},
    "Приоритет": {"en": "Priority", "kk": "Басымдық"},
    "Активные": {"en": "Active", "kk": "Орындалмаған"},
    "Выполненные": {"en": "Completed", "kk": "Орындалған"},
    "Все": {"en": "All", "kk": "Барлығы"},
    "➕ Добавить": {"en": "➕ Add", "kk": "➕ Қосу"},
    "📝 <b>Дедлайны</b>\n": {
        "en": "📝 <b>Deadlines</b>\n",
        "kk": "📝 <b>Тапсыру мерзімдері</b>\n",
    },
    "\n\nЗадача {number} из {total}": {
        "en": "\n\nTask {number} of {total}",
        "kk": "\n\n{total} тапсырманың {number}-сі",
    },
    "✏️ {field}": {"en": "✏️ {field}", "kk": "✏️ {field}"},
    "↩️ Возобновить": {"en": "↩️ Reopen", "kk": "↩️ Қайта ашу"},
    "✅ Выполнить": {"en": "✅ Mark complete", "kk": "✅ Орындалды деп белгілеу"},
    "🗑 Удалить": {"en": "🗑 Delete", "kk": "🗑 Жою"},
    "←": {"en": "←", "kk": "←"},
    "→": {"en": "→", "kk": "→"},
    "Задач нет.": {"en": "No tasks.", "kk": "Тапсырмалар жоқ."},
    "Не указан": {"en": "Not specified", "kk": "Көрсетілмеген"},
    "<b>{task_text}</b>\nПредмет: {subject}\nДедлайн: {deadline}\nПриоритет: {priority}\nСтатус: {status}": {
        "en": "<b>{task_text}</b>\nSubject: {subject}\nDeadline: {deadline}\nPriority: {priority}\nStatus: {status}",
        "kk": "<b>{task_text}</b>\nПән: {subject}\nТапсыру мерзімі: {deadline}\nБасымдық: {priority}\nКүйі: {status}",
    },
    "🔴 Высокий": {"en": "🔴 High", "kk": "🔴 Жоғары"},
    "Высокий": {"en": "High", "kk": "Жоғары"},
    "Обычный": {"en": "Normal", "kk": "Қалыпты"},
    "✅ Выполнена": {"en": "✅ Completed", "kk": "✅ Орындалды"},
    "В работе": {"en": "In progress", "kk": "Орындалуда"},
    "Сначала зарегистрируйтесь: /start": {
        "en": "Please register first: /start",
        "kk": "Алдымен тіркеліңіз: /start",
    },
    "Введите текст задачи (1–255 символов).": {
        "en": "Enter the task text (1–255 characters).",
        "kk": "Тапсырма мәтінін енгізіңіз (1–255 таңба).",
    },
    "Введите дедлайн: ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2026 18:00), либо «-» без срока.": {
        "en": "Enter the deadline: DD.MM.YYYY HH:MM (e.g. 25.12.2026 18:00), or '-' for no deadline.",
        "kk": "Тапсыру мерзімін КК.АА.ЖЖЖЖ СС:ММ пішімінде енгізіңіз (мысалы, 25.12.2026 18:00), мерзімі болмаса, «-» енгізіңіз.",
    },
    "Введите предмет (1–100 символов), либо «-» без предмета.": {
        "en": "Enter the subject (1–100 characters), or '-' for no subject.",
        "kk": "Пәнді енгізіңіз (1–100 таңба), пән болмаса, «-» енгізіңіз.",
    },
    "Выберите приоритет кнопкой ниже.": {
        "en": "Choose a priority using a button below.",
        "kk": "Төмендегі батырма арқылы басымдықты таңдаңыз.",
    },
    "Без срока": {"en": "No deadline", "kk": "Мерзімсіз"},
    "Без предмета": {"en": "No subject", "kk": "Пәнсіз"},
    "Отмена": {"en": "Cancel", "kk": "Бас тарту"},
    "\n/cancel — отменить.": {
        "en": "\n/cancel — cancel.",
        "kk": "\n/cancel — бас тарту.",
    },
    "Сохранено.\n\n": {"en": "Saved.\n\n", "kk": "Сақталды.\n\n"},
    "Задача уже удалена.\n\n": {
        "en": "This task has already been deleted.\n\n",
        "kk": "Бұл тапсырма бұрын жойылған.\n\n",
    },
    "<b>Создать задачу?</b>\n{task_text}\nПредмет: {subject}\nДедлайн: {deadline}\nПриоритет: {priority}": {
        "en": "<b>Create task?</b>\n{task_text}\nSubject: {subject}\nDeadline: {deadline}\nPriority: {priority}",
        "kk": "<b>Тапсырма жасалсын ба?</b>\n{task_text}\nПән: {subject}\nТапсыру мерзімі: {deadline}\nБасымдық: {priority}",
    },
    "✅ Создать": {"en": "✅ Create", "kk": "✅ Жасау"},
    "Меню устарело. Откройте /tasks.": {
        "en": "This menu is out of date. Open /tasks.",
        "kk": "Бұл мәзір ескірген. /tasks пәрменін ашыңыз.",
    },
    "Эта кнопка устарела. Откройте /tasks.": {
        "en": "This button is out of date. Open /tasks.",
        "kk": "Бұл батырма ескірген. /tasks пәрменін ашыңыз.",
    },
    "Задача создана.\n\n": {"en": "Task created.\n\n", "kk": "Тапсырма жасалды.\n\n"},
    "<b>Удалить задачу?</b>\n": {
        "en": "<b>Delete task?</b>\n",
        "kk": "<b>Тапсырма жойылсын ба?</b>\n",
    },
    "🗑 Да, удалить": {"en": "🗑 Yes, delete", "kk": "🗑 Иә, жою"},
    "Нет": {"en": "No", "kk": "Жоқ"},
    "Готово.\n\n": {"en": "Done.\n\n", "kk": "Дайын.\n\n"},
    "Используйте кнопки последнего сообщения или /cancel.": {
        "en": "Use the buttons in the latest message or /cancel.",
        "kk": "Соңғы хабарламадағы батырмаларды немесе /cancel пәрменін пайдаланыңыз.",
    },
    "Отправьте текст, а не файл, фото или стикер.": {
        "en": "Send text, not a file, photo, or sticker.",
        "kk": "Файл, фото немесе стикер емес, мәтін жіберіңіз.",
    },
    "Выберите приоритет кнопкой в последнем сообщении.": {
        "en": "Choose a priority using a button in the latest message.",
        "kk": "Соңғы хабарламадағы батырма арқылы басымдықты таңдаңыз.",
    },
    "Неверная дата. Формат: ДД.ММ.ГГГГ ЧЧ:ММ, либо «-» без срока.": {
        "en": "Invalid date. Use DD.MM.YYYY HH:MM, or '-' for no deadline.",
        "kk": "Күн қате енгізілген. КК.АА.ЖЖЖЖ СС:ММ пішімін пайдаланыңыз, мерзімі болмаса, «-» енгізіңіз.",
    },
    "Нужно от 1 до {limit} символов.": {
        "en": "Enter between 1 and {limit} characters.",
        "kk": "1–{limit} таңба енгізіңіз.",
    },
}
