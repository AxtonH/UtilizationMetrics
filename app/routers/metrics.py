from collections import defaultdict
from datetime import UTC, datetime, date
import re
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
supabase = get_supabase_client(service_mode=True)

EXCLUDED_USERS = {
    "omar.elhasan@prezlab.com",
    "sanad.zaqtan@prezlab.com",
    "saba.dababneh@prezlab.com",
}


class ActiveDaysItem(BaseModel):
    username: str
    display_name: str
    active_days: int


class LastLoginItem(BaseModel):
    username: str
    display_name: str
    last_login_date: date


class LoginSummary(BaseModel):
    distinct_user_count: int
    today_users: list[str]
    active_days: list[ActiveDaysItem]
    last_logins: list[LastLoginItem]


def _handle_response(response):
    data = getattr(response, "data", None)
    if data is None:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unexpected Supabase response")
    return data


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None
    return None


def _format_username(username: str) -> str:
    local_part = username.split("@", 1)[0]
    pieces = [segment for segment in re.split(r"[._-]+", local_part) if segment]
    if not pieces:
        return username
    return " ".join(piece.capitalize() for piece in pieces)


def _fetch_login_events() -> list[dict[str, Any]]:
    query = supabase.table("login_events").select("username, login_timestamp")
    for excluded in EXCLUDED_USERS:
        query = query.neq("username", excluded)
    return _handle_response(query.execute())


@router.get("/login-summary", response_model=LoginSummary)
def login_summary():
    events = _fetch_login_events()
    active_days: dict[str, set[date]] = defaultdict(set)
    last_login: dict[str, datetime] = {}
    today_users: set[str] = set()
    display_name_map: dict[str, str] = {}
    today = datetime.now(tz=UTC).date()

    for entry in events:
        username = entry.get("username")
        timestamp = _parse_timestamp(entry.get("login_timestamp"))
        if not username or not timestamp:
            continue
        display_name_map.setdefault(username, _format_username(username))
        day = timestamp.date()
        active_days[username].add(day)
        if timestamp > last_login.get(username, datetime.min.replace(tzinfo=UTC)):
            last_login[username] = timestamp
        if day == today:
            today_users.add(username)

    active_days_list = [
        ActiveDaysItem(
            username=user,
            display_name=display_name_map.get(user, user),
            active_days=len(days),
        )
        for user, days in active_days.items()
    ]
    active_days_list.sort(key=lambda item: item.active_days, reverse=True)

    last_login_list = [
        LastLoginItem(
            username=user,
            display_name=display_name_map.get(user, user),
            last_login_date=stamp.date(),
        )
        for user, stamp in last_login.items()
    ]
    last_login_list.sort(key=lambda item: item.last_login_date, reverse=True)

    today_users_display = sorted(display_name_map.get(user, user) for user in today_users)

    summary = LoginSummary(
        distinct_user_count=len(active_days),
        today_users=today_users_display,
        active_days=active_days_list,
        last_logins=last_login_list,
    )
    return summary
