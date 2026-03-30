import datetime
import hashlib
import html
import json
import re
from typing import Any

import aiohttp
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

from zhenxun.services.log import logger
from zhenxun.utils.user_agent import get_user_agent

from .config import REPLY_IMAGE
from .db import utcnow

# ── 通用工具 ─────────────────────────────────────────────

def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_time_diff_str(timestamp: datetime.datetime) -> str:
    now = utcnow()
    # 转换为 UTC+8 用于日期比较和显示
    utc8 = datetime.timezone(datetime.timedelta(hours=8))
    now_local = now.replace(tzinfo=datetime.timezone.utc).astimezone(utc8)
    ts_local = timestamp.replace(tzinfo=datetime.timezone.utc).astimezone(utc8)

    if now_local.year != ts_local.year:
        return f"{ts_local.year}年{ts_local.month}月{ts_local.day}日"
    if now_local.month != ts_local.month:
        return f"{ts_local.month}月{ts_local.day}日"
    if now_local.day != ts_local.day:
        return f"{ts_local.day}日"

    # 同一天内
    diff = now - timestamp
    if diff.seconds >= 3600:
        return f"{ts_local.hour}点"
    if diff.seconds >= 60:
        return f"{diff.seconds // 60}分钟之前"
    if diff.seconds > 0:
        return f"{diff.seconds}秒之前"
    return "刚刚"


def int_to_datetime(timestamp: int) -> datetime.datetime:
    utc_plus_8 = datetime.timezone(datetime.timedelta(hours=8))
    dt = datetime.datetime.fromtimestamp(timestamp, tz=utc_plus_8)
    return dt.astimezone(datetime.timezone.utc)


def build_reply_image_seg() -> MessageSegment:
    import base64
    data = REPLY_IMAGE.read_bytes()
    b64 = base64.b64encode(data).decode()
    return MessageSegment.image(file=f"base64://{b64}")


def extract_file_unique(message_content: str) -> str | None:
    match = re.search(r"file_unique=([a-fA-F0-9]+)", message_content)
    return match.group(1) if match else None


# ── 转发消息工具 ──────────────────────────────────────────

async def get_forward_messages(forward_message_id: str, bot: Bot) -> list[str]:
    try:
        response: dict = await bot.call_api(
            "get_forward_msg", message_id=forward_message_id
        )
        messages = response.get("messages", [])
        result = []
        for msg in messages:
            if "[CQ:forward," in msg["raw_message"]:
                ts = msg.get("time")
                result.append(f"has_Forward_message_with_timestamp_{ts}")
            else:
                raw = html.unescape(msg["raw_message"])
                if "file_unique" in str(msg):
                    fu = extract_file_unique(msg["raw_message"])
                    result.append(fu or raw)
                else:
                    result.append(raw)
        return result
    except Exception as e:
        logger.error(f"获取转发消息失败: {e}")
        return []


async def get_forward_fingerprint(forward_message_id: str, bot: Bot) -> str | None:
    """从转发消息中提取稳定指纹。

    调用 get_forward_msg API 获取子消息列表，
    使用每条子消息的 (time, real_seq) 拼接后取 SHA-256。
    这两个字段在不同群转发同一条消息时完全一致，
    而 message_id、file、file_size、url 等字段都不稳定。

    单条子消息（通常是媒体文件）时额外加入 user_id 和 group_id 降低碰撞。
    """
    try:
        response: dict = await bot.call_api(
            "get_forward_msg", message_id=forward_message_id
        )
        messages = response.get("messages", [])
        if not messages:
            return None

        # 单条子消息且是媒体文件时，加上 user_id 和 group_id 降低碰撞
        # 多条子消息时 time+real_seq 组合已足够唯一
        use_extra = len(messages) == 1

        parts = []
        for msg in messages:
            t = msg.get("time", "")
            seq = msg.get("real_seq", "")
            if use_extra:
                uid = msg.get("user_id", "")
                gid = msg.get("group_id", "")
                parts.append(f"{uid}@{gid}:{t}:{seq}")
            else:
                parts.append(f"{t}:{seq}")

        fingerprint = "|".join(parts)
        logger.info(f"转发消息指纹拼接: {fingerprint}", "message_dedup")
        return compute_sha256(fingerprint)
    except Exception as e:
        logger.error(f"获取转发消息指纹失败: {e}", "message_dedup")
        return None


# ── Bilibili 工具 ─────────────────────────────────────────

BILIBILI_URL_PATTERNS = [
    r"https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+",
    r"https?://b23\.tv/[A-Za-z0-9]+",
    r"BV[A-Za-z0-9]{10}",
    r"av\d+",
]

BILIBILI_BROAD_PATTERNS = BILIBILI_URL_PATTERNS + [
    r"bilibili\.com",
    r"b23\.tv",
]


def contains_bilibili_url(message_text: str) -> bool:
    """判断纯文本中是否包含B站视频链接（不再因为消息带图片就跳过）"""
    for pattern in BILIBILI_BROAD_PATTERNS:
        if re.search(pattern, message_text, re.IGNORECASE):
            return True
    return False


def extract_bilibili_url(text: str) -> str | None:
    match = re.search(
        r"https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+", text
    )
    if match:
        return match.group(0)

    match = re.search(r"https?://b23\.tv/[A-Za-z0-9]+", text)
    if match:
        return match.group(0)

    match = re.search(r"BV[A-Za-z0-9]{10}", text)
    if match:
        return f"https://www.bilibili.com/video/{match.group(0)}"

    match = re.search(r"av(\d+)", text)
    if match:
        return f"https://www.bilibili.com/video/av{match.group(1)}"

    return None


def _search_url_in_json(data: Any, depth: int = 0, max_depth: int = 5) -> str | None:
    if depth > max_depth:
        return None
    if isinstance(data, dict):
        for key in ("url", "jumpUrl", "qqdocurl", "link", "href"):
            val = data.get(key)
            if isinstance(val, str) and ("bilibili.com" in val or "b23.tv" in val):
                return val
        for val in data.values():
            r = _search_url_in_json(val, depth + 1, max_depth)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _search_url_in_json(item, depth + 1, max_depth)
            if r:
                return r
    elif isinstance(data, str):
        if "bilibili.com/video" in data or "b23.tv" in data:
            return extract_bilibili_url(data)
    return None


async def resolve_bilibili_video_id(url: str) -> dict[str, str] | None:
    """解析B站链接，返回 {"video_id": ..., "title": ..., "url": ...} 或 None。
    只做一次 HTTP 重定向 + 一次 bilireq API 调用（不再重复重定向）。
    """
    try:
        from bilireq import video as bili_video

        async with aiohttp.ClientSession(headers=get_user_agent()) as sess:
            async with sess.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                real_url = str(resp.url).split("?")[0].rstrip("/")

        if not real_url.startswith(
            ("https://www.bilibili.com/video", "https://m.bilibili.com/video")
        ):
            return None

        vid = real_url.split("/")[-1]
        vd_info = await bili_video.get_video_base_info(vid)
        video_id = vd_info.get("bvid") or f"av{vd_info.get('aid')}"
        return {
            "video_id": video_id,
            "title": vd_info.get("title", "未知视频"),
            "url": real_url,
        }
    except Exception as e:
        logger.error(f"解析B站视频链接失败: {e}")
        return None


async def extract_bilibili_card_info(message: Message) -> dict[str, Any] | None:
    """从 JSON 卡片中提取B站视频信息"""
    for seg in message:
        if seg.type != "json":
            continue
        try:
            data = json.loads(seg.data.get("data", "{}"))
        except (json.JSONDecodeError, TypeError):
            continue

        # 尝试从 JSON 结构中找到 B站链接
        url: str | None = None

        # 标准哔哩哔哩卡片
        if data.get("desc") == "哔哩哔哩" or "哔哩哔哩" in data.get("prompt", ""):
            meta = data.get("meta", {})
            detail = meta.get("detail_1", {})
            url = detail.get("qqdocurl")

        # QQ小程序格式
        if not url and "小程序" in data.get("prompt", ""):
            url = _search_url_in_json(data)

        # 最终兜底：从 JSON 字符串中正则搜索
        if not url:
            url = extract_bilibili_url(json.dumps(data))

        if url:
            info = await resolve_bilibili_video_id(url)
            if info:
                return info

    return None
