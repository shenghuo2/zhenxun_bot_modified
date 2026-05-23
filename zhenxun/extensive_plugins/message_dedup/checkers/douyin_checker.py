import importlib
from pathlib import Path
import re
import sys
from typing import Any

from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from . import build_dup_reply, check_or_store

DOUYIN_URL_RE = re.compile(
    r"""https?://(?:(?:v|www|m)\.douyin\.com|www\.iesdouyin\.com)/[^\s\]"'<>]+"""
)
DOUYIN_STABLE_ID_RE = re.compile(
    r"(?:^|/)(?P<type>video|note|slides|share/(?:video|note|slides))/(?P<id>\d+)"
)
RESOLVER2_PARENT_DIR = Path(__file__).resolve().parents[3] / "plugins"
RESOLVER2_DIR = RESOLVER2_PARENT_DIR / "nonebot_plugin_resolver2"


def _resolver2_available() -> bool:
    return RESOLVER2_DIR.is_dir()


def _ensure_resolver2_parent_on_path() -> None:
    parent = str(RESOLVER2_PARENT_DIR)
    if parent not in sys.path:
        sys.path.insert(0, parent)


def _import_resolver2_parsers() -> tuple[Any, Any] | None:
    _ensure_resolver2_parent_on_path()
    try:
        douyin_module = importlib.import_module(
            "nonebot_plugin_resolver2.parsers.douyin"
        )
        parser_utils = importlib.import_module("nonebot_plugin_resolver2.parsers.utils")
    except Exception as e:
        logger.warning(
            f"nonebot_plugin_resolver2 不可导入，跳过抖音查重: {e}",
            "message_dedup",
        )
        return None
    return douyin_module, parser_utils


def _normalize_douyin_url(url: str) -> str:
    return url.rstrip(".,，。!！?？)）]】>")


def _extract_douyin_url(message: Message) -> str | None:
    text = message.extract_plain_text().strip()
    if matched := DOUYIN_URL_RE.search(text):
        return _normalize_douyin_url(matched.group(0))

    for seg in message:
        if seg.type != "json":
            continue
        data = seg.data.get("data")
        if not isinstance(data, str):
            continue
        data = data.replace("\\/", "/").replace("&amp;", "&")
        if matched := DOUYIN_URL_RE.search(data):
            return _normalize_douyin_url(matched.group(0))

    return None


def _extract_stable_id(url: str) -> str | None:
    if matched := DOUYIN_STABLE_ID_RE.search(url):
        item_type = matched.group("type").removeprefix("share/")
        return f"{item_type}_{matched.group('id')}"
    return None


async def _resolve_douyin(
    url: str,
) -> tuple[str, Any, str] | None:
    """返回 (稳定 ID, 解析结果, 最终用于解析的 URL)。"""
    resolver2_parsers = _import_resolver2_parsers()
    if not resolver2_parsers:
        return None

    douyin_module, parser_utils = resolver2_parsers
    parser = douyin_module.DouyinParser()
    parse_url = url
    stable_id = _extract_stable_id(parse_url)

    if not stable_id:
        try:
            parse_url = await parser_utils.get_redirect_url(url)
        except Exception as e:
            logger.warning(f"抖音短链重定向失败，跳过查重: {e}", "message_dedup")
            return None
        stable_id = _extract_stable_id(parse_url)

    if not stable_id:
        logger.warning(f"未能从抖音链接中提取稳定 ID: {url}", "message_dedup")
        return None

    try:
        parse_result = await parser.parse_share_url(parse_url)
    except Exception as e:
        logger.warning(f"抖音解析失败，跳过查重: {e}", "message_dedup")
        return None

    return stable_id, parse_result, parse_url


def make_douyin_sha(stable_id: str) -> str:
    return f"douyin_{stable_id}"


async def check_and_store_douyin(
    event: MessageEvent,
    group_id: str,
    stable_id: str,
    parse_result: Any,
    message_id: str,
    sender_id: str,
) -> Message | None:
    """查库并返回重复提示消息，如果没有重复则存储并返回 None。"""
    sha = make_douyin_sha(stable_id)
    result = await check_or_store(sha, group_id, message_id, sender_id)
    title = parse_result.title or "这个抖音作品"
    if result.is_dup:
        text = (
            f"抖音《{title}》在{result.time_diff_str}就有人发过了喵"
            f"（第{result.hit_count}次发了捏）"
        )
        return build_dup_reply(
            result,
            event.user_id,
            text,
        )

    logger.info(
        f"已存储抖音作品 {message_id} stable_id={stable_id} "
        f"group={group_id} sender={sender_id}",
        "message_dedup",
    )
    return None


async def check_douyin(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查抖音解析内容是否重复。

    返回 Message 表示有重复需要发送，True 表示已处理无重复，
    False 表示非抖音消息或解析器不可用。
    """
    if not _resolver2_available():
        return False

    douyin_url = _extract_douyin_url(message)
    if not douyin_url:
        return False

    resolved = await _resolve_douyin(douyin_url)
    if not resolved:
        return False

    stable_id, parse_result, _ = resolved
    group_id = str(session.group.id)
    message_id = str(event.message_id)
    sender_id = str(event.user_id)

    reply = await check_and_store_douyin(
        event, group_id, stable_id, parse_result, message_id, sender_id
    )
    return reply if reply else True
