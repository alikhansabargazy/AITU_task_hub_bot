from datetime import datetime, time
from sqlalchemy import BigInteger, ForeignKey, String, Integer, Time, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker

# Базовый класс для всех таблиц
class Base(AsyncAttrs, DeclarativeBase):
    pass

# 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
class User(Base):
    __tablename__ = 'users'
    
    # user_id берем прямо из Telegram, поэтому используем BigInteger
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timezone: Mapped[str] = mapped_column(String(50), default='UTC') # Часовой пояс
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow) # Дата регистрации
    
    # Связи для удобного получения данных (Один ко Многим)
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="user")
    tasks: Mapped[list["Task"]] = relationship(back_populates="user")


# 2. ТАБЛИЦА РАСПИСАНИЯ
class Schedule(Base):
    __tablename__ = 'schedules'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    
    subject: Mapped[str] = mapped_column(String(100)) # Например: "Высшая математика"
    day_of_week: Mapped[int] = mapped_column(Integer) # 1 - Пн, 2 - Вт ... 7 - Вс
    parity: Mapped[str] = mapped_column(String(20), default='all') # 'all', 'numerator' (числитель), 'denominator' (знаменатель)
    
    start_time: Mapped[time] = mapped_column(Time) # Время начала пары
    end_time: Mapped[time] = mapped_column(Time) # Время окончания пары
    
    lesson_type: Mapped[str] = mapped_column(String(50), nullable=True) # Лекция, Практика, Лаба
    location: Mapped[str] = mapped_column(String(100), nullable=True) # Аудитория, корпус или ссылка
    teacher: Mapped[str] = mapped_column(String(100), nullable=True) # ФИО преподавателя
    
    user: Mapped["User"] = relationship(back_populates="schedules")


# 3. ТАБЛИЦА ЗАДАЧ / ДЕДЛАЙНОВ
class Task(Base):
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    
    text: Mapped[str] = mapped_column(String(255)) # Суть задачи (Сдать отчет, подготовить презентацию)
    subject_name: Mapped[str] = mapped_column(String(100), nullable=True) # Привязка к предмету (необязательно)
    
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True) # До какого числа и времени нужно сделать
    priority: Mapped[str] = mapped_column(String(20), default='normal') # 'high' (горит), 'normal' (обычно)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False) # Выполнена или нет
    
    user: Mapped["User"] = relationship(back_populates="tasks")


# --- НАСТРОЙКА ПОДКЛЮЧЕНИЯ К БД ---

# Создаем асинхронный "движок" базы данных (создаст файл db.sqlite3)
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo=False)

# Создаем фабрику сессий (через них мы будем добавлять и искать данные)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Функция для создания всех таблиц при запуске бота
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)