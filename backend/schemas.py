from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(InputModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-z0-9_]+$")
    password: SecretStr = Field(min_length=10, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(Credentials):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    language: Literal["ru", "en", "kk"] = "ru"

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Display name must not be blank")
        return value.strip() if value else value


class PasswordChange(InputModel):
    current_password: SecretStr = Field(min_length=10, max_length=128)
    new_password: SecretStr = Field(min_length=10, max_length=128)


class SessionResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_at: datetime


class TaskCreate(InputModel):
    text: str = Field(min_length=1, max_length=255)
    subject_name: str | None = Field(default=None, min_length=1, max_length=100)
    deadline: datetime | None = None
    priority: Literal["normal", "high"] = "normal"


class TaskUpdate(InputModel):
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


class ScheduleCreate(InputModel):
    subject: str = Field(min_length=1, max_length=100)
    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    parity: Literal["all", "numerator", "denominator"] = "all"
    lesson_type: str | None = Field(default=None, min_length=1, max_length=50)
    location: str | None = Field(default=None, min_length=1, max_length=100)
    teacher: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("start_time", "end_time")
    @classmethod
    def local_time(cls, value):
        if value.tzinfo is not None:
            raise ValueError("Use local time without a timezone")
        return value


class ScheduleUpdate(InputModel):
    subject: str | None = Field(default=None, min_length=1, max_length=100)
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    start_time: time | None = None
    end_time: time | None = None
    parity: Literal["all", "numerator", "denominator"] | None = None
    lesson_type: str | None = Field(default=None, min_length=1, max_length=50)
    location: str | None = Field(default=None, min_length=1, max_length=100)
    teacher: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("subject", "day_of_week", "start_time", "end_time", "parity")
    @classmethod
    def non_nullable(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        if isinstance(value, time) and value.tzinfo is not None:
            raise ValueError("Use local time without a timezone")
        return value


class ScheduleResponse(ScheduleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class SettingsUpdate(InputModel):
    timezone: str | None = Field(default=None, min_length=1, max_length=50)
    language: Literal["ru", "en", "kk"] | None = None
    notifications_enabled: bool | None = Field(default=None, strict=True)
    reminder_minutes: Literal[0, 5, 10, 15, 30, 60] | None = None
    week_parity_offset: Literal[0, 1] | None = None
    dashboard_days: Literal[1, 3, 7, 14] | None = None

    @field_validator("*")
    @classmethod
    def no_null(cls, value):
        if value is None:
            raise ValueError("Settings cannot be null")
        return value


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    timezone: str
    language: str
    notifications_enabled: bool
    reminder_minutes: int
    week_parity_offset: int
    dashboard_days: int


class ProfileResponse(SettingsResponse):
    username: str
    display_name: str


class LessonOccurrence(BaseModel):
    start: datetime
    end: datetime
    lesson: ScheduleResponse


class DashboardResponse(BaseModel):
    local_now: datetime
    timezone: str
    iso_week: int
    parity: str
    dashboard_days: int
    today_count: int
    active_count: int
    later_count: int
    current_lessons: list[LessonOccurrence]
    next_lesson: LessonOccurrence | None
    overdue: list[TaskResponse]
    upcoming: list[TaskResponse]
    undated: list[TaskResponse]
