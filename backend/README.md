# TaskHub API 0.2 — собственные аккаунты

## Запуск без Telegram

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Python 3.10+. Этот набор зависимостей не содержит aiogram/APScheduler.
API не импортирует и не запускает бота, не использует Telegram API или BOT_TOKEN.

SQLite по умолчанию: `db.sqlite3` в корне репозитория. Путь не зависит от cwd.
Для отдельной базы можно задать `DATABASE_URL=sqlite+aiosqlite:////absolute/path/app.sqlite3`
в окружении или игнорируемом файле `.env`. Реализация миграций и rate limiting сейчас
рассчитана на SQLite, не PostgreSQL.

`GET /health` — health check. `/docs` — интерактивная документация.

## Собственные аккаунты

- Логин приводится к lower case, допускает a–z/0–9/_, длина 3–32.
- Пароль 10–128 символов; пробелы не обрезаются.
- Хранится scrypt-хеш с независимой случайной солью (N=32768, r=8, p=3),
  не пароль. Проверка пароля выполняется вне event loop.
- Сервер возвращает случайный 256-битный bearer-токен на 30 дней. В БД хранится
  только SHA-256 токена; его можно отозвать при выходе.
- Смена пароля отзывает все прошлые сессии и возвращает одну новую для текущего клиента.
- Все методы данных получают владельца из сессии; передавать user_id запрещено.
- Старые открытые `/api/v1/users/{user_id}/tasks` удалены.
- Есть SQLite rate limiting входа/регистрации/смены пароля: до 10 попыток на логин
  и 30 на сетевой адрес в минуту. Для неизвестного логина также выполняется scrypt.
- Регистрация нового аккаунта создаёт отдельного пользователя с отрицательным
  внутренним ID; положительные ID старого бота остаются нетронутыми.
- Восстановления по email, OAuth и автоматического импорта данных бота пока нет.
  Запиши свои учётные данные. Старый демонстрационный user_id=1 не присваивается
  первому зарегистрированному аккаунту.

Токен Android хранит с шифрованием Android Keystore; пароли на устройстве не сохраняются.
Снимок данных хранится в приватных данных приложения и исключён из backup/transfer.

## Методы

Все пути ниже начинаются с `/api/v1`.
Кроме register/login и /health, требуется `Authorization: Bearer <access_token>`.
В Swagger можно получить токен через register/login, затем нажать Authorize.

| Метод | Путь | Назначение |
| --- | --- | --- |
| POST | /auth/register | username, password, display_name?, language? |
| POST | /auth/login | username, password |
| POST | /auth/logout | Отозвать текущую сессию |
| PATCH | /auth/password | current_password, new_password; вернуть новую сессию |
| GET | /me | Профиль и настройки |
| GET/PATCH | /me/settings | Язык, зона, уведомления, напоминания, чётность, горизонт |
| GET | /me/dashboard | Структурированная главная страница |
| GET/POST | /me/tasks | Список / создание; GET принимает completed=true/false |
| GET/PATCH/DELETE | /me/tasks/{id} | Чтение / изменение / удаление собственной задачи |
| GET/POST | /me/schedule | Неделя / создание; GET принимает day=1..7 и parity |
| GET/PATCH/DELETE | /me/schedule/{id} | Чтение / изменение / удаление собственной пары |

PATCH изменяет только явно переданные поля. Явный null очищает необязательный
предмет/срок задачи или тип/аудиторию/преподавателя пары. Обязательные поля и
настройки нельзя обнулить. Пустой PATCH и неизвестные поля дают 422.
Чужие идентификаторы дают 404; отсутствие/истечение сессии — 401.
Ошибки валидации не возвращают исходный пароль в поле input.

Время пар — local time, день недели ISO 1=понедельник, 7=воскресенье.
Дедлайн — local naive datetime, например `2026-09-21T18:00:00`, без Z/offset.
Смена часового пояса не пересчитывает сохранённые часы.
Чётность: all/numerator/denominator; по умолчанию нечётная ISO-неделя — numerator.
Совпадающие интервалы допустимы только для разных чётностей. Конец пары должен
быть позже начала в пределах того же дня. В дашборде сохраняется поддержка
старых ночных пар; его расчёт общий с необязательным ботом.

## Обновление и данные

Перед первым запуском новой версии останови процессы записи и сделай копию:

```bash
sqlite3 db.sqlite3 ".backup 'db.before-0.2.sqlite3'"
```

Используй новое имя копии, если она уже существует. Проверь, что копия открывается.
Не заменяй файл рабочей БД во время работы сервера.
Миграция аддитивная и повторяемая: добавляет app_accounts/app_sessions/auth_rate_limits,
а также отсутствующие старые настройки, не удаляя users/tasks/schedules.
Новые аккаунты независимы от данных бота; перенос по одному введённому Telegram ID
намеренно не разрешён.

## Проверки и эксплуатация

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -c 'import sys; import backend.main; assert "aiogram" not in sys.modules'
```

Тесты используют in-memory SQLite и mocks, не отправляют сообщений и не работают
с твоей базой. Android-тесты и сборка описаны в `android/README.md`.
Перед публичным размещением нужны HTTPS reverse proxy, резервные копии, постоянный
диск, ограничения размера запросов и мониторинг. Данный коммит не развёртывает VPS.
Для reverse proxy ограничь доступ к Uvicorn и корректно настрой доверенные proxy IP;
не доверяй произвольным X-Forwarded-For. CORS для native Android не требуется.

Документация используемых платформ:
[scrypt](https://docs.python.org/3/library/hashlib.html#hashlib.scrypt),
[Android alarms](https://developer.android.com/develop/background-work/services/alarms),
[Android notification permissions](https://developer.android.com/develop/ui/compose/notifications/notification-permission),
[WorkManager](https://developer.android.com/jetpack/androidx/releases/work).
