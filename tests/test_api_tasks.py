"""API tests use an isolated in-memory SQLite database."""

import unittest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.main import app
from database import db_requests as db
from database import models


class TaskApiTests(unittest.IsolatedAsyncioTestCase):
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

        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )
        self.addAsyncCleanup(self.client.aclose)

    async def test_health(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    async def test_task_crud_and_user_isolation(self):
        created = await self.client.post(
            "/api/v1/users/1/tasks",
            json={
                "text": " Psychology presentation ",
                "subject_name": "Psychology",
                "deadline": "2026-09-20T18:00:00",
                "priority": "high",
            },
        )
        self.assertEqual(created.status_code, 201)
        task = created.json()
        self.assertEqual(task["text"], "Psychology presentation")
        self.assertFalse(task["is_completed"])

        listed = await self.client.get("/api/v1/users/1/tasks?completed=false")
        self.assertEqual([item["id"] for item in listed.json()], [task["id"]])

        updated = await self.client.patch(
            f"/api/v1/users/1/tasks/{task['id']}",
            json={"is_completed": True},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertTrue(updated.json()["is_completed"])

        foreign = await self.client.get(f"/api/v1/users/2/tasks/{task['id']}")
        self.assertEqual(foreign.status_code, 404)

        deleted = await self.client.delete(f"/api/v1/users/1/tasks/{task['id']}")
        self.assertEqual(deleted.status_code, 204)
        missing = await self.client.get(f"/api/v1/users/1/tasks/{task['id']}")
        self.assertEqual(missing.status_code, 404)

    async def test_rejects_aware_deadline_and_empty_patch(self):
        aware = await self.client.post(
            "/api/v1/users/1/tasks",
            json={"text": "Task", "deadline": "2026-09-20T18:00:00Z"},
        )
        self.assertEqual(aware.status_code, 422)

        created = await self.client.post(
            "/api/v1/users/1/tasks", json={"text": "Task"}
        )
        empty = await self.client.patch(
            f"/api/v1/users/1/tasks/{created.json()['id']}", json={}
        )
        self.assertEqual(empty.status_code, 422)
