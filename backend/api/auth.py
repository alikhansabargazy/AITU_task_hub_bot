import asyncio
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from backend.auth import Account, DUMMY_HASH, bearer, hash_password, issue_session, rate_limit, token_hash, verify_password
from backend.schemas import Credentials, PasswordChange, RegisterRequest, SessionResponse
from database import models

router = APIRouter(prefix="/auth", tags=["accounts"])


@router.post("/register", response_model=SessionResponse, status_code=201)
async def register(payload: RegisterRequest, request: Request):
    await rate_limit(request, payload.username)
    password_hash = await asyncio.to_thread(hash_password, payload.password.get_secret_value())
    # Separate namespace: cannot impersonate or overwrite a legacy Telegram user.
    user_id = -(secrets.randbelow(2**52 - 1) + 1)
    async with models.async_session() as session:
        session.add(models.User(user_id=user_id, language=payload.language))
        await session.flush()
        session.add(models.AppAccount(
            user_id=user_id, username=payload.username,
            display_name=payload.display_name or payload.username, password_hash=password_hash,
        ))
        try:
            await session.flush()
            result = await issue_session(session, user_id)
            await session.commit()
        except IntegrityError as error:
            await session.rollback()
            raise HTTPException(409, "Username already taken") from error
    return result


@router.post("/login", response_model=SessionResponse)
async def login(payload: Credentials, request: Request):
    await rate_limit(request, payload.username)
    async with models.async_session() as session:
        account = await session.scalar(select(models.AppAccount).where(models.AppAccount.username == payload.username))
        valid = await asyncio.to_thread(
            verify_password, payload.password.get_secret_value(), account.password_hash if account else DUMMY_HASH,
        )
        if not account or not valid:
            raise HTTPException(401, "Invalid username or password")
        # Serialize issuance with password rotation; an old password must not
        # create a new session after a concurrent rotation revokes old sessions.
        unchanged = await session.execute(update(models.AppAccount).where(
            models.AppAccount.user_id == account.user_id,
            models.AppAccount.password_hash == account.password_hash,
        ).values(password_hash=account.password_hash))
        if unchanged.rowcount != 1:
            raise HTTPException(401, "Invalid username or password")
        result = await issue_session(session, account.user_id)
        await session.commit()
        return result


@router.post("/logout", status_code=204)
async def logout(account: Account, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
    async with models.async_session() as session:
        await session.execute(delete(models.AppSession).where(
            models.AppSession.user_id == account.user_id,
            models.AppSession.token_hash == token_hash(credentials.credentials),
        ))
        await session.commit()
    return Response(status_code=204)


@router.patch("/password", response_model=SessionResponse)
async def change_password(payload: PasswordChange, account: Account, request: Request):
    await rate_limit(request, account.username)
    if not await asyncio.to_thread(verify_password, payload.current_password.get_secret_value(), account.password_hash):
        raise HTTPException(401, "Invalid current password")
    hashed = await asyncio.to_thread(hash_password, payload.new_password.get_secret_value())
    async with models.async_session() as session:
        # Compare the old hash in the UPDATE: concurrent password changes cannot win twice.
        changed = await session.execute(update(models.AppAccount).where(
            models.AppAccount.user_id == account.user_id,
            models.AppAccount.password_hash == account.password_hash,
        ).values(password_hash=hashed))
        if changed.rowcount != 1:
            raise HTTPException(409, "Password changed. Sign in again.")
        await session.execute(delete(models.AppSession).where(models.AppSession.user_id == account.user_id))
        result = await issue_session(session, account.user_id)
        await session.commit()
        return result
