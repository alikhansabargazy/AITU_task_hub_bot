"""Transport-independent dashboard. Deadlines are local wall time, not UTC."""

from datetime import datetime, time, timedelta

from services.calendar import lesson_occurs, local_now, week_parity


def local_deadline(task, now):
    deadline = task.deadline
    if deadline is not None and deadline.tzinfo is not None:
        return deadline.astimezone(now.tzinfo).replace(tzinfo=None)
    return deadline


def build_dashboard(user, lessons, tasks, *, now=None):
    now = local_now(user, now=now)
    today = now.date()
    wall_now = now.replace(tzinfo=None)
    horizon = datetime.combine(today + timedelta(days=user.dashboard_days), time.min)
    occurrences = []
    today_count = 0
    for delta in range(-1, 14):
        day = today + timedelta(days=delta)
        for lesson in lessons:
            if not lesson_occurs(lesson, day, user):
                continue
            today_count += delta == 0
            start = datetime.combine(day, lesson.start_time, tzinfo=now.tzinfo)
            end = datetime.combine(day, lesson.end_time, tzinfo=now.tzinfo)
            if lesson.end_time < lesson.start_time:
                end += timedelta(days=1)
            occurrences.append((start, end, lesson))
    occurrences.sort(key=lambda item: (item[0], item[1], item[2].id))
    active = [task for task in tasks if not task.is_completed]
    overdue, upcoming, undated = [], [], []
    later_count = 0
    for task in active:
        deadline = local_deadline(task, now)
        if deadline is None:
            undated.append(task)
        elif deadline < wall_now:
            overdue.append((deadline, task))
        elif deadline < horizon:
            upcoming.append((deadline, task))
        else:
            later_count += 1
    overdue.sort(key=lambda item: (item[0], item[1].id))
    upcoming.sort(key=lambda item: (item[0], item[1].id))
    undated.sort(key=lambda task: task.id)
    return dict(
        now=now, horizon=horizon, parity=week_parity(today, user.week_parity_offset),
        today_count=today_count, active=active, later_count=later_count,
        current=[item for item in occurrences if item[0] <= now < item[1]],
        upcoming_lesson=next((item for item in occurrences if item[0] > now), None),
        overdue=overdue, upcoming=upcoming, undated=undated,
    )
