from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException

from backend.auth import Account, UserId
from backend.schemas import ProfileResponse, SettingsResponse, SettingsUpdate
from database import db_requests as db

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def profile(account: Account):
    user = await db.get_user(account.user_id)
    return {**SettingsResponse.model_validate(user).model_dump(),
            "username": account.username, "display_name": account.display_name}


@router.get("/settings", response_model=SettingsResponse)
async def settings(user_id: UserId):
    return await db.get_user(user_id)


@router.patch("/settings", response_model=SettingsResponse)
async def update_settings(user_id: UserId, payload: SettingsUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "At least one setting is required")
    try:
        return await db.update_user(user_id, **fields)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise HTTPException(422, str(error)) from error
