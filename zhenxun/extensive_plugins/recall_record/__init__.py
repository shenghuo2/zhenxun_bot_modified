from __future__ import annotations

from collections import OrderedDict
import base64
from datetime import datetime, timedelta
import hashlib
import html
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from nonebot import on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.models.group_member_info import GroupInfoUser
from zhenxun.services.log import logger
from zhenxun.utils.enum import PluginType
from zhenxun.utils.http_utils import AsyncHttpx
from zhenxun.utils.rules import notice_rule

from .config import MONITORED_GROUP_IDS
from .model import RecallRecord

__plugin_meta__ = PluginMetadata(
    name="撤回记录",
    description="记录指定群的消息与撤回事件，并提供超级用户查询命令",
    usage="""
    仅监控 config.py 里配置的群号

    指令：
        #撤回查询
        #撤回查询 群号
        #撤回查询 2026-03-30
        #撤回查询 群号 2026-03-30
        #撤回查询 消息ID
    """.strip(),
    extra=PluginExtraData(
        author="Codex",
        version="0.1.1",
        plugin_type=PluginType.HIDDEN,
        commands=[
            Command(command="#撤回查询"),
        ],
    ).to_dict(),
)

_MONITORED_GROUP_SET = {str(group_id) for group_id in MONITORED_GROUP_IDS}
_IMAGE_CACHE_DIR = Path(__file__).parent / "image_cache"
_IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_IMAGE_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}

_record_message = on_message(priority=1, block=False)
_record_recall = on_notice(
    priority=1,
    block=False,
    rule=notice_rule(GroupRecallNoticeEvent),
)
_query_recall = on_command(
    "#撤回查询",
    aliases={"#撤回记录查询"},
    priority=5,
    block=True,
    permission=SUPERUSER,
)


def _is_monitored_group(group_id: int | str | None) -> bool:
    return bool(group_id and str(group_id) in _MONITORED_GROUP_SET)


def _to_datetime(timestamp: int | float | None) -> datetime:
    if not timestamp:
        return datetime.now()
    return datetime.fromtimestamp(timestamp)


def _normalize_message_content(message: Message) -> tuple[str | None, str | None]:
    raw_message = str(message).strip() or None
    plain_text = message.extract_plain_text().strip() or None
    if raw_message is None and plain_text is not None:
        raw_message = plain_text
    return raw_message, plain_text


def _guess_image_suffix(image_url: str, content_type: str | None) -> str:
    normalized_content_type = (
        str(content_type or "").split(";", 1)[0].strip().lower()
    )
    if normalized_content_type in _IMAGE_SUFFIX_MAP:
        return _IMAGE_SUFFIX_MAP[normalized_content_type]

    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


async def _cache_image_locally(
    image_url: str,
    *,
    group_id: str,
    message_id: str,
    index: int,
) -> str | None:
    try:
        response = await AsyncHttpx.get(
            image_url,
            timeout=30,
            follow_redirects=True,
        )
        response.raise_for_status()
    except Exception as e:
        logger.warning(
            f"缓存撤回图片失败 group={group_id} message_id={message_id} "
            f"index={index} url={image_url}: {e}",
            "撤回记录",
        )
        return None

    content = response.content
    if not content:
        logger.warning(
            f"缓存撤回图片为空 group={group_id} message_id={message_id} "
            f"index={index} url={image_url}",
            "撤回记录",
        )
        return None

    digest = hashlib.sha256(content).hexdigest()
    suffix = _guess_image_suffix(image_url, response.headers.get("content-type"))
    save_path = _IMAGE_CACHE_DIR / f"{digest}{suffix}"
    if not save_path.exists():
        save_path.write_bytes(content)
    return f"file:///{save_path.resolve()}"


async def _cache_message_images(
    message: Message,
    *,
    group_id: str,
    message_id: str,
) -> Message:
    cached_message = Message()
    for index, segment in enumerate(message):
        if segment.type != "image":
            cached_message += segment
            continue

        image_source = str(segment.data.get("url") or segment.data.get("file") or "").strip()
        if not image_source:
            cached_message += segment
            continue
        if image_source.startswith(("file://", "base64://")):
            cached_message += segment
            continue
        if not image_source.startswith(("http://", "https://")):
            cached_message += segment
            continue

        if cached_file_uri := await _cache_image_locally(
            image_source,
            group_id=group_id,
            message_id=message_id,
            index=index,
        ):
            cached_message += MessageSegment.image(file=cached_file_uri)
        else:
            cached_message += segment
    return cached_message


async def _prepare_message_for_storage(
    message: Message,
    *,
    group_id: str,
    message_id: str,
) -> tuple[str | None, str | None]:
    cached_message = await _cache_message_images(
        message,
        group_id=group_id,
        message_id=message_id,
    )
    return _normalize_message_content(cached_message)


async def _refresh_record_cached_images(record: RecallRecord) -> None:
    raw_message = (record.raw_message or "").strip()
    if not raw_message or "[CQ:image" not in raw_message:
        return

    cached_message = await _cache_message_images(
        Message(raw_message),
        group_id=record.group_id,
        message_id=record.message_id,
    )
    cached_raw_message, cached_plain_text = _normalize_message_content(cached_message)
    if cached_raw_message == record.raw_message and cached_plain_text == record.plain_text:
        return

    record.raw_message = cached_raw_message
    record.plain_text = cached_plain_text
    await record.save(update_fields=["raw_message", "plain_text"])


async def _get_group_user_name(user_id: str, group_id: str) -> str:
    if user := await GroupInfoUser.get_or_none(user_id=user_id, group_id=group_id):
        return (user.nickname or user.user_name or user_id).strip()
    return user_id


async def _get_event_user_name(event: GroupMessageEvent) -> str:
    sender = getattr(event, "sender", None)
    if sender:
        name = getattr(sender, "card", None) or getattr(sender, "nickname", None) or ""
        if name.strip():
            return name.strip()
    return await _get_group_user_name(str(event.user_id), str(event.group_id))


def _parse_date_arg(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    for fmt in ("%m-%d", "%m/%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(year=datetime.now().year)
        except ValueError:
            continue
    return None


def _parse_query_args(message_text: str) -> tuple[str | None, datetime | None, str | None]:
    parts = message_text.split()
    if parts and parts[0] in {
        "#撤回查询",
        "撤回查询",
        "#撤回记录查询",
        "撤回记录查询",
    }:
        parts = parts[1:]

    group_id: str | None = None
    query_date: datetime | None = None
    message_id: str | None = None

    for arg in parts:
        if query_date is None and (parsed_date := _parse_date_arg(arg)):
            query_date = parsed_date
            continue
        if group_id is None and arg in _MONITORED_GROUP_SET:
            group_id = arg
            continue
        if message_id is None and arg.isdigit():
            message_id = arg

    return group_id, query_date, message_id


def _get_date_scope(query_date: datetime | None) -> tuple[datetime, datetime]:
    current = query_date or datetime.now()
    start_time = current.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_time, start_time + timedelta(days=1)


def _format_day(value: datetime | None) -> str:
    return (value or datetime.now()).strftime("%Y-%m-%d")


def _format_clock(value: datetime | None) -> str:
    if not value:
        return "未知时间"
    return value.strftime("%H:%M:%S")


def _format_full_datetime(value: datetime | None) -> str:
    if not value:
        return "未知时间"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _format_content(record: RecallRecord) -> str:
    content = (record.raw_message or record.plain_text or "[未捕获到原消息内容]").strip()
    return content or "[未捕获到原消息内容]"


def _build_record_content_message(record: RecallRecord) -> Message:
    raw_message = (record.raw_message or "").strip()
    if raw_message:
        try:
            parsed_message = Message(raw_message)
            result = Message()
            for segment in parsed_message:
                if segment.type == "text":
                    result += segment
                elif segment.type == "image":
                    image_file = str(segment.data.get("file") or "").strip()
                    if image_file.startswith("file:///"):
                        local_path = Path(image_file.removeprefix("file:///"))
                        if local_path.exists():
                            image_base64 = base64.b64encode(local_path.read_bytes()).decode(
                                "ascii"
                            )
                            result += MessageSegment.image(f"base64://{image_base64}")
                        else:
                            result += MessageSegment.text("[图片缓存文件不存在]")
                    else:
                        result += segment
                else:
                    result += MessageSegment.text(str(segment))
            if result:
                return result
        except Exception:
            pass
    return Message(MessageSegment.text(_format_content(record)))


def _extract_forward_id(content: str | None) -> str | None:
    if not content:
        return None
    match = re.search(r"\[CQ:forward,id=([^,\]]+)", content)
    return match.group(1) if match else None


async def _build_forward_detail_text(bot: Bot, forward_id: str) -> str | None:
    try:
        response: dict = await bot.call_api("get_forward_msg", message_id=forward_id)
    except Exception as e:
        logger.error(f"获取合并转发内容失败: {e}", "撤回记录")
        return f"合并转发内容获取失败: {e}"

    messages = response.get("messages", [])
    if not messages:
        return "合并转发内容为空。"

    lines = [f"合并转发内容({forward_id})"]
    for index, msg in enumerate(messages, start=1):
        sender_name = (
            str(msg.get("sender", {}).get("nickname", "")).strip()
            if isinstance(msg.get("sender"), dict)
            else ""
        )
        sender_name = (
            sender_name
            or str(msg.get("nickname", "")).strip()
            or str(msg.get("name", "")).strip()
            or str(msg.get("user_id", "未知用户")).strip()
        )
        send_time = _format_full_datetime(_to_datetime(msg.get("time")))
        raw_message = html.unescape(str(msg.get("raw_message", "")).strip())
        content = raw_message or str(msg.get("content", "")).strip() or "[空消息]"
        lines.append(f"{index}. {send_time} {sender_name}")
        lines.append(content)
        lines.append("")
    return "\n".join(lines).strip()


async def _resend_forward_body(bot: Bot, event: MessageEvent, forward_id: str) -> bool:
    try:
        response: dict[str, Any] = await bot.call_api(
            "get_forward_msg", message_id=forward_id
        )
    except Exception as e:
        logger.error(f"获取合并转发本体失败: {e}", "撤回记录")
        return False

    messages = response.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return False

    nodes = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        sender = msg.get("sender", {})
        if isinstance(sender, dict):
            user_id = sender.get("user_id") or msg.get("user_id") or bot.self_id
            nickname = (
                sender.get("nickname")
                or sender.get("card")
                or msg.get("nickname")
                or msg.get("name")
                or str(user_id)
            )
        else:
            user_id = msg.get("user_id") or bot.self_id
            nickname = msg.get("nickname") or msg.get("name") or str(user_id)

        content = msg.get("content")
        if not content:
            raw_message = html.unescape(str(msg.get("raw_message", "")).strip())
            content = Message(raw_message or "[空消息]")

        nodes.append(
            MessageSegment.node_custom(
                user_id=int(user_id),
                nickname=str(nickname),
                content=content,
            )
        )

    if not nodes:
        return False

    api = "send_group_forward_msg"
    kwargs: dict[str, Any] = {"messages": Message(nodes)}
    if isinstance(event, GroupMessageEvent):
        kwargs["group_id"] = event.group_id
    else:
        api = "send_private_forward_msg"
        kwargs["user_id"] = event.user_id
    await bot.call_api(api, **kwargs)
    return True


def _build_summary_message(
    grouped_records: "OrderedDict[str, list[RecallRecord]]",
    query_date: datetime | None,
) -> str:
    lines = [f"撤回摘要 (日期{_format_day(query_date)})"]
    for group_id, records in grouped_records.items():
        lines.append("")
        lines.append(f"【群 {group_id}】")
        for index, record in enumerate(records, start=1):
            user_name = record.user_name or record.user_id
            lines.append(
                f"{index}. (时间{_format_clock(record.recall_time)})-"
                f"发送者QQ({record.user_id})-({user_name})-"
                f"消息ID({record.message_id})"
            )
    return "\n".join(lines).strip()


def _build_detail_message(records: list[RecallRecord]) -> Message:
    message = Message(MessageSegment.text("撤回详情"))
    for index, record in enumerate(records, start=1):
        user_name = record.user_name or record.user_id
        operator_id = record.operator_id or record.user_id
        detail_lines = [
            "",
            "",
            f"{index}. 群号: {record.group_id}",
            f"发送者QQ: {record.user_id}",
            f"发送者昵称: {user_name}",
            f"撤回操作者QQ: {operator_id}",
            f"消息ID: {record.message_id}",
            f"原消息时间: {_format_full_datetime(record.message_time)}",
            f"撤回时间: {_format_full_datetime(record.recall_time)}",
            "消息内容:",
        ]
        message += MessageSegment.text("\n".join(detail_lines))
        message += _build_record_content_message(record)
    return message


@_record_message.handle()
async def _(event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return
    if not _is_monitored_group(event.group_id):
        return

    group_id = str(event.group_id)
    user_id = str(event.user_id)
    user_name = await _get_event_user_name(event)
    message_id = str(event.message_id)
    raw_message, plain_text = await _prepare_message_for_storage(
        event.get_message(),
        group_id=group_id,
        message_id=message_id,
    )

    await RecallRecord.upsert_message(
        group_id=group_id,
        user_id=user_id,
        user_name=user_name,
        message_id=message_id,
        raw_message=raw_message,
        plain_text=plain_text,
        message_time=_to_datetime(getattr(event, "time", None)),
        bot_id=str(event.self_id),
        platform="qq",
    )


@_record_recall.handle()
async def _(event: GroupRecallNoticeEvent):
    if not _is_monitored_group(event.group_id):
        return

    group_id = str(event.group_id)
    user_id = str(event.user_id)
    operator_id = str(event.operator_id) if event.operator_id is not None else None
    user_name = await _get_group_user_name(user_id, group_id)
    message_id = str(event.message_id)
    recall_time = _to_datetime(getattr(event, "time", None))

    if record := await RecallRecord.get_or_none(group_id=group_id, message_id=message_id):
        await _refresh_record_cached_images(record)

    await RecallRecord.mark_recalled(
        group_id=group_id,
        user_id=user_id,
        user_name=user_name,
        message_id=message_id,
        operator_id=operator_id,
        recall_time=recall_time,
        bot_id=str(event.self_id),
        platform="qq",
    )
    logger.info(
        f"记录撤回消息 group={group_id} user={user_id} operator={operator_id} "
        f"message_id={message_id}",
        "撤回记录",
        session=user_id,
        group_id=group_id,
    )


@_query_recall.handle()
async def _(bot: Bot, event: MessageEvent):
    if not _MONITORED_GROUP_SET:
        await _query_recall.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("撤回记录插件未配置监控群号。")
            )
        )

    group_id, query_date, message_id = _parse_query_args(
        event.get_message().extract_plain_text().strip()
    )

    if message_id:
        records = await RecallRecord.get_recalled_by_message_id(
            message_id=message_id,
            group_id=group_id,
        )
        if not records:
            await _query_recall.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text("未找到对应的撤回内容。")
                )
            )
        logger.info(
            f"查询撤回详情 group={group_id or 'all'} message_id={message_id}",
            "撤回记录",
            session=event.user_id,
            group_id=getattr(event, "group_id", None),
        )
        detail_message = Message(MessageSegment.reply(event.message_id))
        detail_message += _build_detail_message(records)
        await _query_recall.send(detail_message)
        for record in records:
            if forward_id := _extract_forward_id(record.raw_message or record.plain_text):
                if not await _resend_forward_body(bot, event, forward_id):
                    if forward_detail := await _build_forward_detail_text(bot, forward_id):
                        await _query_recall.send(
                            Message(MessageSegment.text(forward_detail))
                        )
        await _query_recall.finish()

    start_time, end_time = _get_date_scope(query_date)
    grouped_records: OrderedDict[str, list[RecallRecord]] = OrderedDict()

    if group_id:
        records = await RecallRecord.get_recalled_by_date(
            group_id=group_id,
            start_time=start_time,
            end_time=end_time,
        )
        if records:
            grouped_records[group_id] = records
    else:
        for current_group_id in _MONITORED_GROUP_SET:
            records = await RecallRecord.get_recalled_by_date(
                group_id=current_group_id,
                start_time=start_time,
                end_time=end_time,
            )
            if records:
                grouped_records[current_group_id] = records

    if not grouped_records:
        await _query_recall.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"日期 {_format_day(start_time)} 暂无撤回记录。")
            )
        )

    logger.info(
        f"查询撤回摘要 group={group_id or 'all'} date={_format_day(start_time)}",
        "撤回记录",
        session=event.user_id,
        group_id=getattr(event, "group_id", None),
    )
    await _query_recall.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(_build_summary_message(grouped_records, start_time))
        )
    )
