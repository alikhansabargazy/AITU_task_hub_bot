from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    subject_name: str | None = Field(default=None, min_length=1, max_length=100)
    deadline: datetime | None = None
    priority: Literal["normal", "high"] = "normal"


class TaskUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=255)
    subject_name: str | None = Field(default=None, min_length=1, max_length=100)
    deadline: datetime | None = None
    priority: Literal["normal", "high"] | None = None
    is_completed: bool | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    text: str
    subject_name: str | None
    deadline: datetime | None
    priority: Literal["normal", "high"]
    is_completed: bool
