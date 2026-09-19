"""First-party credentials and revocable, hashed opaque sessions. No Telegram API."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.sqlite import insert

from database import models
from services.i18n import reset_language, set_language

SESSION_DAYS = 30
bearer = HTTPBearer(auto_error=False)


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=bytes.fromhex(salt),
        n=32768, r=8, p=3, maxmem=64 * 1024 * 1024,
    ).hex()
    return f"scrypt${salt}${digest}"


# Do the same expensive verification for an unknown username.
DUMMY_HASH = "scrypt$" + "00" * 16 + "$" + "00" * 64


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, _ = stored.split("$")
        return algorithm == "scrypt" and hmac.compare_digest(hash_password(password, salt), stored)
    except (ValueError, TypeError):
        return False


async def rate_limit(request: Request, username: str):
    """Shared SQLite counters, bounded expiry; do not trust forwarded IP headers."""
    window = int(datetime.now(timezone.utc).timestamp()) // 60
    ip = request.client.host if request.client else "unknown"
    blocked = False
    async with models.async_session() as session:
        await session.execute(delete(models.AuthRateLimit).where(models.AuthRateLimit.window < window - 1))
        for label, limit in ((f"ip:{ip}", 30), (f"username:{username}", 10)):
            key = token_hash(label)
            await session.execute(
                insert(models.AuthRateLimit).values(key=key, window=window, attempts=0)
                .on_conflict_do_nothing()
            )
            await session.execute(
                update(models.AuthRateLimit).where(
                    models.AuthRateLimit.key == key, models.AuthRateLimit.window != window,
                ).values(window=window, attempts=0)
            )
            count = await session.scalar(
                update(models.AuthRateLimit).where(models.AuthRateLimit.key == key)
                .values(attempts=models.AuthRateLimit.attempts + 1)
                .returning(models.AuthRateLimit.attempts)
            )
            blocked |= count > limit
        await session.commit()
    if blocked:
        raise HTTPException(429, "Too many attempts. Try again in a minute.", headers={"Retry-After": "60"})


async def issue_session(session, user_id: int):
    raw = secrets.token_urlsafe(32)
    expires = utc_now() + timedelta(days=SESSION_DAYS)
    await session.execute(delete(models.AppSession).where(models.AppSession.expires_at <= utc_now()))
    session.add(models.AppSession(token_hash=token_hash(raw), user_id=user_id, expires_at=expires))
    return {"access_token": raw, "token_type": "bearer", "expires_at": expires.replace(tzinfo=timezone.utc)}


async def current_account(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or len(credentials.credentials) > 256:
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    async with models.async_session() as session:
        account = await session.scalar(
            select(models.AppAccount).join(models.AppSession, models.AppSession.user_id == models.AppAccount.user_id)
            .where(models.AppSession.token_hash == token_hash(credentials.credentials), models.AppSession.expires_at > utc_now())
        )
    if account is None:
        raise HTTPException(401, "Session expired. Sign in again.", headers={"WWW-Authenticate": "Bearer"})
    return account


Account = Annotated[models.AppAccount, Depends(current_account)]


async def current_user_id(account: Account):
    async with models.async_session() as session:
        user = await session.get(models.User, account.user_id)
    language = set_language(user.language)
    try:
        yield account.user_id
    finally:
        reset_language(language)


UserId = Annotated[int, Depends(current_user_id)]
