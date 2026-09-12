import unittest
from datetime import datetime, time, timezone
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

from services import scheduler
from services.i18n import reset_language, set_language, tr


def profile(**fields):
    return NS(
        **{
            **dict(
                user_id=1,
                timezone="Asia/Almaty",
                language="ru",
                reminder_minutes=15,
                week_parity_offset=0,
            ),
            **fields,
        }
    )


def lesson(**fields):
    return NS(
        **{
            **dict(
                subject="Не указано <&>",
                location="Не указан <&>",
                teacher="Teacher <&>",
                day_of_week=1,
                parity="denominator",
                start_time=time(0, 5),
                end_time=time(1),
            ),
            **fields,
        }
    )


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = NS(send_message=AsyncMock())
        clock_patch = patch.object(scheduler, "datetime", wraps=datetime)
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.clock.now.return_value = datetime(
            2026, 1, 4, 18, 50, 37, tzinfo=timezone.utc
        )
        data_patch = patch.object(
            scheduler, "get_notification_data", new_callable=AsyncMock
        )
        self.data = data_patch.start()
        self.addCleanup(data_patch.stop)
        token = set_language("ru")
        self.addCleanup(reset_language, token)

    async def test_midnight_target_parity_and_html_escaping(self):
        self.data.return_value = [(profile(), lesson())]
        await scheduler.check_upcoming_lessons(self.bot)
        self.data.assert_awaited_once_with()
        self.bot.send_message.assert_awaited_once()
        args, kwargs = self.bot.send_message.await_args
        self.assertEqual(args[0], 1)
        self.assertIn("00:05–01:00", args[1])
        self.assertIn("Не указано &lt;&amp;&gt;", args[1])
        self.assertIn("Teacher &lt;&amp;&gt;", args[1])
        self.assertEqual(kwargs["parse_mode"], "HTML")

    async def test_nonmatching_day_time_and_parity_do_not_send(self):
        self.data.return_value = [
            (profile(), lesson(day_of_week=7)),
            (profile(), lesson(parity="numerator")),
            (profile(), lesson(start_time=time(0, 6))),
        ]
        await scheduler.check_upcoming_lessons(self.bot)
        self.bot.send_message.assert_not_awaited()

    async def test_offset_reverses_target_parity(self):
        self.data.return_value = [
            (profile(week_parity_offset=1), lesson(parity="numerator"))
        ]
        await scheduler.check_upcoming_lessons(self.bot)
        self.bot.send_message.assert_awaited_once()

    async def test_zero_reminder_sends_at_start(self):
        self.clock.now.return_value = datetime(
            2026, 1, 4, 19, 5, 59, tzinfo=timezone.utc
        )
        self.data.return_value = [(profile(reminder_minutes=0), lesson())]
        await scheduler.check_upcoming_lessons(self.bot)
        self.bot.send_message.assert_awaited_once()
        self.assertIn("начинается сейчас", self.bot.send_message.await_args.args[1])

    async def test_localization_per_recipient_and_context_restored(self):
        self.data.return_value = [
            (profile(user_id=i, language=language), lesson())
            for i, language in enumerate(("en", "kk", "ru"), 1)
        ]
        await scheduler.check_upcoming_lessons(self.bot)
        self.assertEqual(self.bot.send_message.await_count, 3)
        for call, title in zip(
            self.bot.send_message.await_args_list, ("Class", "Сабақ", "Пара")
        ):
            with self.subTest(title=title):
                self.assertIn(f"<b>{title} ", call.args[1])
                self.assertIn("Не указано &lt;&amp;&gt;", call.args[1])
                self.assertIn("Не указан &lt;&amp;&gt;", call.args[1])
        self.assertEqual(tr("начинается сейчас"), "начинается сейчас")

    async def test_send_failure_does_not_block_next_user(self):
        self.data.return_value = [
            (profile(user_id=1), lesson()),
            (profile(user_id=2), lesson()),
        ]
        self.bot.send_message.side_effect = [RuntimeError("Telegram unavailable"), None]
        with self.assertLogs(scheduler.logger, level="ERROR"):
            await scheduler.check_upcoming_lessons(self.bot)
        self.assertEqual(
            [c.args[0] for c in self.bot.send_message.await_args_list], [1, 2]
        )

    async def test_empty_notification_data(self):
        self.data.return_value = []
        await scheduler.check_upcoming_lessons(self.bot)
        self.bot.send_message.assert_not_awaited()

    async def test_scheduler_configuration_without_starting_real_scheduler(self):
        with patch.object(scheduler, "AsyncIOScheduler") as factory:
            result = scheduler.setup_scheduler(self.bot)
        factory.assert_called_once_with(timezone="UTC")
        self.assertIs(result, factory.return_value)
        result.start.assert_called_once_with()
        result.add_job.assert_called_once_with(
            scheduler.check_upcoming_lessons,
            "cron",
            second=0,
            args=[self.bot],
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )
