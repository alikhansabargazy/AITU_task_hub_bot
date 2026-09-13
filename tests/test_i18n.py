import unittest
from contextvars import Context

from services.i18n import main_keyboard, reset_language, set_language, tr


class DefaultLanguageTests(unittest.TestCase):
    def test_new_context_defaults_to_english(self):
        context = Context()
        self.assertEqual(context.run(tr, "📅 Расписание"), "📅 Schedule")
        keyboard = context.run(main_keyboard)
        self.assertEqual(keyboard.keyboard[0][0].text, "🏠 Dashboard")

    def test_unsupported_language_falls_back_to_english(self):
        for code in (None, "", "de"):
            with self.subTest(code=code):
                token = set_language(code)
                try:
                    self.assertEqual(tr("📅 Расписание"), "📅 Schedule")
                finally:
                    reset_language(token)

    def test_explicit_language_still_wins(self):
        for code, expected in (
            ("ru", "📅 Расписание"),
            ("en", "📅 Schedule"),
            ("kk", "📅 Сабақ кестесі"),
        ):
            with self.subTest(code=code):
                token = set_language(code)
                try:
                    self.assertEqual(tr("📅 Расписание"), expected)
                finally:
                    reset_language(token)
