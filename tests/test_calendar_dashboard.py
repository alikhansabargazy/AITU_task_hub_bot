import unittest
from datetime import date, datetime, time, timezone
from types import SimpleNamespace as NS
from zoneinfo import ZoneInfo

from handlers.dashboard import (
    MAX_MESSAGE_UNITS,
    local_deadline,
    render_dashboard,
    units,
)
from services.calendar import lesson_occurs, local_now, week_parity
from services.i18n import reset_language, set_language


def user(**fields):
    return NS(
        **{
            **dict(
                user_id=1,
                timezone="UTC",
                language="ru",
                dashboard_days=7,
                week_parity_offset=0,
                reminder_minutes=15,
                notifications_enabled=True,
            ),
            **fields,
        }
    )


def lesson(**fields):
    return NS(
        **{
            **dict(
                id=1,
                subject="Не указано",
                day_of_week=1,
                parity="all",
                start_time=time(9),
                end_time=time(10),
                location="Не указан",
                teacher=None,
            ),
            **fields,
        }
    )


def task(**fields):
    return NS(
        **{**dict(id=1, text="Нет.", deadline=None, is_completed=False), **fields}
    )


class CalendarTests(unittest.TestCase):
    def test_local_midnight_and_invalid_zone_fallback(self):
        now = datetime(2026, 1, 4, 19, 5, tzinfo=timezone.utc)
        local = local_now(user(timezone="Asia/Almaty"), now)
        self.assertEqual(
            (local.date(), local.hour, local.minute), (date(2026, 1, 5), 0, 5)
        )
        self.assertEqual(local_now(user(timezone="Invalid/Zone"), now), now)

    def test_iso_year_boundary_and_offset(self):
        for day, parity in (
            (date(2021, 1, 1), "numerator"),
            (date(2021, 1, 4), "numerator"),
            (date(2021, 1, 11), "denominator"),
            (date(2024, 12, 30), "numerator"),
        ):
            with self.subTest(day=day):
                self.assertEqual(week_parity(day), parity)
                self.assertNotEqual(week_parity(day, 1), parity)

    def test_lesson_occurs_weekday_and_both_parities(self):
        monday = date(2026, 1, 5)  # ISO week 2
        for offset in (0, 1):
            for parity in ("all", "numerator", "denominator"):
                with self.subTest(offset=offset, parity=parity):
                    self.assertEqual(
                        lesson_occurs(
                            lesson(parity=parity),
                            monday,
                            user(week_parity_offset=offset),
                        ),
                        parity
                        in ("all", "denominator" if offset == 0 else "numerator"),
                    )
                    self.assertFalse(
                        lesson_occurs(lesson(parity=parity), date(2026, 1, 6), user())
                    )


class DashboardTests(unittest.TestCase):
    def setUp(self):
        token = set_language("ru")
        self.addCleanup(reset_language, token)

    def test_locales_translate_ui_not_user_text(self):
        titles = {"ru": "Дашборд", "en": "Dashboard", "kk": "Басқару панелі"}
        for language, title in titles.items():
            with self.subTest(language=language):
                token = set_language(language)
                try:
                    rendered = render_dashboard(
                        user(language=language),
                        [lesson()],
                        [task(), task(id=2, text="<b>A&B</b>")],
                        now=datetime(2026, 1, 5, 9, 30, tzinfo=timezone.utc),
                    )
                finally:
                    reset_language(token)
                self.assertIn(f"🏠 <b>{title}</b>", rendered)
                self.assertIn("<b>Не указано</b>", rendered)
                self.assertIn("Не указан", rendered)
                self.assertIn("• Нет.", rendered)
                self.assertIn("&lt;b&gt;A&amp;B&lt;/b&gt;", rendered)
                self.assertNotIn("<b>A&B</b>", rendered)

    def test_deadlines_local_naive_and_horizon_boundaries(self):
        now = datetime(2026, 1, 5, 7, tzinfo=timezone.utc)  # local noon
        tasks = [
            task(id=1, text="overdue", deadline=datetime(2026, 1, 5, 11, 59)),
            task(id=2, text="due now", deadline=datetime(2026, 1, 5, 12)),
            task(id=3, text="last minute", deadline=datetime(2026, 1, 5, 23, 59)),
            task(id=4, text="outside", deadline=datetime(2026, 1, 6)),
            task(id=5, text="undated"),
            task(id=6, text="completed", is_completed=True),
        ]
        rendered = render_dashboard(
            user(timezone="Asia/Almaty", dashboard_days=1), [], tasks, now=now
        )
        self.assertIn("Просрочено: 1 · В горизонте: 2 · Без срока: 1", rendered)
        self.assertIn("За горизонтом: 1", rendered)
        self.assertNotIn("completed", rendered)
        self.assertNotIn("outside", rendered)
        self.assertIn("05.01.2026 12:00 — due now", rendered)

    def test_aware_legacy_deadline_conversion(self):
        now = datetime(2026, 1, 5, 12, tzinfo=ZoneInfo("Asia/Almaty"))
        self.assertEqual(
            local_deadline(
                task(deadline=datetime(2026, 1, 5, 7, tzinfo=timezone.utc)), now
            ),
            datetime(2026, 1, 5, 12),
        )
        naive = datetime(2026, 1, 5, 7)
        self.assertEqual(local_deadline(task(deadline=naive), now), naive)
        self.assertIsNone(local_deadline(task(), now))

    def test_legacy_overnight_uses_previous_days_parity(self):
        rendered = render_dashboard(
            user(),
            [
                lesson(
                    day_of_week=7,
                    parity="numerator",
                    subject="Night",
                    start_time=time(23, 30),
                    end_time=time(1),
                )
            ],
            [],
            now=datetime(2026, 1, 5, 0, 15, tzinfo=timezone.utc),
        )
        self.assertIn("Сейчас: 04.01 23:30–05.01 01:00 · <b>Night</b>", rendered)
        self.assertIn("Пар сегодня: 0", rendered)

    def test_current_lesson_end_exclusive_and_parity(self):
        lessons = [
            lesson(subject="Even", parity="denominator"),
            lesson(id=2, subject="Odd", parity="numerator"),
        ]
        for offset, subject in ((0, "Even"), (1, "Odd")):
            with self.subTest(offset=offset):
                rendered = render_dashboard(
                    user(week_parity_offset=offset),
                    lessons,
                    [],
                    now=datetime(2026, 1, 5, 9, tzinfo=timezone.utc),
                )
                self.assertIn(f"Сейчас: 05.01 09:00–10:00 · <b>{subject}</b>", rendered)
        rendered = render_dashboard(
            user(), lessons, [], now=datetime(2026, 1, 5, 10, tzinfo=timezone.utc)
        )
        self.assertIn("Сейчас: пары нет.", rendered)

    def test_large_dashboard_stays_bounded(self):
        rendered = render_dashboard(
            user(),
            [lesson(subject="<&😀" * 100)],
            [task(id=i, text="<&😀" * 255) for i in range(100)],
            now=datetime(2026, 1, 5, 9, tzinfo=timezone.utc),
        )
        self.assertLessEqual(units(rendered), MAX_MESSAGE_UNITS)
        self.assertNotIn("<&", rendered)
        self.assertEqual(rendered.count("<b>"), rendered.count("</b>"))
