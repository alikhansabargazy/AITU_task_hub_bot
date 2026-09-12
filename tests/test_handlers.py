import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch

from aiogram.types import Message

from handlers import dashboard, schedule, settings, tasks
from services.i18n import reset_language, set_language


def message():
    result = Mock(spec=Message)
    result.message_id = 10
    result.chat = NS(id=1)
    result.from_user = NS(id=1)
    result.answer = AsyncMock()
    result.edit_text = AsyncMock()
    return result


def callback(data):
    return NS(data=data, message=message(), from_user=NS(id=1), answer=AsyncMock())


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        token = set_language("ru")
        self.addCleanup(reset_language, token)
        self.state = AsyncMock()
        self.state.get_state.return_value = None

    async def test_dashboard_rejects_foreign_owner_without_clearing_draft(self):
        event = callback("dashboard:refresh:2")
        with patch.object(dashboard, "show_dashboard", new_callable=AsyncMock) as show:
            await dashboard.dashboard_refresh(event, self.state)
        show.assert_not_awaited()
        self.state.clear.assert_not_awaited()
        self.assertTrue(event.answer.await_args.kwargs["show_alert"])

    async def test_dashboard_refresh_preserves_draft(self):
        event = callback("dashboard:refresh:1")
        with patch.object(dashboard, "show_dashboard", new_callable=AsyncMock) as show:
            await dashboard.dashboard_refresh(event, self.state)
        show.assert_awaited_once_with(event.message, 1, edit=True)
        self.state.clear.assert_not_awaited()

    async def test_settings_guard_owner_token_message_and_chat(self):
        valid = dict(
            settings_token="token",
            settings_owner=1,
            settings_message=10,
            settings_chat=1,
        )
        for change in (
            {"settings_owner": 2},
            {"settings_token": "old"},
            {"settings_message": 9},
            {"settings_chat": 2},
        ):
            with self.subTest(change=change):
                self.state.get_data.return_value = {**valid, **change}
                event = callback("settings:token:toggle")
                with patch.object(
                    settings.db, "update_user", new_callable=AsyncMock
                ) as update:
                    await settings.settings_callback(event, self.state)
                update.assert_not_awaited()
                self.assertTrue(event.answer.await_args.kwargs["show_alert"])
        self.state.clear.assert_not_awaited()

    async def test_language_selection_updates_context_and_keyboard(self):
        self.state.get_data.return_value = dict(
            settings_token="token",
            settings_owner=1,
            settings_message=10,
            settings_chat=1,
        )
        for language, notice, button in (
            ("en", "Language", "🏠 Dashboard"),
            ("kk", "Тіл", "🏠 Шолу"),
        ):
            with self.subTest(language=language):
                event = callback(f"settings:token:language:{language}")
                profile = NS(language=language)
                with (
                    patch.object(
                        settings.db,
                        "update_user",
                        new_callable=AsyncMock,
                        return_value=profile,
                    ) as update,
                    patch.object(
                        settings, "overview", new_callable=AsyncMock
                    ) as overview,
                ):
                    await settings.settings_callback(event, self.state)
                update.assert_awaited_once_with(1, language=language)
                overview.assert_awaited_once_with(
                    event.message, self.state, 1, user=profile, edit=True
                )
                self.assertIn(notice, event.message.answer.await_args.args[0])
                keyboard = event.message.answer.await_args.kwargs["reply_markup"]
                self.assertEqual(keyboard.keyboard[0][0].text, button)

    async def test_manual_timezone_valid_invalid_and_stale(self):
        self.state.get_data.return_value = dict(
            settings_owner=1, settings_message=10, settings_chat=1
        )
        for value, message_id, expected in (
            (" Europe/Berlin ", 11, True),
            ("UTC+5", 11, False),
            ("UTC", 9, False),
            (None, 11, False),
        ):
            with self.subTest(value=value, message_id=message_id):
                event = message()
                event.message_id, event.text, event.reply_to_message = (
                    message_id,
                    value,
                    None,
                )
                with (
                    patch.object(
                        settings.db, "update_user", new_callable=AsyncMock
                    ) as update,
                    patch.object(
                        settings, "overview", new_callable=AsyncMock
                    ) as overview,
                ):
                    await settings.timezone_input(event, self.state)
                if expected:
                    update.assert_awaited_once_with(1, timezone="Europe/Berlin")
                    overview.assert_awaited_once()
                else:
                    update.assert_not_awaited()
                    overview.assert_not_awaited()
                    event.answer.assert_awaited_once()

    async def test_stale_crud_buttons_do_not_reach_database(self):
        self.state.get_data.return_value = dict(
            ui_token="current", ui_message=10, ui_chat=1, task_actions=["remove:1"]
        )
        for module, handler, payload in (
            (schedule, schedule.schedule_callback, "schedule:old:yes"),
            (tasks, tasks.task_callback, "task:old:remove:1"),
        ):
            with self.subTest(payload=payload):
                event = callback(payload)
                with (
                    patch.object(module.db, "get_user", new_callable=AsyncMock) as get,
                    patch.object(
                        module.db, "delete_task", new_callable=AsyncMock
                    ) as delete_task,
                    patch.object(
                        module.db, "delete_lesson", new_callable=AsyncMock
                    ) as delete_lesson,
                ):
                    await handler(event, self.state)
                get.assert_not_awaited()
                delete_task.assert_not_awaited()
                delete_lesson.assert_not_awaited()
                event.answer.assert_awaited_once()

    async def test_invalid_deadline_input_does_not_advance_fsm(self):
        self.state.get_state.return_value = tasks.TaskState.create.state
        self.state.get_data.return_value = {"task_field": "deadline"}
        for value in ("31.02.2026 10:00", "05.01.2026 24:00", "tomorrow"):
            with self.subTest(value=value):
                event = message()
                event.text = value
                with patch.object(tasks, "accept", new_callable=AsyncMock) as accept:
                    await tasks.task_input(event, self.state)
                accept.assert_not_awaited()
                event.answer.assert_awaited_once()


class ScheduleValidationTests(unittest.TestCase):
    def test_valid_time_separators(self):
        for separator in ("-", "–", "—"):
            with self.subTest(separator=separator):
                self.assertEqual(
                    schedule.validate("time", f"08:30 {separator} 10:05"),
                    {"start_time": "08:30", "end_time": "10:05"},
                )

    def test_invalid_times(self):
        for value in (
            None,
            "",
            "8:30-10:05",
            "24:00-25:00",
            "08:60-10:00",
            "10:00-10:00",
            "11:00-10:00",
            "23:00-01:00",
            "08:00/10:00",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                schedule.validate("time", value)
