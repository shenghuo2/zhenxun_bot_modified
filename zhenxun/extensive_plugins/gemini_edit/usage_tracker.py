"""
使用次数追踪器
- 每人每天限制3次
- 记录群总使用次数和总花费
- 数据持久化到 JSON 文件
"""

import json
from datetime import date
from pathlib import Path

# 数据文件路径（与本文件同目录）
DATA_FILE = Path(__file__).parent / "usage_data.json"

# 每人每天限制次数
DAILY_LIMIT = 3


def _load_data() -> dict:
    """加载数据"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "users": {},  # user_id -> {"total_count": int, "daily_count": int, "last_date": str}
        "groups": {},  # group_id -> {"total_count": int, "total_cost": float}
    }


def _save_data(data: dict) -> None:
    """保存数据"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_today() -> str:
    """获取今天日期字符串"""
    return date.today().isoformat()


def check_user_limit(user_id: str) -> tuple[bool, int]:
    """
    检查用户是否超过每日限制

    Args:
        user_id: 用户 ID

    Returns:
        tuple[bool, int]: (是否可以使用, 今日已使用次数)
    """
    data = _load_data()
    today = _get_today()

    user_data = data.get("users", {}).get(user_id, {})
    last_date = user_data.get("last_date", "")
    daily_count = user_data.get("daily_count", 0)

    # 如果日期变化，重置每日计数
    if last_date != today:
        daily_count = 0

    can_use = daily_count < DAILY_LIMIT
    return can_use, daily_count


def record_usage(
    user_id: str,
    group_id: str | None,
    cost: float,
) -> dict:
    """
    记录一次使用

    Args:
        user_id: 用户 ID
        group_id: 群 ID（可选）
        cost: 本次花费

    Returns:
        dict: 包含统计信息
    """
    data = _load_data()
    today = _get_today()

    # 更新用户数据
    if "users" not in data:
        data["users"] = {}

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "total_count": 0,
            "daily_count": 0,
            "last_date": today,
        }

    user_data = data["users"][user_id]

    # 如果日期变化，重置每日计数
    if user_data.get("last_date", "") != today:
        user_data["daily_count"] = 0
        user_data["last_date"] = today

    user_data["total_count"] += 1
    user_data["daily_count"] += 1

    # 更新群数据
    if group_id:
        if "groups" not in data:
            data["groups"] = {}

        if group_id not in data["groups"]:
            data["groups"][group_id] = {
                "total_count": 0,
                "total_cost": 0.0,
            }

        group_data = data["groups"][group_id]
        group_data["total_count"] += 1
        group_data["total_cost"] += cost

    _save_data(data)

    return {
        "user_daily_count": user_data["daily_count"],
        "user_total_count": user_data["total_count"],
        "group_total_count": data["groups"].get(group_id, {}).get("total_count", 0)
        if group_id
        else 0,
        "group_total_cost": data["groups"].get(group_id, {}).get("total_cost", 0.0)
        if group_id
        else 0.0,
    }


def get_group_stats(group_id: str) -> dict:
    """
    获取群统计信息

    Args:
        group_id: 群 ID

    Returns:
        dict: 群统计信息
    """
    data = _load_data()
    group_data = data.get("groups", {}).get(group_id, {})
    return {
        "total_count": group_data.get("total_count", 0),
        "total_cost": group_data.get("total_cost", 0.0),
    }


def get_user_stats(user_id: str) -> dict:
    """
    获取用户统计信息

    Args:
        user_id: 用户 ID

    Returns:
        dict: 用户统计信息
    """
    data = _load_data()
    today = _get_today()

    user_data = data.get("users", {}).get(user_id, {})
    last_date = user_data.get("last_date", "")
    daily_count = user_data.get("daily_count", 0)

    # 如果日期变化，每日计数显示为0
    if last_date != today:
        daily_count = 0

    return {
        "total_count": user_data.get("total_count", 0),
        "daily_count": daily_count,
        "remaining_today": max(0, DAILY_LIMIT - daily_count),
    }
