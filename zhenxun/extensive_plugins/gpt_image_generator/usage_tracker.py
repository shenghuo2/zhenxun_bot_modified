"""
用量追踪
- 每人每天限制 N 次 (仅普通用户, 按天清零)
- 按用户累计计费 (不按天清零)
- 按群组累计计费 (不按天清零, 不含 superuser)
- superuser 单独累计计费 (不加入群组统计)
- 数据持久化到 JSON 文件
"""

import json
from datetime import date
from pathlib import Path

from .config import DAILY_LIMIT

DATA_FILE = Path(__file__).parent / "usage_data.json"


def _load_data() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "users": {},       # 普通用户: {total_count, total_cost, daily_count, last_date}
        "groups": {},       # 群组累计: {total_count, total_cost}
        "superusers": {},   # superuser 单独累计: {total_count, total_cost}
    }


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_today() -> str:
    return date.today().isoformat()


def check_user_limit(user_id: str) -> tuple[bool, int]:
    """
    检查普通用户是否超过每日限制 (superuser 不走此函数)

    Returns:
        tuple[bool, int]: (是否可以使用, 今日已使用次数)
    """
    data = _load_data()
    today = _get_today()

    user_data = data.get("users", {}).get(user_id, {})
    last_date = user_data.get("last_date", "")
    daily_count = user_data.get("daily_count", 0)

    if last_date != today:
        daily_count = 0

    can_use = daily_count < DAILY_LIMIT
    return can_use, daily_count


def record_usage(
    user_id: str,
    group_id: str | None,
    cost: float,
    is_superuser: bool = False,
    count: int = 1,
) -> dict:
    """
    记录一次使用 (仅在成功时调用)

    Args:
        user_id: 用户 ID
        group_id: 群 ID (可选)
        cost: 本次总花费 (RMB, 已含 count 倍率)
        is_superuser: 是否 superuser
        count: 生成张数 (同时计入次数)
    """
    data = _load_data()
    today = _get_today()

    if is_superuser:
        # superuser 单独累计, 不受每日限制, 不计入群组
        if "superusers" not in data:
            data["superusers"] = {}
        if user_id not in data["superusers"]:
            data["superusers"][user_id] = {"total_count": 0, "total_cost": 0.0}
        su_data = data["superusers"][user_id]
        su_data["total_count"] += count
        su_data["total_cost"] += cost

        _save_data(data)

        return {
            "user_total_count": su_data["total_count"],
            "user_total_cost": su_data["total_cost"],
            "user_daily_count": 0,
            "group_total_count": 0,
            "group_total_cost": 0.0,
            "is_superuser": True,
        }

    # 普通用户
    if "users" not in data:
        data["users"] = {}

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "total_count": 0,
            "total_cost": 0.0,
            "daily_count": 0,
            "last_date": today,
        }

    user_data = data["users"][user_id]

    if user_data.get("last_date", "") != today:
        user_data["daily_count"] = 0
        user_data["last_date"] = today

    user_data["total_count"] += count
    user_data["total_cost"] += cost
    user_data["daily_count"] += count

    group_total_count = 0
    group_total_cost = 0.0
    if group_id:
        if "groups" not in data:
            data["groups"] = {}
        if group_id not in data["groups"]:
            data["groups"][group_id] = {"total_count": 0, "total_cost": 0.0}
        group_data = data["groups"][group_id]
        group_data["total_count"] += count
        group_data["total_cost"] += cost
        group_total_count = group_data["total_count"]
        group_total_cost = group_data["total_cost"]

    _save_data(data)

    return {
        "user_total_count": user_data["total_count"],
        "user_total_cost": user_data["total_cost"],
        "user_daily_count": user_data["daily_count"],
        "group_total_count": group_total_count,
        "group_total_cost": group_total_cost,
        "is_superuser": False,
    }


def get_group_stats(group_id: str) -> dict:
    data = _load_data()
    group_data = data.get("groups", {}).get(group_id, {})
    return {
        "total_count": group_data.get("total_count", 0),
        "total_cost": group_data.get("total_cost", 0.0),
    }


def get_user_stats(user_id: str) -> dict:
    data = _load_data()
    today = _get_today()

    user_data = data.get("users", {}).get(user_id, {})
    last_date = user_data.get("last_date", "")
    daily_count = user_data.get("daily_count", 0)

    if last_date != today:
        daily_count = 0

    return {
        "total_count": user_data.get("total_count", 0),
        "total_cost": user_data.get("total_cost", 0.0),
        "daily_count": daily_count,
        "remaining_today": max(0, DAILY_LIMIT - daily_count),
    }


def get_superuser_stats(user_id: str) -> dict:
    data = _load_data()
    su_data = data.get("superusers", {}).get(user_id, {})
    return {
        "total_count": su_data.get("total_count", 0),
        "total_cost": su_data.get("total_cost", 0.0),
    }
