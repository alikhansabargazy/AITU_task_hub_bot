"""Standalone API contract, sessions, ownership, and scheduling regression tests."""

import unittest
from datetime import datetime, time, timedelta, timezone
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.auth import token_hash, utc_now, verify_password
from backend.main import app
from database import db_requests as db
from database import models
from test_database import MemoryDatabase


class FeatureApiTests(MemoryDatabase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        self.addAsyncCleanup(self.client.aclose)
        self.password = "a-strong-test-password"
        self.session = await self.register("alikhan")
        self.headers = {"Authorization": "Bearer " + self.session["access_token"]}
        self.client.headers.update(self.headers)
        self.user = (await self.client.get("/api/v1/me")).json()

    async def register(self, username):
        response = await self.client.post("/api/v1/auth/register", json={
            "username": username, "password": self.password, "display_name": "Alikhan",
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    async def lesson(self, **changes):
        body = dict(subject="Math", day_of_week=1, start_time="09:00", end_time="09:50", parity="all", teacher="Ada", location="C1")
        body.update(changes)
        return await self.client.post("/api/v1/me/schedule", json=body)

    async def test_account_hashing_login_logout_and_no_legacy_access(self):
        self.assertLess(self.user["user_id"], 0)
        async with models.async_session() as session:
            account = await session.get(models.AppAccount, self.user["user_id"])
            self.assertNotEqual(account.password_hash, self.password)
            self.assertTrue(verify_password(self.password, account.password_hash))
            saved = await session.get(models.AppSession, token_hash(self.session["access_token"]))
            self.assertIsNotNone(saved)
        self.assertNotIn("password", str(self.user))
        login = await self.client.post("/api/v1/auth/login", json={"username": " ALIKHAN ", "password": self.password})
        self.assertEqual(login.status_code, 200)
        failed = await self.client.post("/api/v1/auth/login", json={"username": "alikhan", "password": "incorrect-password"})
        unknown = await self.client.post("/api/v1/auth/login", json={"username": "unknown", "password": "incorrect-password"})
        self.assertEqual((failed.status_code, failed.json()), (unknown.status_code, unknown.json()))
        legacy = await self.client.get("/api/v1/users/1/tasks")
        self.assertEqual(legacy.status_code, 404)
        await self.client.post("/api/v1/auth/logout")
        self.assertEqual((await self.client.get("/api/v1/me")).status_code, 401)
        other_session = await self.client.get("/api/v1/me", headers={"Authorization": "Bearer " + login.json()["access_token"]})
        self.assertEqual(other_session.status_code, 200)

    async def test_no_public_profile_tasks_settings_or_schedule(self):
        for endpoint in ("me", "me/tasks", "me/schedule", "me/settings", "me/dashboard"):
            response = await self.client.get("/api/v1/" + endpoint, headers={"Authorization": "Bearer made-up-token"})
            self.assertEqual(response.status_code, 401, endpoint)
        duplicate = await self.client.post("/api/v1/auth/register", json={"username": "Alikhan", "password": self.password})
        self.assertEqual(duplicate.status_code, 409)

    async def test_password_validation_never_reflects_secret(self):
        response = await self.client.post("/api/v1/auth/register", json={"username": "new_user", "password": "secret!"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("secret!", response.text)

    async def test_password_change_revokes_existing_sessions(self):
        second = await self.client.post("/api/v1/auth/login", json={"username": "alikhan", "password": self.password})
        changed = await self.client.patch("/api/v1/auth/password", json={"current_password": self.password, "new_password": "a-new-strong-password"})
        self.assertEqual(changed.status_code, 200, changed.text)
        for raw in (self.session["access_token"], second.json()["access_token"]):
            self.assertEqual((await self.client.get("/api/v1/me", headers={"Authorization": "Bearer " + raw})).status_code, 401)
        good = await self.client.get("/api/v1/me", headers={"Authorization": "Bearer " + changed.json()["access_token"]})
        self.assertEqual(good.status_code, 200)
        self.assertEqual((await self.client.post("/api/v1/auth/login", json={"username": "alikhan", "password": self.password})).status_code, 401)

    async def test_expired_session_is_rejected(self):
        async with models.async_session() as session:
            item = await session.get(models.AppSession, token_hash(self.session["access_token"]))
            item.expires_at = utc_now() - timedelta(seconds=1)
            await session.commit()
        self.assertEqual((await self.client.get("/api/v1/me/tasks")).status_code, 401)

    async def test_login_rate_limit(self):
        # Keep this test fast while checking the persistent rate-limit boundary.
        with patch("backend.api.auth.verify_password", return_value=False):
            for _ in range(10):
                response = await self.client.post("/api/v1/auth/login", json={"username": "victim", "password": self.password})
                self.assertEqual(response.status_code, 401)
            response = await self.client.post("/api/v1/auth/login", json={"username": "victim", "password": self.password})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "60")

    async def test_schedule_crud_conflicts_parity_and_atomic_rollback(self):
        first = await self.lesson(parity="numerator")
        self.assertEqual(first.status_code, 201, first.text)
        lesson_id = first.json()["id"]
        self.assertEqual((await self.lesson(parity="numerator")).status_code, 422)
        second = await self.lesson(parity="denominator", subject="Physics")
        self.assertEqual(second.status_code, 201)
        overlap = await self.client.patch(f"/api/v1/me/schedule/{lesson_id}", json={"parity": "all", "subject": "Should roll back"})
        self.assertEqual(overlap.status_code, 422)
        original = (await self.client.get(f"/api/v1/me/schedule/{lesson_id}")).json()
        self.assertEqual(original["subject"], "Math")
        cleared = await self.client.patch(f"/api/v1/me/schedule/{lesson_id}", json={"location": None, "teacher": None, "lesson_type": "Lab"})
        self.assertEqual(cleared.status_code, 200)
        self.assertIsNone(cleared.json()["teacher"])
        self.assertEqual((await self.lesson(start_time="09:50", end_time="10:40")).status_code, 201)
        self.assertEqual((await self.lesson(start_time="10:00", end_time="09:00")).status_code, 422)
        self.assertEqual((await self.lesson(start_time="10:00Z", end_time="11:00Z")).status_code, 422)
        self.assertEqual((await self.client.patch(f"/api/v1/me/schedule/{lesson_id}", json={"subject": None})).status_code, 422)
        filtered = await self.client.get("/api/v1/me/schedule?day=1&parity=numerator")
        self.assertNotIn(second.json()["id"], [lesson["id"] for lesson in filtered.json()])
        self.assertEqual((await self.client.get("/api/v1/me/schedule?day=8")).status_code, 422)
        self.assertEqual((await self.client.delete(f"/api/v1/me/schedule/{lesson_id}")).status_code, 204)
        self.assertEqual((await self.client.get(f"/api/v1/me/schedule/{lesson_id}")).status_code, 404)

    async def test_all_mutations_are_scoped_to_the_account(self):
        task = (await self.client.post("/api/v1/me/tasks", json={"text": "Private"})).json()
        lesson = (await self.lesson()).json()
        other = await self.register("second_user")
        headers = {"Authorization": "Bearer " + other["access_token"]}
        for kind, item in (("tasks", task), ("schedule", lesson)):
            endpoint = f"/api/v1/me/{kind}/{item['id']}"
            self.assertEqual((await self.client.get(endpoint, headers=headers)).status_code, 404)
            payload = {"text": "Changed"} if kind == "tasks" else {"subject": "Changed"}
            self.assertEqual((await self.client.patch(endpoint, headers=headers, json=payload)).status_code, 404)
            self.assertEqual((await self.client.delete(endpoint, headers=headers)).status_code, 404)
            self.assertEqual((await self.client.get(endpoint)).status_code, 200)
        await db.add_task(1, "Legacy Telegram task")
        self.assertNotIn("Legacy Telegram task", (await self.client.get("/api/v1/me/tasks")).text)

    async def test_task_edit_clears_optional_fields_and_restores_completed(self):
        task = (await self.client.post("/api/v1/me/tasks", json={"text": "Exam", "subject_name": "Math", "deadline": "2026-10-01T12:00:00", "priority": "high"})).json()
        endpoint = f"/api/v1/me/tasks/{task['id']}"
        await self.client.patch(endpoint, json={"is_completed": True})
        response = await self.client.patch(endpoint, json={"text": "Revised", "subject_name": None, "deadline": None, "priority": "normal", "is_completed": False})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["deadline"])
        self.assertIsNone(response.json()["subject_name"])
        self.assertFalse(response.json()["is_completed"])
        self.assertEqual((await self.client.post("/api/v1/me/tasks", json={"text": "  "})).status_code, 422)
        self.assertEqual((await self.client.patch(endpoint, json={"user_id": 1})).status_code, 422)

    async def test_settings_validation_and_native_users_not_sent_to_telegram(self):
        for body in ({"language": "de"}, {"timezone": "Not/AZone"}, {"reminder_minutes": 4}, {"dashboard_days": 2}, {"notifications_enabled": None}, {}):
            self.assertEqual((await self.client.patch("/api/v1/me/settings", json=body)).status_code, 422, str(body))
        for language in ("ru", "en", "kk"):
            updated = await self.client.patch("/api/v1/me/settings", json={"language": language, "timezone": "UTC", "reminder_minutes": 0, "week_parity_offset": 1, "dashboard_days": 14, "notifications_enabled": True})
            self.assertEqual(updated.status_code, 200, updated.text)
            self.assertEqual(updated.json()["language"], language)
        await self.lesson()
        self.assertEqual(await db.get_notification_data(), [])

    async def test_dashboard_local_time_horizon_and_current_lesson(self):
        await self.client.patch("/api/v1/me/settings", json={"timezone": "UTC", "dashboard_days": 1})
        now = datetime(2026, 9, 21, 9, 20, tzinfo=timezone.utc)
        await self.lesson()
        await self.lesson(start_time="11:00", end_time="11:50", subject="Physics")
        for text, deadline in (("Overdue", "2026-09-21T09:19:00"), ("Today", "2026-09-21T23:59:00"), ("Tomorrow", "2026-09-22T00:00:00"), ("Undated", None)):
            await self.client.post("/api/v1/me/tasks", json={"text": text, "deadline": deadline})
        with patch("services.dashboard.local_now", return_value=now):
            response = await self.client.get("/api/v1/me/dashboard")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["today_count"], 2)
        self.assertEqual(result["current_lessons"][0]["lesson"]["subject"], "Math")
        self.assertEqual(result["next_lesson"]["lesson"]["subject"], "Physics")
        self.assertEqual([item["text"] for item in result["overdue"]], ["Overdue"])
        self.assertEqual([item["text"] for item in result["upcoming"]], ["Today"])
        self.assertEqual(result["later_count"], 1)
        self.assertEqual([item["text"] for item in result["undated"]], ["Undated"])


if __name__ == "__main__":
    unittest.main()
