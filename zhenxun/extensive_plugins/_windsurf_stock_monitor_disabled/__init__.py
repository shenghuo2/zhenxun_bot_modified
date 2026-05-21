"""
Windsurf 库存监控插件
每分钟检查目标商品库存，命中后推送 QQ 群消息并可选发送 SMTP 邮件
"""

from __future__ import annotations

import asyncio
import json
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import httpx
from nonebot import get_bots, on_command, require
from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .config import (CHECK_INTERVAL_MINUTES, GOODS_TYPE, QQ_GROUP_IDS,
                     REPEAT_NOTIFY_WHEN_IN_STOCK, REQUEST_COOKIES,
                     REQUEST_HEADERS, REQUEST_TIMEOUT, SHOP_API_URL,
                     SHOP_TOKEN, SMTP_ENABLED, SMTP_FROM, SMTP_HOST,
                     SMTP_PASSWORD, SMTP_PORT, SMTP_SUBJECT, SMTP_TO,
                     SMTP_USE_SSL, SMTP_USE_STARTTLS, SMTP_USERNAME,
                     TARGET_CATEGORY_NAME, TARGET_GOODS_NAMES)

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name="Windsurf 库存监控",
    description="每分钟检查 Windsurf 指定商品库存，补货后自动通知",
    usage="后台自动运行；#windsurf测试smtp 可测试邮件配置（仅超级用户）",
    extra=PluginExtraData(
        author="",
        version="0.1.0",
        plugin_type=PluginType.NORMAL,
        is_show=False,
        commands=[Command(command="#windsurf测试smtp")],
    ).to_dict(),
)

_STATE_DIR: Path = DATA_PATH / "windsurf_stock_monitor"
_STATE_FILE: Path = _STATE_DIR / "stock_state.json"
# 状态结构: {商品名: {"stock": int, "price": float}}
_stock_state: dict[str, dict[str, Any]] = {}

_smtp_test_cmd = on_command(
    "#windsurf测试smtp",
    aliases={"#windsurf测试邮箱", "#测试windsurf smtp"},
    priority=5,
    block=True,
    permission=SUPERUSER,
)


@dataclass
class GoodsInfo:
    """商品简要信息"""

    name: str
    stock_count: int
    price: float
    link: str


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_state() -> None:
    global _stock_state

    if not _STATE_FILE.exists():
        _stock_state = {}
        return

    try:
        raw_data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(raw_data, dict):
            # 兼容旧格式（纯数字）和新格式（字典）
            _stock_state = {}
            for k, v in raw_data.items():
                if isinstance(v, dict):
                    _stock_state[str(k)] = {
                        "stock": _safe_int(v.get("stock", 0)),
                        "price": _safe_float(v.get("price", 0.0)),
                    }
                else:
                    # 旧格式兼容
                    _stock_state[str(k)] = {"stock": _safe_int(v), "price": 0.0}
        else:
            _stock_state = {}
    except Exception as e:
        logger.warning(f"Windsurf 监控状态读取失败，将使用空状态: {e}")
        _stock_state = {}


def _save_state() -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(
        json.dumps(_stock_state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def _fetch_goods_list() -> list[dict[str, Any]]:
    payload = {
        "token": SHOP_TOKEN,
        "keywords": "",
        "goods_type": GOODS_TYPE,
        "current": 1,
        "pageSize": 999999,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            SHOP_API_URL,
            headers=REQUEST_HEADERS,
            cookies=REQUEST_COOKIES,
            json=payload,
        )

    if response.status_code != 200:
        body = response.text.strip()[:500]
        raise RuntimeError(f"请求失败(status={response.status_code}): {body}")

    try:
        result = response.json()
    except json.JSONDecodeError as e:
        snippet = response.text.strip()[:500]
        raise RuntimeError(f"返回内容不是 JSON: {snippet}") from e

    if not isinstance(result, dict):
        raise RuntimeError(f"返回结构异常: {type(result).__name__}")
    if result.get("code") != 1:
        raise RuntimeError(f"接口返回失败: code={result.get('code')} msg={result.get('msg')}")

    data = result.get("data")
    if not isinstance(data, dict):
        return []

    goods_list = data.get("list", [])
    if not isinstance(goods_list, list):
        return []

    return [item for item in goods_list if isinstance(item, dict)]


def _extract_target_goods(goods_list: list[dict[str, Any]]) -> dict[str, GoodsInfo]:
    target_set = set(TARGET_GOODS_NAMES)
    result: dict[str, GoodsInfo] = {}

    for item in goods_list:
        name = str(item.get("name", "")).strip()
        if name not in target_set:
            continue

        category_data = item.get("category")
        category_name = ""
        if isinstance(category_data, dict):
            category_name = str(category_data.get("name", "")).strip()

        if TARGET_CATEGORY_NAME and category_name != TARGET_CATEGORY_NAME:
            continue

        extend_data = item.get("extend")
        stock_count = 0
        if isinstance(extend_data, dict):
            stock_count = _safe_int(extend_data.get("stock_count", 0))

        result[name] = GoodsInfo(
            name=name,
            stock_count=stock_count,
            price=_safe_float(item.get("price", 0)),
            link=str(item.get("link", "")).strip(),
        )

    for name in TARGET_GOODS_NAMES:
        result.setdefault(name, GoodsInfo(name=name, stock_count=0, price=0.0, link=""))

    return result


@dataclass
class AlertInfo:
    """提醒信息"""
    goods: GoodsInfo
    alert_type: str  # "restock": 补货, "decrease": 数量减少, "price_change": 价格变化
    previous_stock: int = 0
    previous_price: float = 0.0


def _collect_alerts(current_goods: dict[str, GoodsInfo]) -> tuple[list[AlertInfo], list[AlertInfo]]:
    """
    收集提醒信息
    返回: (需要邮件的提醒列表, 不需要邮件的提醒列表)
    """
    email_alerts: list[AlertInfo] = []  # 补货提醒，需要邮件
    no_email_alerts: list[AlertInfo] = []  # 数量减少/价格变化，不需要邮件

    for name in TARGET_GOODS_NAMES:
        info = current_goods.get(name, GoodsInfo(name=name, stock_count=0, price=0.0, link=""))
        prev_state = _stock_state.get(name, {"stock": 0, "price": 0.0})
        previous_stock = prev_state.get("stock", 0)
        previous_price = prev_state.get("price", 0.0)
        current_stock = info.stock_count
        current_price = info.price

        alerted = False  # 标记是否已经添加过提醒，避免重复

        # 补货提醒：从 0 变为 >0（优先级最高）
        if current_stock > 0 and (REPEAT_NOTIFY_WHEN_IN_STOCK or previous_stock <= 0):
            email_alerts.append(AlertInfo(
                goods=info,
                alert_type="restock",
                previous_stock=previous_stock,
                previous_price=previous_price,
            ))
            alerted = True
        
        # 数量减少提醒：之前有货(>0)，现在数量减少了（包括变为0）
        # 只有在没有触发补货提醒时才检查
        if not alerted and previous_stock > 0 and current_stock < previous_stock:
            no_email_alerts.append(AlertInfo(
                goods=info,
                alert_type="decrease",
                previous_stock=previous_stock,
                previous_price=previous_price,
            ))
            alerted = True
        
        # 价格变化提醒：库存>0 且价格发生变化
        # 只有在没有触发其他提醒时才检查
        if not alerted and current_stock > 0 and previous_price > 0 and abs(current_price - previous_price) > 0.01:
            no_email_alerts.append(AlertInfo(
                goods=info,
                alert_type="price_change",
                previous_stock=previous_stock,
                previous_price=previous_price,
            ))

        # 更新状态
        _stock_state[name] = {"stock": current_stock, "price": current_price}

    return email_alerts, no_email_alerts


def _build_notify_message(alerts: list[AlertInfo], title: str) -> str:
    lines = [title]
    for alert in alerts:
        item = alert.goods
        if alert.alert_type == "restock":
            lines.append(f"{item.name} | 库存: {item.stock_count} | 价格: {item.price:g}")
        elif alert.alert_type == "decrease":
            lines.append(f"{item.name} | 库存: {alert.previous_stock} → {item.stock_count} | 价格: {item.price:g}")
        elif alert.alert_type == "price_change":
            lines.append(f"{item.name} | 库存: {item.stock_count} | 价格: {alert.previous_price:g} → {item.price:g}")
        if item.link:
            lines.append(item.link)
    lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


async def _send_group_message(message: str) -> None:
    if not QQ_GROUP_IDS:
        logger.warning("Windsurf 监控未配置 QQ_GROUP_IDS，跳过群消息推送")
        return

    onebot_bots = [bot for bot in get_bots().values() if isinstance(bot, Bot)]
    if not onebot_bots:
        logger.warning("Windsurf 监控未找到 OneBot v11 Bot 实例，跳过群消息推送")
        return

    bot = onebot_bots[0]
    for group_id in QQ_GROUP_IDS:
        try:
            await bot.send_group_msg(group_id=int(group_id), message=Message(message))
        except Exception as e:
            logger.error(f"Windsurf 监控发送群消息失败 group_id={group_id}: {e}")


def _send_email_sync(message: str) -> None:
    sender = SMTP_FROM or SMTP_USERNAME
    if not sender:
        raise ValueError("SMTP_FROM 或 SMTP_USERNAME 不能为空")
    if not SMTP_HOST:
        raise ValueError("SMTP_HOST 不能为空")
    if not SMTP_TO:
        raise ValueError("SMTP_TO 不能为空")

    mail = MIMEText(message, "plain", "utf-8")
    mail["Subject"] = SMTP_SUBJECT
    mail["From"] = sender
    mail["To"] = ",".join(SMTP_TO)

    smtp_cls: type[smtplib.SMTP] | type[smtplib.SMTP_SSL]
    smtp_cls = smtplib.SMTP_SSL if SMTP_USE_SSL else smtplib.SMTP
    with smtp_cls(SMTP_HOST, SMTP_PORT, timeout=20) as client:
        if not SMTP_USE_SSL and SMTP_USE_STARTTLS:
            client.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            client.login(SMTP_USERNAME, SMTP_PASSWORD)
        client.sendmail(sender, SMTP_TO, mail.as_string())


async def _send_email_message(message: str) -> None:
    if not SMTP_ENABLED:
        return
    try:
        await asyncio.to_thread(_send_email_sync, message)
    except Exception as e:
        logger.error(f"Windsurf 监控发送邮件失败: {e}")


async def _monitor_once() -> None:
    goods_list = await _fetch_goods_list()
    current_goods = _extract_target_goods(goods_list)
    email_alerts, no_email_alerts = _collect_alerts(current_goods)
    _save_state()

    # 补货提醒（发群消息+邮件）
    if email_alerts:
        notify_text = _build_notify_message(email_alerts, "【Windsurf 库存提醒】以下商品已补货：")
        await _send_group_message(notify_text)
        await _send_email_message(notify_text)
        logger.success(f"Windsurf 补货提醒已发送，命中商品数: {len(email_alerts)}")

    # 数量减少/价格变化提醒（仅发群消息，不发邮件）
    if no_email_alerts:
        # 按类型分组构建消息
        decrease_alerts = [a for a in no_email_alerts if a.alert_type == "decrease"]
        price_alerts = [a for a in no_email_alerts if a.alert_type == "price_change"]
        
        if decrease_alerts:
            notify_text = _build_notify_message(decrease_alerts, "【Windsurf 库存变化】以下商品库存减少：")
            await _send_group_message(notify_text)
            logger.info(f"Windsurf 库存减少提醒已发送，命中商品数: {len(decrease_alerts)}")
        
        if price_alerts:
            notify_text = _build_notify_message(price_alerts, "【Windsurf 价格变化】以下商品价格变动：")
            await _send_group_message(notify_text)
            logger.info(f"Windsurf 价格变化提醒已发送，命中商品数: {len(price_alerts)}")


@_smtp_test_cmd.handle()
async def _handle_smtp_test(event: MessageEvent) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"Windsurf SMTP 测试邮件\n时间: {now}\n触发者: {event.user_id}"
    try:
        await asyncio.to_thread(_send_email_sync, body)
    except Exception as e:
        await _smtp_test_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"SMTP 测试失败: {e}")
            )
        )
        return

    await _smtp_test_cmd.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("SMTP 测试成功，邮件已发送")
        )
    )


_load_state()
_interval_minutes = CHECK_INTERVAL_MINUTES if CHECK_INTERVAL_MINUTES > 0 else 1


@scheduler.scheduled_job(
    "interval",
    minutes=_interval_minutes,
    id="windsurf_stock_monitor_job",
    max_instances=1,
    coalesce=True,
    misfire_grace_time=30,
)
async def _windsurf_stock_monitor_job() -> None:
    try:
        await _monitor_once()
    except Exception as e:
        logger.exception(f"Windsurf 监控任务执行失败: {e}")
