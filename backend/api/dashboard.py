from fastapi import APIRouter

from backend.auth import UserId
from backend.schemas import DashboardResponse
from database import db_requests as db
from services.dashboard import build_dashboard

router = APIRouter(prefix="/me/dashboard", tags=["dashboard"])


def occurrence(value):
    if value is None:
        return None
    return dict(start=value[0], end=value[1], lesson=value[2])


@router.get("", response_model=DashboardResponse)
async def dashboard(user_id: UserId):
    user = await db.get_user(user_id)
    data = build_dashboard(user, await db.get_week_schedule(user_id), await db.get_tasks(user_id))
    return dict(
        local_now=data["now"], timezone=user.timezone, iso_week=data["now"].isocalendar().week,
        parity=data["parity"], dashboard_days=user.dashboard_days,
        today_count=data["today_count"], active_count=len(data["active"]), later_count=data["later_count"],
        current_lessons=[occurrence(item) for item in data["current"]],
        next_lesson=occurrence(data["upcoming_lesson"]),
        overdue=[task for _, task in data["overdue"]], upcoming=[task for _, task in data["upcoming"]], undated=data["undated"],
    )
