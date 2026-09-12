from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Almaty")
    language: Mapped[str] = mapped_column(String(2), default="ru")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=15)
    week_parity_offset: Mapped[int] = mapped_column(Integer, default=0)
    dashboard_days: Mapped[int] = mapped_column(Integer, default=7)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="user")
    tasks: Mapped[list["Task"]] = relationship(back_populates="user")


class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    subject: Mapped[str] = mapped_column(String(100))
    day_of_week: Mapped[int] = mapped_column(Integer)
    parity: Mapped[str] = mapped_column(String(20), default="all")
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    lesson_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    teacher: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user: Mapped["User"] = relationship(back_populates="schedules")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    text: Mapped[str] = mapped_column(String(255))
    subject_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped["User"] = relationship(back_populates="tasks")


engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3", echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Additive, repeatable migration: preserve existing users and schedules.
        columns = {
            row[1] for row in await conn.execute(text("PRAGMA table_info(users)"))
        }
        additions = {
            "language": "VARCHAR(2) NOT NULL DEFAULT 'ru'",
            "notifications_enabled": "BOOLEAN NOT NULL DEFAULT 1",
            "reminder_minutes": "INTEGER NOT NULL DEFAULT 15",
            "week_parity_offset": "INTEGER NOT NULL DEFAULT 0",
            "dashboard_days": "INTEGER NOT NULL DEFAULT 7",
        }
        for name, definition in additions.items():
            if name not in columns:
                await conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN {name} {definition}")
                )
