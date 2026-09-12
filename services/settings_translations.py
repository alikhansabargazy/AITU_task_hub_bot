"""Russian source templates and English/Kazakh UI translations.

Register at handler import time; translate at render time, never at import time.
User-provided values are escaped by the handlers and passed as format arguments.
"""

CATALOG = {
    "Русский": {"en": "Russian", "kk": "Орысша"},
    "Английский": {"en": "English", "kk": "Ағылшынша"},
    "Казахский": {"en": "Kazakh", "kk": "Қазақша"},
    "🗣 Язык": {"en": "🗣 Language", "kk": "🗣 Тіл"},
    "🗣 <b>Язык интерфейса</b>\nВыберите язык:": {
        "en": "🗣 <b>Interface language</b>\nChoose a language:",
        "kk": "🗣 <b>Интерфейс тілі</b>\nТілді таңдаңыз:",
    },
    "✅ Язык изменён. Главное меню обновлено.": {
        "en": "✅ Language changed. Main menu updated.",
        "kk": "✅ Тіл өзгертілді. Негізгі мәзір жаңартылды.",
    },
    "числитель": {"en": "numerator", "kk": "алым"},
    "знаменатель": {"en": "denominator", "kk": "бөлім"},
    "в момент начала пары": {
        "en": "when the class starts",
        "kk": "сабақ басталған кезде",
    },
    "за {minutes} мин.": {"en": "{minutes} min before", "kk": "{minutes} минут бұрын"},
    "включены": {"en": "enabled", "kk": "қосулы"},
    "выключены": {"en": "disabled", "kk": "өшірулі"},
    (
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
        "Горизонт дашборда включает сегодня. Просроченные задачи показываются независимо от горизонта."
    ): {
        "en": (
            "⚙️ <b>Settings</b>\n\n{notice}"
            "🗣 Language: {language}\n"
            "🌐 Time zone: <code>{timezone}</code>\n"
            "🔔 Notifications: {notifications}\n"
            "⏰ Reminder: {reminder}\n"
            "🔁 Week parity offset: {offset}\n"
            "Today: ISO week {week}, {parity}\n"
            "🏠 Deadline horizon: {days} days\n\n"
            "Weeks follow ISO: they start on Monday, and week 1 contains January 4. "
            "With offset 0, odd weeks are numerator weeks and even weeks are denominator weeks; "
            "offset 1 swaps them.\n\n"
            "The dashboard horizon includes today. Overdue tasks are shown regardless of the horizon."
        ),
        "kk": (
            "⚙️ <b>Баптаулар</b>\n\n{notice}"
            "🗣 Тіл: {language}\n"
            "🌐 Уақыт белдеуі: <code>{timezone}</code>\n"
            "🔔 Хабарландырулар: {notifications}\n"
            "⏰ Еске салу: {reminder}\n"
            "🔁 Апта жұптылығының ығысуы: {offset}\n"
            "Бүгін: ISO бойынша {week}-апта, {parity}\n"
            "🏠 Мерзімдерді көрсету аралығы: {days} күн\n\n"
            "Апталар ISO бойынша есептеледі: дүйсенбіден басталады, 1-аптаға 4 қаңтар кіреді. "
            "Ығысу 0 болса, тақ апта — алым, жұп апта — бөлім; "
            "ығысу 1 болса, олардың орны ауысады.\n\n"
            "Басқару панелінің көрсету аралығына бүгінгі күн кіреді. Мерзімі өткен тапсырмалар аралыққа қарамастан көрсетіледі."
        ),
    },
    "🌐 Часовой пояс": {"en": "🌐 Time zone", "kk": "🌐 Уақыт белдеуі"},
    "🔕 Выключить уведомления": {
        "en": "🔕 Disable notifications",
        "kk": "🔕 Хабарландыруларды өшіру",
    },
    "🔔 Включить уведомления": {
        "en": "🔔 Enable notifications",
        "kk": "🔔 Хабарландыруларды қосу",
    },
    "⏰ Напоминание": {"en": "⏰ Reminder", "kk": "⏰ Еске салу"},
    "🔁 Чётность недели": {"en": "🔁 Week parity", "kk": "🔁 Апта жұптылығы"},
    "🏠 Горизонт дашборда": {
        "en": "🏠 Dashboard horizon",
        "kk": "🏠 Панельдің көрсету аралығы",
    },
    "🔄 Обновить": {"en": "🔄 Refresh", "kk": "🔄 Жаңарту"},
    "Этот экран устарел. Откройте /settings заново.": {
        "en": "This screen is outdated. Open /settings again.",
        "kk": "Бұл экран ескірген. /settings пәрменін қайта ашыңыз.",
    },
    "Неизвестная настройка.": {"en": "Unknown setting.", "kk": "Белгісіз баптау."},
    (
        "🌐 <b>Часовой пояс</b>\n\nВыберите IANA-зону или введите её вручную.\n"
        "Алматы и Астана используют <code>Asia/Almaty</code>.\n"
        "Время пар и naive-дедлайнов хранится как местное время: смена зоны не пересчитывает их часы."
    ): {
        "en": (
            "🌐 <b>Time zone</b>\n\nChoose an IANA zone or enter one manually.\n"
            "Almaty and Astana use <code>Asia/Almaty</code>.\n"
            "Class times and deadlines without time zone information are stored as local time: changing the zone does not convert their clock times."
        ),
        "kk": (
            "🌐 <b>Уақыт белдеуі</b>\n\nIANA белдеуін таңдаңыз немесе қолмен енгізіңіз.\n"
            "Алматы мен Астана <code>Asia/Almaty</code> белдеуін пайдаланады.\n"
            "Сабақ уақыты мен уақыт белдеуі көрсетілмеген мерзімдер жергілікті уақыт ретінде сақталады: белдеуді өзгерту олардың сағатын қайта есептемейді."
        ),
    },
    "Алматы / Астана": {"en": "Almaty / Astana", "kk": "Алматы / Астана"},
    "UTC": {"en": "UTC", "kk": "UTC"},
    "Москва": {"en": "Moscow", "kk": "Мәскеу"},
    "✍️ Ввести IANA-зону": {
        "en": "✍️ Enter an IANA zone",
        "kk": "✍️ IANA белдеуін енгізу",
    },
    "← Назад": {"en": "← Back", "kk": "← Артқа"},
    (
        "✍️ Отправьте текстом IANA-зону, например <code>Asia/Almaty</code>, "
        "<code>Europe/Moscow</code> или <code>Europe/Berlin</code>.\n"
        "Регистр важен. Смещения вида UTC+5 не подходят.\n"
        "Можно ответить на это сообщение. Для отмены нажмите кнопку ниже или /settings."
    ): {
        "en": (
            "✍️ Send an IANA zone as text, for example <code>Asia/Almaty</code>, "
            "<code>Europe/Moscow</code> or <code>Europe/Berlin</code>.\n"
            "Names are case-sensitive. Offsets such as UTC+5 are not accepted.\n"
            "You can reply to this message. To cancel, use the button below or /settings."
        ),
        "kk": (
            "✍️ IANA белдеуін мәтінмен жіберіңіз, мысалы <code>Asia/Almaty</code>, "
            "<code>Europe/Moscow</code> немесе <code>Europe/Berlin</code>.\n"
            "Бас және кіші әріптер маңызды. UTC+5 түріндегі ығысулар қабылданбайды.\n"
            "Осы хабарламаға жауап бере аласыз. Бас тарту үшін төмендегі түймені немесе /settings пәрменін пайдаланыңыз."
        ),
    },
    "Отмена": {"en": "Cancel", "kk": "Бас тарту"},
    "⏰ За сколько минут до пары напоминать?\n0 — в момент начала, не отключение уведомлений.": {
        "en": "⏰ How many minutes before class should the reminder arrive?\n0 means at the start, not disabling notifications.",
        "kk": "⏰ Сабақ басталғанға дейін неше минут бұрын еске салу керек?\n0 — сабақ басталған кезде, хабарландыруларды өшіру емес.",
    },
    "🔁 Смещение ISO-чётности\n0: нечётная ISO-неделя — числитель, чётная — знаменатель.\n1: наоборот. ISO-неделя начинается в понедельник; неделя №1 содержит 4 января.": {
        "en": "🔁 ISO week parity offset\n0: odd ISO weeks are numerator weeks, even weeks are denominator weeks.\n1: the reverse. ISO weeks start on Monday; week 1 contains January 4.",
        "kk": "🔁 ISO апта жұптылығының ығысуы\n0: ISO бойынша тақ апта — алым, жұп апта — бөлім.\n1: керісінше. ISO аптасы дүйсенбіден басталады; 1-аптаға 4 қаңтар кіреді.",
    },
    "🏠 На сколько календарных дней показывать дедлайны, включая сегодня?": {
        "en": "🏠 For how many calendar days should deadlines be shown, including today?",
        "kk": "🏠 Бүгінгі күнді қоса алғанда, мерзімдер неше күнтізбелік күнге көрсетілсін?",
    },
    "В момент начала (0)": {"en": "At the start (0)", "kk": "Басталған кезде (0)"},
    "За {minutes} мин.": {"en": "{minutes} min before", "kk": "{minutes} минут бұрын"},
    "{days} дн.": {"en": "{days} days", "kk": "{days} күн"},
    "✓ {label}": {"en": "✓ {label}", "kk": "✓ {label}"},
    "✅ Настройка сохранена.\n\n": {
        "en": "✅ Setting saved.\n\n",
        "kk": "✅ Баптау сақталды.\n\n",
    },
    "⚠️ База часовых поясов недоступна на сервере.\n\n": {
        "en": "⚠️ The time zone database is unavailable on the server.\n\n",
        "kk": "⚠️ Серверде уақыт белдеулерінің дерекқоры қолжетімсіз.\n\n",
    },
    "Это ответ на старый экран. Ответьте на последний запрос часового пояса или откройте /settings.": {
        "en": "This is a reply to an old screen. Reply to the latest time zone prompt or open /settings.",
        "kk": "Бұл — ескі экранға жауап. Уақыт белдеуі туралы соңғы сұрауға жауап беріңіз немесе /settings пәрменін ашыңыз.",
    },
    "Нужен текст с IANA-зоной, например Asia/Almaty, а не фото, файл или стикер.": {
        "en": "Send an IANA zone as text, such as Asia/Almaty, not a photo, file or sticker.",
        "kk": "Фото, файл немесе стикер емес, Asia/Almaty сияқты IANA белдеуі бар мәтін қажет.",
    },
    "Введите IANA-зону длиной от 1 до 50 символов, например Asia/Almaty.": {
        "en": "Enter an IANA zone of 1 to 50 characters, such as Asia/Almaty.",
        "kk": "Ұзындығы 1–50 таңбадан тұратын IANA белдеуін енгізіңіз, мысалы Asia/Almaty.",
    },
    "Неизвестная IANA-зона. Проверьте регистр и название, например Europe/Moscow. Если верное имя не принимается, проверьте базу часовых поясов сервера.": {
        "en": "Unknown IANA zone. Check the spelling and letter case, for example Europe/Moscow. If a correct name is rejected, check the server's time zone database.",
        "kk": "Белгісіз IANA белдеуі. Атауын және бас-кіші әріптерді тексеріңіз, мысалы Europe/Moscow. Дұрыс атау қабылданбаса, сервердегі уақыт белдеулерінің дерекқорын тексеріңіз.",
    },
    "✅ Часовой пояс сохранён.\n\n": {
        "en": "✅ Time zone saved.\n\n",
        "kk": "✅ Уақыт белдеуі сақталды.\n\n",
    },
    "понедельник": {"en": "Monday", "kk": "дүйсенбі"},
    "вторник": {"en": "Tuesday", "kk": "сейсенбі"},
    "среда": {"en": "Wednesday", "kk": "сәрсенбі"},
    "четверг": {"en": "Thursday", "kk": "бейсенбі"},
    "пятница": {"en": "Friday", "kk": "жұма"},
    "суббота": {"en": "Saturday", "kk": "сенбі"},
    "воскресенье": {"en": "Sunday", "kk": "жексенбі"},
    " · {location}": {"en": " · {location}", "kk": " · {location}"},
    "{start:%d.%m %H:%M}–{end} · <b>{subject}</b>{location}": {
        "en": "{start:%d.%m %H:%M}–{end} · <b>{subject}</b>{location}",
        "kk": "{start:%d.%m %H:%M}–{end} · <b>{subject}</b>{location}",
    },
    "🏠 <b>Дашборд</b>": {
        "en": "🏠 <b>Dashboard</b>",
        "kk": "🏠 <b>Басқару панелі</b>",
    },
    "📅 {now:%d.%m.%Y %H:%M} · {weekday}": {
        "en": "📅 {now:%d.%m.%Y %H:%M} · {weekday}",
        "kk": "📅 {now:%d.%m.%Y %H:%M} · {weekday}",
    },
    "🌐 <code>{timezone}</code> · UTC{now:%z}": {
        "en": "🌐 <code>{timezone}</code> · UTC{now:%z}",
        "kk": "🌐 <code>{timezone}</code> · UTC{now:%z}",
    },
    "ISO-неделя {week} · {parity}": {
        "en": "ISO week {week} · {parity}",
        "kk": "ISO бойынша {week}-апта · {parity}",
    },
    "🎓 <b>Пар сегодня: {count}</b>": {
        "en": "🎓 <b>Classes today: {count}</b>",
        "kk": "🎓 <b>Бүгінгі сабақтар: {count}</b>",
    },
    "Сейчас: {lesson}": {"en": "Now: {lesson}", "kk": "Қазір: {lesson}"},
    "пары нет.": {"en": "no class.", "kk": "сабақ жоқ."},
    "Ещё одновременно идут пары: {count}.": {
        "en": "Other classes in progress: {count}.",
        "kk": "Бір уақытта өтіп жатқан басқа сабақтар: {count}.",
    },
    "Следующая: {lesson}": {"en": "Next: {lesson}", "kk": "Келесі: {lesson}"},
    "нет в ближайшие 14 дней (включая сегодня).": {
        "en": "none in the next 14 days (including today).",
        "kk": "алдағы 14 күнде жоқ (бүгінгі күнді қоса алғанда).",
    },
    "📝 <b>Активных задач: {count}</b>": {
        "en": "📝 <b>Active tasks: {count}</b>",
        "kk": "📝 <b>Белсенді тапсырмалар: {count}</b>",
    },
    "Просрочено: {overdue} · В горизонте: {upcoming} · Без срока: {undated}": {
        "en": "Overdue: {overdue} · Within horizon: {upcoming} · No deadline: {undated}",
        "kk": "Мерзімі өткен: {overdue} · Аралықта: {upcoming} · Мерзімсіз: {undated}",
    },
    "Горизонт: {start:%d.%m.%Y}–{end:%d.%m.%Y} ({days} дн., включая сегодня).": {
        "en": "Horizon: {start:%d.%m.%Y}–{end:%d.%m.%Y} ({days} days, including today).",
        "kk": "Көрсету аралығы: {start:%d.%m.%Y}–{end:%d.%m.%Y} ({days} күн, бүгінгі күнді қоса алғанда).",
    },
    "За горизонтом: {count}. Все сроки — местное время.": {
        "en": "Beyond horizon: {count}. All deadlines are in local time.",
        "kk": "Аралықтан тыс: {count}. Барлық мерзімдер жергілікті уақытпен көрсетілген.",
    },
    "🔥 Просроченные": {"en": "🔥 Overdue", "kk": "🔥 Мерзімі өткен"},
    "⏳ Ближайшие дедлайны": {
        "en": "⏳ Upcoming deadlines",
        "kk": "⏳ Жақында аяқталатын мерзімдер",
    },
    "📌 Без срока": {"en": "📌 No deadline", "kk": "📌 Мерзімсіз"},
    "<b>{title}</b>": {"en": "<b>{title}</b>", "kk": "<b>{title}</b>"},
    "Нет.": {"en": "None.", "kk": "Жоқ."},
    "• {deadline:%d.%m.%Y %H:%M} — {task_text}": {
        "en": "• {deadline:%d.%m.%Y %H:%M} — {task_text}",
        "kk": "• {deadline:%d.%m.%Y %H:%M} — {task_text}",
    },
    "• {task_text}": {"en": "• {task_text}", "kk": "• {task_text}"},
    "Ещё: {count}. Полный список — в «📝 Дедлайны».": {
        "en": "More: {count}. Full list in “📝 Deadlines”.",
        "kk": "Тағы: {count}. Толық тізім «📝 Мерзімдер» бөлімінде.",
    },
    (
        "🏠 <b>Дашборд</b>\n📅 {now:%d.%m.%Y %H:%M}\n"
        "🌐 <code>{timezone}</code>\n"
        "Пар сегодня: {lessons}\nАктивных задач: {active}\n"
        "Просрочено: {overdue}\nВ ближайшие {days} дн.: {upcoming}\n"
        "Без срока: {undated}\nЗа горизонтом: {later}\n"
        "Подробности — в «📅 Расписание» и «📝 Дедлайны»."
    ): {
        "en": (
            "🏠 <b>Dashboard</b>\n📅 {now:%d.%m.%Y %H:%M}\n"
            "🌐 <code>{timezone}</code>\n"
            "Classes today: {lessons}\nActive tasks: {active}\n"
            "Overdue: {overdue}\nWithin the next {days} days: {upcoming}\n"
            "No deadline: {undated}\nBeyond horizon: {later}\n"
            "Details in “📅 Schedule” and “📝 Deadlines”."
        ),
        "kk": (
            "🏠 <b>Басқару панелі</b>\n📅 {now:%d.%m.%Y %H:%M}\n"
            "🌐 <code>{timezone}</code>\n"
            "Бүгінгі сабақтар: {lessons}\nБелсенді тапсырмалар: {active}\n"
            "Мерзімі өткен: {overdue}\nАлдағы {days} күнде: {upcoming}\n"
            "Мерзімсіз: {undated}\nАралықтан тыс: {later}\n"
            "Толығырақ «📅 Сабақ кестесі» және «📝 Мерзімдер» бөлімдерінде."
        ),
    },
    "Откройте свой дашборд командой /dashboard.": {
        "en": "Open your own dashboard with /dashboard.",
        "kk": "/dashboard пәрменімен өз басқару панеліңізді ашыңыз.",
    },
    "Сообщение недоступно. Откройте /dashboard.": {
        "en": "Message unavailable. Open /dashboard.",
        "kk": "Хабарлама қолжетімсіз. /dashboard пәрменін ашыңыз.",
    },
}
