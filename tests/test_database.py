"""Real async SQLite tests. Never connect to the application's file engine."""

import unittest
from datetime import datetime, time, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database import db_requests as db
from database import models


class MemoryDatabase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:", poolclass=StaticPool
        )
        self.addAsyncCleanup(self.engine.dispose)

        @event.listens_for(self.engine.sync_engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        factory = async_sessionmaker(self.engine, expire_on_commit=False)
        for target, attribute, value in (
            (models, "engine", self.engine),
            (models, "async_session", factory),
            (db, "async_session", factory),
        ):
            patcher = patch.object(target, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        async with self.engine.begin() as connection:
            await connection.run_sync(models.Base.metadata.create_all)

    async def lesson(self, user_id=1, **changes):
        values = dict(
            subject=" Math ", day_of_week=1, start_time=time(9), end_time=time(10)
        )
        values.update(changes)
        return await db.add_lesson(user_id, **values)


class DatabaseTests(MemoryDatabase):
    async def test_user_defaults_and_repeated_registration(self):
        first = await db.add_user(1)
        second = await db.add_user(1)
        self.assertEqual(first.created_at, second.created_at)
        self.assertEqual((second.timezone, second.language), ("Asia/Almaty", "en"))
        self.assertEqual(
            (
                second.notifications_enabled,
                second.reminder_minutes,
                second.week_parity_offset,
                second.dashboard_days,
            ),
            (True, 15, 0, 7),
        )

    async def test_lesson_crud(self):
        lesson = await self.lesson(
            location=" C1 ", teacher=" Ada ", lesson_type="lecture"
        )
        self.assertEqual(
            (lesson.subject, lesson.location, lesson.teacher), ("Math", "C1", "Ada")
        )
        self.assertEqual((await db.get_lesson(1, lesson.id)).lesson_type, "lecture")
        self.assertTrue(
            await db.update_lesson(1, lesson.id, subject="Physics", location=None)
        )
        updated = await db.get_lesson(1, lesson.id)
        self.assertEqual(updated.subject, "Physics")
        self.assertIsNone(updated.location)
        self.assertTrue(await db.delete_lesson(1, lesson.id))
        self.assertIsNone(await db.get_lesson(1, lesson.id))
        self.assertFalse(await db.delete_lesson(1, lesson.id))

    async def test_task_crud_filter_and_order(self):
        undated = await db.add_task(1, " No date ")
        late = await db.add_task(1, "Late", deadline=datetime(2026, 1, 6))
        early = await db.add_task(
            1, "Early", deadline=datetime(2026, 1, 5), priority="high"
        )
        await db.add_task(2, "Other user's task")
        self.assertEqual(
            [t.id for t in await db.get_tasks(1)], [early.id, late.id, undated.id]
        )
        self.assertEqual((await db.get_task(1, undated.id)).text, "No date")
        self.assertTrue(
            await db.update_task(1, early.id, is_completed=True, subject_name="Math")
        )
        self.assertEqual([t.id for t in await db.get_tasks(1, True)], [early.id])
        self.assertEqual(
            [t.id for t in await db.get_tasks(1, False)], [late.id, undated.id]
        )
        self.assertTrue(
            await db.update_task(1, early.id, is_completed=False, deadline=None)
        )
        self.assertIsNone((await db.get_task(1, early.id)).deadline)
        self.assertTrue(await db.delete_task(1, early.id))
        self.assertFalse(await db.delete_task(1, early.id))

    async def test_ownership_guards(self):
        lesson = await self.lesson()
        task = await db.add_task(1, "Private")
        for get, update, delete, item, fields in (
            (
                db.get_lesson,
                db.update_lesson,
                db.delete_lesson,
                lesson,
                {"subject": "stolen"},
            ),
            (db.get_task, db.update_task, db.delete_task, task, {"text": "stolen"}),
        ):
            with self.subTest(model=type(item).__name__):
                self.assertIsNone(await get(2, item.id))
                self.assertFalse(await update(2, item.id, **fields))
                self.assertFalse(await delete(2, item.id))
                self.assertIsNotNone(await get(1, item.id))
                with self.assertRaises(ValueError):
                    await update(1, item.id, id=999)
        self.assertEqual(await db.get_week_schedule(2), [])
        self.assertEqual(await db.get_tasks(2), [])
        self.assertEqual((await db.get_task(1, task.id)).text, "Private")

    async def test_conflicts_parity_adjacency_and_user_isolation(self):
        first = await self.lesson(parity="numerator")
        opposite = await self.lesson(parity="denominator")
        adjacent = await self.lesson(start_time=time(10), end_time=time(11))
        await self.lesson(user_id=2)
        await self.lesson(day_of_week=2)
        for parity in ("all", "numerator", "denominator"):
            with self.subTest(parity=parity), self.assertRaises(ValueError):
                await self.lesson(
                    start_time=time(9, 30), end_time=time(10, 30), parity=parity
                )
        self.assertEqual(
            [x.id for x in await db.get_schedule_by_day(1, 1, "numerator")],
            [first.id, adjacent.id],
        )
        self.assertEqual(
            [x.id for x in await db.get_schedule_by_day(1, 1, "denominator")],
            [opposite.id, adjacent.id],
        )
        with self.assertRaises(ValueError):
            await db.update_lesson(1, opposite.id, parity="all")
        self.assertEqual((await db.get_lesson(1, opposite.id)).parity, "denominator")
        self.assertTrue(await db.update_lesson(1, first.id, teacher="Updated"))

    async def test_invalid_lesson_values_do_not_persist(self):
        for fields in (
            {"start_time": time(10)},
            {"end_time": time(8)},
            {"start_time": "09:00"},
            {"end_time": None},
            {"start_time": time(23), "end_time": time(1)},
            {"day_of_week": 0},
            {"day_of_week": 8},
            {"parity": "odd"},
            {"subject": " "},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                await self.lesson(**fields)
        self.assertEqual(await db.get_week_schedule(1), [])
        lesson = await self.lesson()
        with self.assertRaises(ValueError):
            await db.update_lesson(1, lesson.id, end_time=time(8))
        self.assertEqual((await db.get_lesson(1, lesson.id)).end_time, time(10))

    async def test_invalid_tasks_and_rollback(self):
        for fields in (
            {"deadline": "tomorrow"},
            {"deadline": datetime.now(timezone.utc)},
            {"priority": "urgent"},
            {"text": " "},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                await db.add_task(1, **{"text": "Task", **fields})
        self.assertEqual(await db.get_tasks(1), [])
        task = await db.add_task(1, "Task")
        with self.assertRaises(ValueError):
            await db.update_task(1, task.id, text="Changed", is_completed=1)
        self.assertEqual((await db.get_task(1, task.id)).text, "Task")

    async def test_settings_timezone_preserves_wall_times(self):
        deadline = datetime(2026, 1, 5, 12, 30)
        task = await db.add_task(1, "Task", deadline=deadline)
        lesson = await self.lesson()
        await db.update_user(
            1,
            timezone="Europe/Berlin",
            reminder_minutes=0,
            notifications_enabled=False,
            dashboard_days=14,
            week_parity_offset=1,
        )
        user = await db.get_user(1)
        self.assertEqual(
            (
                user.timezone,
                user.reminder_minutes,
                user.notifications_enabled,
                user.dashboard_days,
                user.week_parity_offset,
            ),
            ("Europe/Berlin", 0, False, 14, 1),
        )
        self.assertEqual((await db.get_task(1, task.id)).deadline, deadline)
        self.assertEqual((await db.get_lesson(1, lesson.id)).start_time, time(9))

    async def test_language_roundtrip(self):
        for language in ("en", "kk", "ru"):
            with self.subTest(language=language):
                await db.update_user(1, language=language)
                self.assertEqual((await db.get_user(1)).language, language)

    async def test_invalid_settings(self):
        await db.get_user(1)
        for fields in (
            {"language": "de"},
            {"timezone": "UTC+5"},
            {"reminder_minutes": 7},
            {"week_parity_offset": 2},
            {"dashboard_days": 0},
            {"notifications_enabled": 1},
            {"unknown": True},
        ):
            with (
                self.subTest(fields=fields),
                self.assertRaises((ValueError, ZoneInfoNotFoundError)),
            ):
                await db.update_user(1, **fields)
        self.assertEqual((await db.get_user(1)).timezone, "Asia/Almaty")

    async def test_notification_query_excludes_disabled_users(self):
        enabled = await self.lesson()
        await self.lesson(user_id=2)
        await db.update_user(2, notifications_enabled=False)
        await db.get_user(3)
        rows = await db.get_notification_data()
        self.assertEqual([(u.user_id, s.id) for u, s in rows], [(1, enabled.id)])


class MigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_users_preserved_and_migration_idempotent(self):
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.addAsyncCleanup(engine.dispose)
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE users (user_id BIGINT PRIMARY KEY, timezone VARCHAR(50) NOT NULL, created_at DATETIME NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO users VALUES (42, 'Europe/Moscow', '2020-01-02 03:04:05')"
                )
            )
            await connection.execute(
                text(
                    "CREATE TABLE schedules (id INTEGER PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(user_id), subject VARCHAR(100) NOT NULL, day_of_week INTEGER NOT NULL, parity VARCHAR(20) NOT NULL, start_time TIME NOT NULL, end_time TIME NOT NULL, lesson_type VARCHAR(50), location VARCHAR(100), teacher VARCHAR(100))"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO schedules VALUES (7, 42, 'Legacy', 1, 'all', '09:00:00', '10:00:00', NULL, 'C1', NULL)"
                )
            )
            await connection.execute(
                text(
                    "CREATE TABLE tasks (id INTEGER PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(user_id), text VARCHAR(255) NOT NULL, subject_name VARCHAR(100), deadline DATETIME, priority VARCHAR(20) NOT NULL, is_completed BOOLEAN NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO tasks VALUES (8, 42, 'Keep me', NULL, '2020-02-01 00:00:00', 'high', 1)"
                )
            )
        with patch.object(models, "engine", engine):
            await models.async_main()
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                user = await session.get(models.User, 42)
                self.assertEqual(
                    (user.timezone, user.created_at),
                    ("Europe/Moscow", datetime(2020, 1, 2, 3, 4, 5)),
                )
                self.assertEqual(
                    (
                        user.language,
                        user.notifications_enabled,
                        user.reminder_minutes,
                        user.week_parity_offset,
                        user.dashboard_days,
                    ),
                    ("en", True, 15, 0, 7),
                )
                lesson = await session.get(models.Schedule, 7)
                task = await session.get(models.Task, 8)
                self.assertEqual(
                    (
                        lesson.user_id,
                        lesson.subject,
                        lesson.start_time,
                        lesson.location,
                    ),
                    (42, "Legacy", time(9), "C1"),
                )
                self.assertEqual(
                    (
                        task.user_id,
                        task.text,
                        task.deadline,
                        task.priority,
                        task.is_completed,
                    ),
                    (42, "Keep me", datetime(2020, 2, 1), "high", True),
                )
                user.language = "kk"
                user.reminder_minutes = 30
                await session.commit()

            async def snapshot():
                async with engine.connect() as connection:
                    return {
                        table: (
                            await connection.execute(text(f"SELECT * FROM {table}"))
                        ).all()
                        for table in ("users", "schedules", "tasks")
                    }

            before = await snapshot()
            await models.async_main()
            await models.async_main()
            self.assertEqual(await snapshot(), before)
            async with engine.connect() as connection:
                columns = (
                    await connection.execute(text("PRAGMA table_info(users)"))
                ).all()
                names = [row[1] for row in columns]
                self.assertEqual(len(names), len(set(names)))
                self.assertIn("language", names)
