from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from backend.schemas import TaskCreate, TaskResponse, TaskUpdate
from database import db_requests as db


router = APIRouter(prefix="/users/{user_id}/tasks", tags=["tasks"])
UserId = Annotated[int, Path(gt=0)]


def invalid_request(error: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(error),
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    user_id: UserId,
    completed: bool | None = Query(default=None),
):
    return await db.get_tasks(user_id, completed=completed)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(user_id: UserId, payload: TaskCreate):
    try:
        return await db.add_task(user_id, **payload.model_dump())
    except ValueError as error:
        raise invalid_request(error) from error


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(user_id: UserId, task_id: Annotated[int, Path(gt=0)]):
    task = await db.get_task(user_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    user_id: UserId,
    task_id: Annotated[int, Path(gt=0)],
    payload: TaskUpdate,
):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one field is required",
        )
    try:
        updated = await db.update_task(user_id, task_id, **fields)
    except ValueError as error:
        raise invalid_request(error) from error
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return await db.get_task(user_id, task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(user_id: UserId, task_id: Annotated[int, Path(gt=0)]):
    if not await db.delete_task(user_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
