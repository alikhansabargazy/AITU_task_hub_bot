from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Response

from backend.auth import UserId
from backend.api.tasks import invalid_request
from backend.schemas import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from database import db_requests as db

router = APIRouter(prefix="/me/schedule", tags=["schedule"])
LessonId = Annotated[int, Path(gt=0)]


@router.get("", response_model=list[ScheduleResponse])
async def list_schedule(user_id: UserId, day: int | None = Query(None, ge=1, le=7), parity: Literal["all", "numerator", "denominator"] | None = None):
    lessons = await db.get_week_schedule(user_id)
    return [item for item in lessons if (day is None or item.day_of_week == day)
            and (parity is None or item.parity in ("all", parity))]


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_lesson(user_id: UserId, payload: ScheduleCreate):
    try:
        return await db.add_lesson(user_id, **payload.model_dump())
    except ValueError as error:
        raise invalid_request(error) from error


@router.get("/{lesson_id}", response_model=ScheduleResponse)
async def get_lesson(user_id: UserId, lesson_id: LessonId):
    lesson = await db.get_lesson(user_id, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Class not found")
    return lesson


@router.patch("/{lesson_id}", response_model=ScheduleResponse)
async def update_lesson(user_id: UserId, lesson_id: LessonId, payload: ScheduleUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "At least one field is required")
    try:
        updated = await db.update_lesson(user_id, lesson_id, **fields)
    except ValueError as error:
        raise invalid_request(error) from error
    if not updated:
        raise HTTPException(404, "Class not found")
    return await db.get_lesson(user_id, lesson_id)


@router.delete("/{lesson_id}", status_code=204)
async def delete_lesson(user_id: UserId, lesson_id: LessonId):
    if not await db.delete_lesson(user_id, lesson_id):
        raise HTTPException(404, "Class not found")
    return Response(status_code=204)
