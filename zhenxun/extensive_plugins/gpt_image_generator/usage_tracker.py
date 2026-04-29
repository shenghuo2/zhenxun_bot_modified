"""
用量追踪
- 每日免费次数按 (用户+群/私聊) 隔离, 按天清零
- 优先消耗每日免费额度, 再用永久次数 (不失效, 全局)
- 按用户累计计费 (不按天清零)
- 按群组累计计费 (不按天清零, 不含 superuser)
- superuser 单独累计计费 (不加入群组统计)
- 数据持久化到 JSON 文件
"""

import json
from datetime import date
from pathlib import Path

from .config import DAILY_LIMIT, GROUP_DAILY_LIMITS

DATA_FILE = Path(__file__).parent / "usage_data.json"


def _load_data() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "users": {},       # {total_count, total_cost, permanent_credits, daily_scopes: {scope: {count, last_date}}}
        "groups": {},       # {total_count, total_cost}
        "superusers": {},   # {total_count, total_cost}
    }


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_today() -> str:
    return date.today().isoformat()


def _get_daily_limit(group_id: str | None) -> int:
    """获取指定群的每日限额"""
    if group_id and group_id in GROUP_DAILY_LIMITS:
        return GROUP_DAILY_LIMITS[group_id]
    return DAILY_LIMIT


def _scope_key(group_id: str | None) -> str:
    """生成每日计数的 scope key: 群号 或 'private'"""
    return group_id if group_id else "private"


def _get_daily_count(user_data: dict, scope: str, today: str) -> int:
    """获取指定 scope 的今日已用次数"""
    scopes = user_data.get("daily_scopes", {})
    scope_data = scopes.get(scope, {})
    if scope_data.get("last_date") != today:
        return 0
    return scope_data.get("count", 0)


def _set_daily_count(user_data: dict, scope: str, today: str, count: int) -> None:
    """设置指定 scope 的今日已用次数"""
    if "daily_scopes" not in user_data:
        user_data["daily_scopes"] = {}
    user_data["daily_scopes"][scope] = {"count": count, "last_date": today}


def _migrate_old_format(user_data: dict, today: str) -> None:
    """兼容旧格式: daily_count/last_date → daily_scopes"""
    if "daily_count" in user_data and "daily_scopes" not in user_data:
        old_count = user_data.pop("daily_count", 0)
        old_date = user_data.pop("last_date", "")
        if old_date == today and old_count > 0:
            user_data["daily_scopes"] = {
                "private": {"count": old_count, "last_date": old_date}
            }
        else:
            user_data["daily_scopes"] = {}


def add_credits(user_id: str, amount: int) -> int:
    """给用户添加永久次数 (不失效). 返回当前余额."""
    data = _load_data()
    today = _get_today()

    if "users" not in data:
        data["users"] = {}

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "total_count": 0, "total_cost": 0.0,
            "permanent_credits": 0, "daily_scopes": {},
        }
    else:
        _migrate_old_format(data["users"][user_id], today)

    user_data = data["users"][user_id]
    if "permanent_credits" not in user_data:
        user_data["permanent_credits"] = 0

    user_data["permanent_credits"] += amount
    _save_data(data)
    return user_data["permanent_credits"]


def check_user_limit(user_id: str, group_id: str | None) -> dict:
    """
    检查普通用户是否可生成, 优先消耗每日免费额度.

    Returns:
        {"can_use", "daily_count", "daily_limit", "permanent_credits",
         "free_remaining", "total_available"}
    """
    data = _load_data()
    today = _get_today()
    daily_limit = _get_daily_limit(group_id)
    scope = _scope_key(group_id)

    user_data = data.get("users", {}).get(user_id, {})
    _migrate_old_format(user_data, today)

    daily_count = _get_daily_count(user_data, scope, today)
    permanent_credits = user_data.get("permanent_credits", 0)

    free_remaining = max(0, daily_limit - daily_count)
    total_available = free_remaining + permanent_credits

    return {
        "can_use": total_available > 0,
        "daily_count": daily_count,
        "daily_limit": daily_limit,
        "permanent_credits": permanent_credits,
        "free_remaining": free_remaining,
        "total_available": total_available,
    }


def record_usage(
    user_id: str,
    group_id: str | None,
    cost: float,
    is_superuser: bool = False,
    count: int = 1,
) -> dict:
    """
    记录一次使用 (仅在成功时调用).
    优先消耗该 scope 的每日免费额度, 超出部分扣永久次数.
    """
    data = _load_data()
    today = _get_today()
    scope = _scope_key(group_id)

    if is_superuser:
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
            "user_daily_count": 0, "daily_limit": 0,
            "permanent_credits": 0, "used_free": 0, "used_permanent": 0,
            "group_total_count": 0, "group_total_cost": 0.0,
            "is_superuser": True,
        }

    # 普通用户
    if "users" not in data:
        data["users"] = {}

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "total_count": 0, "total_cost": 0.0,
            "permanent_credits": 0, "daily_scopes": {},
        }
    else:
        _migrate_old_format(data["users"][user_id], today)

    user_data = data["users"][user_id]
    if "permanent_credits" not in user_data:
        user_data["permanent_credits"] = 0

    daily_limit = _get_daily_limit(group_id)
    daily_count = _get_daily_count(user_data, scope, today)
    free_remaining = max(0, daily_limit - daily_count)

    used_free = min(count, free_remaining)
    used_permanent = count - used_free

    _set_daily_count(user_data, scope, today, daily_count + used_free)
    user_data["permanent_credits"] -= used_permanent
    user_data["total_count"] += count
    user_data["total_cost"] += cost

    group_total_count = 0
    group_total_cost = 0.0
    if group_id:
        if "groups" not in data:
            data["groups"] = {}
        if group_id not in data["groups"]:
            data["groups"][group_id] = {"total_count": 0, "total_cost": 0.0}
        gd = data["groups"][group_id]
        gd["total_count"] += count
        gd["total_cost"] += cost
        group_total_count = gd["total_count"]
        group_total_cost = gd["total_cost"]

    _save_data(data)

    return {
        "user_total_count": user_data["total_count"],
        "user_total_cost": user_data["total_cost"],
        "user_daily_count": daily_count + used_free,
        "daily_limit": daily_limit,
        "permanent_credits": user_data["permanent_credits"],
        "used_free": used_free,
        "used_permanent": used_permanent,
        "group_total_count": group_total_count,
        "group_total_cost": group_total_cost,
        "is_superuser": False,
    }


def get_group_stats(group_id: str) -> dict:
    data = _load_data()
    gd = data.get("groups", {}).get(group_id, {})
    return {"total_count": gd.get("total_count", 0), "total_cost": gd.get("total_cost", 0.0)}


def get_user_stats(user_id: str) -> dict:
    data = _load_data()
    today = _get_today()
    ud = data.get("users", {}).get(user_id, {})
    return {
        "total_count": ud.get("total_count", 0),
        "total_cost": ud.get("total_cost", 0.0),
        "permanent_credits": ud.get("permanent_credits", 0),
    }


def get_superuser_stats(user_id: str) -> dict:
    data = _load_data()
    su = data.get("superusers", {}).get(user_id, {})
    return {"total_count": su.get("total_count", 0), "total_cost": su.get("total_cost", 0.0)}
