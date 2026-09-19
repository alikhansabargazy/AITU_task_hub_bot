import os
from datetime import datetime, time
from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    event,
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
    language: Mapped[str] = mapped_column(String(2), default="en")
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


class AppAccount(Base):
    """Standalone accounts use negative IDs; Telegram IDs remain untouched."""

    __tablename__ = "app_accounts"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))


class AppSession(Base):
    __tablename__ = "app_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_accounts.user_id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{PROJECT_ROOT / 'db.sqlite3'}")
engine = create_async_engine(url=DATABASE_URL, echo=False)


@event.listens_for(engine.sync_engine, "connect")
def configure_sqlite(connection, _):
    if engine.dialect.name == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


async_session = async_sessionmaker(engine, expire_on_commit=False)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Additive, repeatable migration: preserve existing users and schedules.
        columns = {
            row[1] for row in await conn.execute(text("PRAGMA table_info(users)"))
        }
        additions = {
            "language": "VARCHAR(2) NOT NULL DEFAULT 'en'",
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
