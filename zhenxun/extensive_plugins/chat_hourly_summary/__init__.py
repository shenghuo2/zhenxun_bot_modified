from __future__ import annotations

import asyncio
import base64
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from nonebot import get_bots, on_command, on_message, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, PrivateMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.models.chat_history import ChatHistory
from zhenxun.models.group_info import GroupInfo
from zhenxun.models.group_member_info import GroupInfoUser
from zhenxun.services.log import logger
from zhenxun.utils.enum import PluginType

from .db import (
    delete_day_summaries,
    get_admin_subscriptions,
    get_day_summaries,
    get_enabled_subscriptions,
    get_hourly_images,
    get_hourly_summary,
    get_subscription,
    init_db,
    save_hourly_images,
    save_hourly_summary,
    set_last_pushed_hour,
    update_hourly_image_summary,
    update_subscription_group_name,
    enable_subscription,
    disable_subscription,
)
from .config import API_BASE, API_KEY

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name="群聊小时总结",
    description="基于 chat_history 表按小时总结群聊内容，按管理员私聊订阅推送",
    usage="""
    私聊机器人使用：
    #开启群聊总结 <群号>
    #关闭群聊总结 <群号>
    #查看群聊总结
    #查看群聊总结 <群号>
    #清理群聊总结缓存 <群号> [日期]
    #补发群聊总结 <群号> [日期]
    #立即群聊总结
    """.strip(),
    extra=PluginExtraData(
        author="Codex",
        version="0.2.0",
        plugin_type=PluginType.HIDDEN,
        commands=[
            Command(command="#开启群聊总结 <群号>"),
            Command(command="#关闭群聊总结 <群号>"),
            Command(command="#查看群聊总结 [群号]"),
            Command(command="#清理群聊总结缓存 <群号> [日期]"),
            Command(command="#补发群聊总结 <群号> [日期]"),
            Command(command="#立即群聊总结"),
        ],
    ).to_dict(),
)

DEFAULT_MODEL = "gpt-5.4-mini"
IMAGE_MODEL = "gpt-5.4"
REQUEST_TIMEOUT = 90.0
CONNECT_TIMEOUT = 15.0
READ_TIMEOUT = 90.0
MAX_SAMPLE_MESSAGES = 80
MAX_PLAIN_TEXT_CHARS = 6000
DISPLAY_TZ = ZoneInfo("Asia/Shanghai")
UTC_TZ = timezone.utc
REPLAY_AI_CONCURRENCY = 3
MAX_PRIVATE_MESSAGE_CHARS = 1500
SUBSCRIPTION_PUSH_HOURS = 3
IMAGE_AI_CONCURRENCY = 3
MAX_IMAGE_SUMMARY_IMAGES = 9
MAX_IMAGE_ANALYSIS_CHARS = 60
IMAGE_DOWNLOAD_TIMEOUT = 20.0

ENABLE_COMMANDS = ("#开启群聊总结", "#开启小时总结")
DISABLE_COMMANDS = ("#关闭群聊总结", "#关闭小时总结")
STATUS_COMMANDS = ("#查看群聊总结", "#查看小时总结")
REPLAY_COMMANDS = ("#补发群聊总结", "#补发小时总结")
CLEAR_CACHE_COMMANDS = ("#清理群聊总结缓存", "#清理小时总结缓存", "#删除群聊总结缓存")
MANUAL_COMMANDS = ("#立即群聊总结", "#手动群聊总结")

ENABLE_COMMAND_PATTERNS = (r"^#\s*开\s*启(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结(?:\s+|$)",)
DISABLE_COMMAND_PATTERNS = (r"^#\s*关\s*闭(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结(?:\s+|$)",)
STATUS_COMMAND_PATTERNS = (r"^#\s*查\s*看(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结(?:\s+|$)",)
REPLAY_COMMAND_PATTERNS = (r"^#\s*补\s*发(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结(?:\s+|$)",)
CLEAR_CACHE_COMMAND_PATTERNS = (
    r"^#\s*清\s*理(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结\s*缓\s*存(?:\s+|$)",
    r"^#\s*删\s*除(?:\s*群\s*聊|\s*小\s*时)?\s*总\s*结\s*缓\s*存(?:\s+|$)",
)

_enable_matcher = on_command(
    ENABLE_COMMANDS[0],
    aliases=set(ENABLE_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_disable_matcher = on_command(
    DISABLE_COMMANDS[0],
    aliases=set(DISABLE_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_status_matcher = on_command(
    STATUS_COMMANDS[0],
    aliases=set(STATUS_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_replay_matcher = on_command(
    REPLAY_COMMANDS[0],
    aliases=set(REPLAY_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_clear_cache_matcher = on_command(
    CLEAR_CACHE_COMMANDS[0],
    aliases=set(CLEAR_CACHE_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_manual_matcher = on_command(
    MANUAL_COMMANDS[0],
    aliases=set(MANUAL_COMMANDS[1:]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)
_private_fallback_matcher = on_message(priority=10, block=False, permission=SUPERUSER)
_image_collect_matcher = on_message(priority=2, block=False)

_image_analysis_tasks: dict[int, asyncio.Task[str | None]] = {}
_image_analysis_semaphore = asyncio.Semaphore(IMAGE_AI_CONCURRENCY)


def _pick_bot() -> Bot | None:
    bots = get_bots()
    if not bots:
        return None
    return next(iter(bots.values()))


def _local_now() -> datetime:
    return datetime.now(DISPLAY_TZ)


def _hour_window(base_time: datetime | None = None) -> tuple[datetime, datetime]:
    current = base_time or _local_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=DISPLAY_TZ)
    else:
        current = current.astimezone(DISPLAY_TZ)
    end = current.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    return start, end


def _to_display_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    return value.astimezone(DISPLAY_TZ)


def _to_local_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=DISPLAY_TZ)
    return value.astimezone(DISPLAY_TZ)


def _to_query_time(value: datetime) -> datetime:
    local_time = _to_local_time(value)
    return local_time.astimezone(UTC_TZ)


def _format_hour_label(start_time: datetime, end_time: datetime) -> str:
    local_start = _to_local_time(start_time)
    local_end = _to_local_time(end_time)
    return f"{local_start:%Y-%m-%d %H}:00-{local_end:%H}:00"


def _format_compact_hour_label(start_time: datetime, end_time: datetime) -> str:
    local_start = _to_local_time(start_time)
    local_end = _to_local_time(end_time)
    return f"{local_start:%H}:00-{local_end:%H}:00"


def _to_iso_hour(value: datetime) -> str:
    local_time = _to_local_time(value).replace(minute=0, second=0, microsecond=0)
    return local_time.replace(tzinfo=None).isoformat(sep=" ")


def _parse_date_arg(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    now = _local_now()

    natural_map = {
        "今天": 0,
        "本日": 0,
        "昨日": 1,
        "昨天": 1,
        "前天": 2,
    }
    if text in natural_map:
        return (now - timedelta(days=natural_map[text])).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=DISPLAY_TZ)
        except ValueError:
            continue

    for fmt in ("%m-%d", "%m/%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(year=now.year, tzinfo=DISPLAY_TZ)
        except ValueError:
            continue

    for fmt in ("%Y年%m月%d日", "%Y年%m月%d号", "%m月%d日", "%m月%d号"):
        try:
            parsed = datetime.strptime(text, fmt)
            if "%Y" not in fmt:
                parsed = parsed.replace(year=now.year)
            parsed = parsed.replace(tzinfo=DISPLAY_TZ)
            return parsed
        except ValueError:
            continue

    return None


def _extract_args_after_command(plain_text: str, command_name: str) -> list[str] | None:
    pattern = r"^\s*" + r"\s*".join(re.escape(char) for char in command_name) + r"(?:\s+|$)(?P<args>.*)"
    match = re.match(pattern, plain_text, flags=re.S)
    if not match:
        return None
    args_text = match.group("args").strip()
    return [item for item in args_text.split() if item]


def _match_command_args(message: MessageEvent, command_names: tuple[str, ...]) -> list[str] | None:
    plain_text = message.get_message().extract_plain_text()
    tokens = [item for item in plain_text.strip().split() if item]
    for command_name in command_names:
        result = _extract_args_after_command(plain_text, command_name)
        if result is not None:
            return result

        if not tokens:
            continue

        merged = ""
        for index, token in enumerate(tokens):
            merged += token
            if merged == command_name:
                return tokens[index + 1 :]
            if not command_name.startswith(merged):
                break
    return None


def _match_command_args_by_patterns(
    message: MessageEvent,
    patterns: tuple[str, ...],
) -> list[str] | None:
    plain_text = message.get_message().extract_plain_text()
    for pattern in patterns:
        match = re.match(pattern, plain_text, flags=re.S)
        if not match:
            continue
        args_text = plain_text[match.end():].strip()
        return [item for item in args_text.split() if item]
    return None


def _split_command_args(
    message: MessageEvent,
    command_name: str,
    aliases: tuple[str, ...] = (),
) -> list[str]:
    if args := _match_command_args(message, (command_name, *aliases)):
        return args

    tokens = [item for item in message.get_message().extract_plain_text().strip().split() if item]
    if not tokens:
        return []
    return tokens[1:]


def _chunk_lines(lines: list[str], max_chars: int = MAX_PRIVATE_MESSAGE_CHARS) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in lines:
        part = line.strip()
        if not part:
            continue
        candidate = f"{current}\n\n{part}" if current else part
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(part) <= max_chars:
            current = part
            continue

        start = 0
        while start < len(part):
            chunks.append(part[start:start + max_chars])
            start += max_chars

    if current:
        chunks.append(current)
    return chunks


async def _finish_in_chunks(matcher, lines: list[str]) -> None:
    chunks = _chunk_lines(lines)
    if not chunks:
        await matcher.finish("无可发送内容")

    for chunk in chunks[:-1]:
        await matcher.send(chunk)
    await matcher.finish(chunks[-1])


def _is_sticker_image(segment) -> bool:
    summary = str(segment.data.get("summary") or "").strip()
    sub_type = str(segment.data.get("subType") or segment.data.get("sub_type") or "").strip().lower()
    if summary:
        return True
    return sub_type in {"1", "face", "mface", "emoji", "sticker"}


def _extract_non_sticker_images(event: GroupMessageEvent) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    hour_start = _to_iso_hour(_local_now())
    message_time = _local_now().replace(tzinfo=None).isoformat(sep=" ")
    sender_name = str(
        getattr(getattr(event, "sender", None), "card", "")
        or getattr(getattr(event, "sender", None), "nickname", "")
        or event.user_id
    )

    for segment in event.message:
        if segment.type != "image":
            continue
        if _is_sticker_image(segment):
            continue
        image_url = str(segment.data.get("url") or segment.data.get("file") or "").strip()
        if not image_url:
            continue
        rows.append(
            {
                "group_id": str(event.group_id),
                "hour_start": hour_start,
                "create_time": message_time,
                "user_id": str(event.user_id),
                "sender_name": sender_name,
                "image_url": image_url,
                "file_unique": str(segment.data.get("file_unique") or "").strip(),
            }
        )
    return rows


async def _collect_hourly_images(event: GroupMessageEvent):
    rows = _extract_non_sticker_images(event)
    if not rows:
        return []
    return await save_hourly_images(rows=rows)


def _extract_cached_image_summary(row) -> str | None:
    summary = _compress_image_summary(str(row["image_summary"] or ""))
    return summary or None


async def _analyze_image_row(row) -> str | None:
    if cached_summary := _extract_cached_image_summary(row):
        return cached_summary

    image_url = str(row["image_url"] or "").strip()
    if not image_url:
        return None
    sender_name = str(row["sender_name"] or row["user_id"] or "未知")

    async with _image_analysis_semaphore:
        image_data_url = await _download_image_base64(image_url)
        if not image_data_url:
            return None
        try:
            summary = await _call_image_summary_api(
                image_data_url=image_data_url,
                sender_name=sender_name,
            )
        except Exception as e:
            logger.warning(
                f"图片实时总结失败 group={row['group_id']}, hour={row['hour_start']}: {e}",
                "群聊总结",
            )
            return None

    summary = _compress_image_summary(summary)
    if not summary:
        return None
    await update_hourly_image_summary(image_id=int(row["id"]), image_summary=summary)
    return summary


def _schedule_image_analysis(row) -> asyncio.Task[str | None]:
    image_id = int(row["id"])
    task = _image_analysis_tasks.get(image_id)
    if task and not task.done():
        return task

    task = asyncio.create_task(_analyze_image_row(row))
    _image_analysis_tasks[image_id] = task

    def _cleanup(done_task: asyncio.Task[str | None]) -> None:
        current = _image_analysis_tasks.get(image_id)
        if current is done_task:
            _image_analysis_tasks.pop(image_id, None)
        try:
            done_task.result()
        except Exception as e:
            logger.warning(f"图片分析任务异常 image_id={image_id}: {e}", "群聊总结")

    task.add_done_callback(_cleanup)
    return task


async def _ensure_image_summary(row) -> str | None:
    if cached_summary := _extract_cached_image_summary(row):
        return cached_summary
    try:
        return await _schedule_image_analysis(row)
    except Exception as e:
        logger.warning(f"图片分析补偿失败 image_id={row['id']}: {e}", "群聊总结")
        return None


async def _get_group_name(group_id: str) -> str:
    if group := await GroupInfo.get_or_none(group_id=group_id):
        if group.group_name.strip():
            return group.group_name.strip()
    return group_id


def _count_images(records: list[ChatHistory]) -> int:
    return sum((record.text or "").count("[image]") for record in records)


def _count_marker(records: list[ChatHistory], marker: str) -> int:
    return sum((record.text or "").count(marker) for record in records)


async def _get_group_member_name_map(group_id: str, user_ids: list[str]) -> dict[str, str]:
    if not user_ids:
        return {}

    rows = await GroupInfoUser.filter(
        group_id=group_id,
        user_id__in=list(set(user_ids)),
    ).values("user_id", "nickname", "user_name")

    result: dict[str, str] = {}
    for row in rows:
        user_id = str(row.get("user_id", "")).strip()
        if not user_id:
            continue
        display_name = (
            str(row.get("nickname") or "").strip()
            or str(row.get("user_name") or "").strip()
            or user_id
        )
        result[user_id] = display_name
    return result


def _top_speakers(
    records: list[ChatHistory],
    name_map: dict[str, str],
    limit: int = 5,
) -> list[tuple[str, int]]:
    counter = Counter(record.user_id for record in records if record.user_id)
    return [
        (name_map.get(user_id, user_id), count)
        for user_id, count in counter.most_common(limit)
    ]


def _pick_plain_text_samples(
    records: list[ChatHistory],
    name_map: dict[str, str],
) -> list[str]:
    samples: list[str] = []
    total_chars = 0
    for record in records:
        plain_text = (record.plain_text or "").strip()
        if not plain_text:
            continue
        sender_name = name_map.get(record.user_id, record.user_id)
        line = f"[{_to_display_time(record.create_time):%H:%M}] {sender_name}: {plain_text}"
        if total_chars + len(line) > MAX_PLAIN_TEXT_CHARS:
            break
        samples.append(line)
        total_chars += len(line)
        if len(samples) >= MAX_SAMPLE_MESSAGES:
            break
    return samples


def _build_prompt(
    *,
    group_name: str,
    start_time: datetime,
    end_time: datetime,
    message_count: int,
    image_count: int,
    record_count: int,
    at_count: int,
    reply_count: int,
    reference_count: int,
    speakers: list[tuple[str, int]],
    samples: list[str],
) -> str:
    speaker_text = "、".join(f"{uid}({count}条)" for uid, count in speakers) or "无"
    sample_text = "\n".join(samples) if samples else "本小时没有可用的纯文本样本。"
    return (
        "请根据以下群聊统计和聊天样本，输出中文总结。\n"
        "要求：\n"
        "1. 控制在80字以内，像管理员看的摘要，不要客套。\n"
        "2. 优先总结谁在说什么，谁在@谁，主要在讨论什么。\n"
        "3. 样本不足时明确说信息不足，不要编造。\n"
        "4. 不要重复统计数字，不要加标题，不要出现群名和时间。\n"
        "5. 输出成一句紧凑中文。\n\n"
        f"群名: {group_name}\n"
        f"时间范围: {_format_hour_label(start_time, end_time)}\n"
        f"消息数: {message_count}\n"
        f"图片数: {image_count}\n"
        f"聊天记录数: {record_count}\n"
        f"At次数: {at_count}\n"
        f"Reply次数: {reply_count}\n"
        f"Reference次数: {reference_count}\n"
        f"活跃用户: {speaker_text}\n"
        "聊天样本:\n"
        f"{sample_text}"
    )


async def _download_image_base64(image_url: str) -> str | None:
    timeout = httpx.Timeout(timeout=IMAGE_DOWNLOAD_TIMEOUT, connect=10.0, read=IMAGE_DOWNLOAD_TIMEOUT)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(image_url)
            response.raise_for_status()
    except Exception:
        return None

    content_type = str(response.headers.get("content-type") or "image/jpeg").split(";", 1)[0].strip() or "image/jpeg"
    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


async def _call_image_summary_api(*, image_data_url: str, sender_name: str) -> str:
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": IMAGE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是群聊图片分析助手，只输出精炼中文结论，不输出多余说明。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _build_image_summary_prompt(sender_name)},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        "temperature": 0.2,
    }

    timeout = httpx.Timeout(
        timeout=REQUEST_TIMEOUT,
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.ConnectTimeout as e:
        raise RuntimeError(f"AI接口连接超时(connect>{CONNECT_TIMEOUT}s)") from e
    except httpx.ReadTimeout as e:
        raise RuntimeError(f"AI接口响应超时(read>{READ_TIMEOUT}s)") from e

    if response.status_code != 200:
        body = response.text.strip()[:500]
        raise RuntimeError(f"AI接口请求失败(status={response.status_code}): {body}")

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        snippet = response.text.strip()[:500]
        raise RuntimeError(f"AI接口返回非JSON: {snippet}") from e

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"AI接口返回结构异常: {data}")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
    return str(content).strip()


def _compress_image_summary(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" ，。；;\n\t")
    if len(text) > MAX_IMAGE_ANALYSIS_CHARS:
        text = text[: MAX_IMAGE_ANALYSIS_CHARS].rstrip(" ，。；;")
    return text


async def _build_hour_image_summary(*, group_id: str, start_time: datetime) -> str | None:
    rows = await get_hourly_images(group_id=group_id, hour_start=_to_iso_hour(start_time))
    if not rows:
        return None

    deduped_rows = []
    seen: set[str] = set()
    for row in rows:
        dedupe_key = str(row["file_unique"] or row["image_url"]).strip()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_rows.append(row)
        if len(deduped_rows) >= MAX_IMAGE_SUMMARY_IMAGES:
            break

    if not deduped_rows:
        return None

    results = await asyncio.gather(*(_ensure_image_summary(row) for row in deduped_rows))
    valid: list[str] = []
    for row, summary in zip(deduped_rows, results):
        if not summary:
            continue
        sender_name = str(row["sender_name"] or row["user_id"] or "未知")
        valid.append(f"{sender_name}发图: {summary}")
    if not valid:
        return None
    return "图片补充: " + "；".join(valid[:3])


def _build_image_summary_prompt(sender_name: str) -> str:
    return (
        "请直接识别这张群聊图片，并输出一句不超过"
        f"{MAX_IMAGE_ANALYSIS_CHARS}字的中文摘要。"
        "只描述主要画面或截图内容，不要客套，不要猜测过度。"
        f"发送者: {sender_name or '未知'}。"
    )


async def _call_summary_api(prompt: str) -> str:
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是群聊内容分析助手，只输出精炼中文总结，不输出多余说明。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    timeout = httpx.Timeout(
        timeout=REQUEST_TIMEOUT,
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.ConnectTimeout as e:
        raise RuntimeError(f"AI接口连接超时(connect>{CONNECT_TIMEOUT}s)") from e
    except httpx.ReadTimeout as e:
        raise RuntimeError(f"AI接口响应超时(read>{READ_TIMEOUT}s)") from e

    if response.status_code != 200:
        body = response.text.strip()[:500]
        raise RuntimeError(f"AI接口请求失败(status={response.status_code}): {body}")

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        snippet = response.text.strip()[:500]
        raise RuntimeError(f"AI接口返回非JSON: {snippet}") from e

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"AI接口返回结构异常: {data}")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        content = "".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        )
    content = str(content).strip()
    if not content:
        raise RuntimeError("AI接口返回空内容")
    return content


async def _build_or_load_summary(
    *,
    group_id: str,
    group_name: str,
    start_time: datetime,
    end_time: datetime,
) -> tuple[str | None, int, int]:
    hour_start = _to_iso_hour(start_time)
    existing = await get_hourly_summary(group_id=group_id, hour_start=hour_start)
    if existing:
        return existing["summary_text"], existing["message_count"], existing["image_count"]

    query_start = _to_query_time(start_time)
    query_end = _to_query_time(end_time)
    records = await ChatHistory.filter(
        group_id=group_id,
        create_time__gte=query_start,
        create_time__lt=query_end,
    ).order_by("create_time")
    if not records:
        return None, 0, 0

    name_map = await _get_group_member_name_map(
        group_id,
        [record.user_id for record in records if record.user_id],
    )
    message_count = len(records)
    image_count = _count_images(records)
    at_count = _count_marker(records, "[at]")
    reply_count = _count_marker(records, "[reply]")
    reference_count = _count_marker(records, "[reference]")
    record_count = reply_count + reference_count
    prompt = _build_prompt(
        group_name=group_name,
        start_time=start_time,
        end_time=end_time,
        message_count=message_count,
        image_count=image_count,
        record_count=record_count,
        at_count=at_count,
        reply_count=reply_count,
        reference_count=reference_count,
        speakers=_top_speakers(records, name_map),
        samples=_pick_plain_text_samples(records, name_map),
    )
    ai_summary = await _call_summary_api(prompt)
    image_summary = await _build_hour_image_summary(group_id=group_id, start_time=start_time)
    summary_text = (
        f"{_format_compact_hour_label(start_time, end_time)}，总消息/图/聊天记录为"
        f"{message_count}/{image_count}/{record_count}。{ai_summary}"
    )
    if image_summary:
        summary_text = f"{summary_text} {image_summary}"
    await save_hourly_summary(
        group_id=group_id,
        group_name=group_name,
        hour_start=hour_start,
        hour_end=_to_iso_hour(end_time),
        message_count=message_count,
        image_count=image_count,
        summary_text=summary_text,
    )
    return summary_text, message_count, image_count


def _compress_summary_text(summary_text: str, start_time: datetime, end_time: datetime) -> str:
    local_label = _format_compact_hour_label(start_time, end_time)
    if summary_text.startswith(local_label):
        return summary_text

    prefixes = [
        f"在 {_format_hour_label(start_time, end_time)}，",
        f" 在 {_format_hour_label(start_time, end_time)}，",
    ]

    compact = summary_text
    for prefix in prefixes:
        if prefix in compact:
            left, right = compact.split(prefix, 1)
            compact = right.strip()
            break
    return f"{local_label} {compact}"


async def _collect_day_summaries(
    *,
    group_id: str,
    group_name: str,
    day_start: datetime,
    day_end: datetime,
) -> list[str]:
    slots: list[tuple[datetime, datetime]] = []
    current = day_start
    while current < day_end:
        next_hour = current + timedelta(hours=1)
        slots.append((current, next_hour))
        current = next_hour

    semaphore = asyncio.Semaphore(REPLAY_AI_CONCURRENCY)

    async def _process_slot(start_time: datetime, end_time: datetime) -> tuple[datetime, str | None]:
        async with semaphore:
            summary_text, _, _ = await _build_or_load_summary(
                group_id=group_id,
                group_name=group_name,
                start_time=start_time,
                end_time=end_time,
            )
        if not summary_text:
            return start_time, None
        return start_time, _compress_summary_text(summary_text, start_time, end_time)

    results = await asyncio.gather(
        *(_process_slot(start_time, end_time) for start_time, end_time in slots)
    )
    results.sort(key=lambda item: item[0])
    return [text for _, text in results if text]


async def _push_summary_for_subscription(
    bot: Bot,
    subscription,
    *,
    start_time: datetime,
    end_time: datetime,
    force: bool = False,
) -> bool:
    hour_start = _to_iso_hour(start_time)
    if not force and subscription["last_pushed_hour"] == hour_start:
        return False

    group_id = subscription["group_id"]
    admin_user_id = subscription["admin_user_id"]
    group_name = subscription["group_name"] or await _get_group_name(group_id)
    await update_subscription_group_name(
        group_id=group_id,
        admin_user_id=admin_user_id,
        group_name=group_name,
    )

    summary_text, _, _ = await _build_or_load_summary(
        group_id=group_id,
        group_name=group_name,
        start_time=start_time,
        end_time=end_time,
    )
    await set_last_pushed_hour(
        group_id=group_id,
        admin_user_id=admin_user_id,
        hour_start=hour_start,
    )
    if not summary_text:
        return False
    await bot.send_private_msg(user_id=int(admin_user_id), message=summary_text)
    return True


async def _push_batch_summary_for_subscription(
    bot: Bot,
    subscription,
    *,
    batch_start: datetime,
    batch_end: datetime,
    force: bool = False,
) -> bool:
    batch_key = _to_iso_hour(batch_end)
    if not force and subscription["last_pushed_hour"] == batch_key:
        return False

    group_id = subscription["group_id"]
    admin_user_id = subscription["admin_user_id"]
    group_name = subscription["group_name"] or await _get_group_name(group_id)
    await update_subscription_group_name(
        group_id=group_id,
        admin_user_id=admin_user_id,
        group_name=group_name,
    )

    lines = [
        f"{group_name} { _format_hour_label(batch_start, batch_end) } 订阅总结："
    ]
    has_content = False
    current = batch_start
    while current < batch_end:
        next_hour = current + timedelta(hours=1)
        summary_text, _, _ = await _build_or_load_summary(
            group_id=group_id,
            group_name=group_name,
            start_time=current,
            end_time=next_hour,
        )
        if summary_text:
            has_content = True
            lines.append(_compress_summary_text(summary_text, current, next_hour))
        current = next_hour

    await set_last_pushed_hour(
        group_id=group_id,
        admin_user_id=admin_user_id,
        hour_start=batch_key,
    )

    if not has_content:
        return False

    chunks = _chunk_lines(lines)
    for chunk in chunks:
        await bot.send_private_msg(user_id=int(admin_user_id), message=chunk)
    return True


async def _handle_enable_command(matcher, event: PrivateMessageEvent, args: list[str]) -> None:
    if not args:
        await matcher.finish("用法: #开启群聊总结 <群号>")

    group_id = args[0]
    group_name = await _get_group_name(group_id)
    await enable_subscription(
        group_id=group_id,
        group_name=group_name,
        admin_user_id=str(event.user_id),
    )
    await matcher.finish(f"已开启群 {group_name}({group_id}) 的群聊小时总结，后续会私聊发给你")


async def _handle_disable_command(matcher, event: PrivateMessageEvent, args: list[str]) -> None:
    if not args:
        await matcher.finish("用法: #关闭群聊总结 <群号>")

    group_id = args[0]
    updated = await disable_subscription(
        group_id=group_id,
        admin_user_id=str(event.user_id),
    )
    if updated:
        await matcher.finish(f"已关闭群 {group_id} 的群聊小时总结")
    await matcher.finish(f"你当前没有订阅群 {group_id} 的群聊小时总结")


async def _handle_status_command(matcher, event: PrivateMessageEvent, args: list[str]) -> None:
    admin_user_id = str(event.user_id)

    if args:
        group_id = args[0]
        sub = await get_subscription(group_id=group_id, admin_user_id=admin_user_id)
        if not sub:
            await matcher.finish(f"你没有订阅群 {group_id} 的群聊小时总结")
        last_hour = sub["last_pushed_hour"] or "尚未推送"
        status = "开启" if sub["enabled"] else "关闭"
        await matcher.finish(
            f"群 {sub['group_name'] or group_id}({group_id}) 当前状态: {status}，最近推送小时: {last_hour}"
        )

    subs = await get_admin_subscriptions(admin_user_id)
    if not subs:
        await matcher.finish("你当前没有任何群聊小时总结订阅")

    lines = ["当前群聊小时总结订阅："]
    for sub in subs:
        status = "开启" if sub["enabled"] else "关闭"
        last_hour = sub["last_pushed_hour"] or "尚未推送"
        lines.append(
            f"{sub['group_name'] or sub['group_id']}({sub['group_id']}) | {status} | 最近推送: {last_hour}"
        )
    await matcher.finish("\n".join(lines))


async def _handle_replay_command(matcher, event: PrivateMessageEvent, args: list[str]) -> None:
    if not args:
        await matcher.finish("用法: #补发群聊总结 <群号> [日期]，日期默认今天，格式 2026-04-15")

    group_id = args[0]
    query_day = _parse_date_arg(args[1] if len(args) > 1 else None) or _local_now()
    day_start = query_day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    group_name = await _get_group_name(group_id)

    logger.info(
        f"收到群聊总结补发: user={event.user_id}, group={group_id}, date={day_start:%Y-%m-%d}, args={args}",
        "群聊总结",
    )

    try:
        stored_rows = await get_day_summaries(
            group_id=group_id,
            day_start=day_start.isoformat(sep=" "),
            day_end=day_end.isoformat(sep=" "),
        )
        logger.info(
            f"补发缓存命中: group={group_id}, date={day_start:%Y-%m-%d}, rows={len(stored_rows)}",
            "群聊总结",
        )
        if stored_rows:
            lines = [f"{group_name}({group_id}) {day_start:%Y-%m-%d} 小时总结补发："]
            for row in stored_rows:
                start_time = datetime.fromisoformat(row["hour_start"])
                end_time = datetime.fromisoformat(row["hour_end"])
                lines.append(_compress_summary_text(row["summary_text"], start_time, end_time))
            await _finish_in_chunks(matcher, lines)

        generated_lines = await _collect_day_summaries(
            group_id=group_id,
            group_name=group_name,
            day_start=day_start,
            day_end=day_end,
        )
        logger.info(
            f"补发现场生成完成: group={group_id}, date={day_start:%Y-%m-%d}, rows={len(generated_lines)}",
            "群聊总结",
        )
        if not generated_lines:
            await matcher.finish(
                f"群 {group_name}({group_id}) 在 {day_start:%Y-%m-%d} 没有可生成总结的聊天记录"
            )

        lines = [
            f"{group_name}({group_id}) {day_start:%Y-%m-%d} 小时总结补发：",
            "以下内容为现场生成，已自动写入本地小时总结库。",
        ]
        lines.extend(generated_lines)
        await _finish_in_chunks(matcher, lines)
    except Exception as e:
        logger.error(
            f"补发群聊总结失败 group={group_id}, date={day_start:%Y-%m-%d}: {e}",
            "群聊总结",
            e=e,
        )
        await matcher.finish(f"补发失败: {e}")


async def _handle_clear_cache_command(matcher, event: PrivateMessageEvent, args: list[str]) -> None:
    if not args:
        await matcher.finish("用法: #清理群聊总结缓存 <群号> [日期]，日期默认今天")

    group_id = args[0]
    query_day = _parse_date_arg(args[1] if len(args) > 1 else None) or _local_now()
    day_start = query_day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    deleted = await delete_day_summaries(
        group_id=group_id,
        day_start=day_start.isoformat(sep=" "),
        day_end=day_end.isoformat(sep=" "),
    )
    await matcher.finish(f"已清理群 {group_id} 在 {day_start:%Y-%m-%d} 的 {deleted} 条小时总结缓存")


@_image_collect_matcher.handle()
async def handle_collect_hourly_images(event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return

    try:
        inserted_rows = await _collect_hourly_images(event)
        for row in inserted_rows:
            _schedule_image_analysis(row)
    except Exception as e:
        logger.error(f"记录群聊总结图片缓存失败 group={getattr(event, 'group_id', 'unknown')}: {e}", "群聊总结", e=e)


@_enable_matcher.handle()
async def handle_enable(event: PrivateMessageEvent):
    args = _split_command_args(event, ENABLE_COMMANDS[0], ENABLE_COMMANDS[1:])
    await _handle_enable_command(_enable_matcher, event, args)


@_disable_matcher.handle()
async def handle_disable(event: PrivateMessageEvent):
    args = _split_command_args(event, DISABLE_COMMANDS[0], DISABLE_COMMANDS[1:])
    await _handle_disable_command(_disable_matcher, event, args)


@_status_matcher.handle()
async def handle_status(event: PrivateMessageEvent):
    args = _split_command_args(event, STATUS_COMMANDS[0], STATUS_COMMANDS[1:])
    await _handle_status_command(_status_matcher, event, args)


@_replay_matcher.handle()
async def handle_replay(event: PrivateMessageEvent):
    args = _split_command_args(event, REPLAY_COMMANDS[0], REPLAY_COMMANDS[1:])
    await _handle_replay_command(_replay_matcher, event, args)


@_clear_cache_matcher.handle()
async def handle_clear_cache(event: PrivateMessageEvent):
    args = _split_command_args(event, CLEAR_CACHE_COMMANDS[0], CLEAR_CACHE_COMMANDS[1:])
    await _handle_clear_cache_command(_clear_cache_matcher, event, args)


@_manual_matcher.handle()
async def handle_manual(event: MessageEvent):
    bot = _pick_bot()
    if not bot:
        await _manual_matcher.finish("当前没有可用 Bot 连接")

    start_time, end_time = _hour_window()
    subscriptions = await get_enabled_subscriptions()
    if not subscriptions:
        await _manual_matcher.finish("当前没有开启的群聊小时总结订阅")

    sent_count = 0
    batch_end = end_time
    batch_start = batch_end - timedelta(hours=SUBSCRIPTION_PUSH_HOURS)
    for subscription in subscriptions:
        try:
            if await _push_batch_summary_for_subscription(
                bot,
                subscription,
                batch_start=batch_start,
                batch_end=batch_end,
                force=True,
            ):
                sent_count += 1
        except Exception as e:
            logger.error(
                f"手动执行群聊总结失败 group={subscription['group_id']}: {e}",
                "群聊总结",
            )
    await _manual_matcher.finish(
        f"手动执行完成，时间范围 {_format_hour_label(batch_start, batch_end)}，成功发送 {sent_count} 条订阅总结"
    )


@_private_fallback_matcher.handle()
async def handle_private_command_fallback(event: MessageEvent):
    if not isinstance(event, PrivateMessageEvent):
        return

    plain_text = event.get_message().extract_plain_text().strip()
    if not plain_text.startswith("#"):
        return

    command_handlers = (
        (ENABLE_COMMANDS, ENABLE_COMMAND_PATTERNS, _handle_enable_command),
        (DISABLE_COMMANDS, DISABLE_COMMAND_PATTERNS, _handle_disable_command),
        (STATUS_COMMANDS, STATUS_COMMAND_PATTERNS, _handle_status_command),
        (REPLAY_COMMANDS, REPLAY_COMMAND_PATTERNS, _handle_replay_command),
        (CLEAR_CACHE_COMMANDS, CLEAR_CACHE_COMMAND_PATTERNS, _handle_clear_cache_command),
    )
    for command_names, patterns, handler in command_handlers:
        args = _match_command_args(event, command_names)
        if args is None:
            args = _match_command_args_by_patterns(event, patterns)
        if args is None:
            continue
        logger.info(
            f"命中群聊总结私聊兜底路由: user={event.user_id}, command={command_names[0]}, args={args}",
            "群聊总结",
        )
        await handler(_private_fallback_matcher, event, args)
        return


@scheduler.scheduled_job(
    "cron",
    minute=5,
    id="chat_hourly_summary_job",
)
async def _scheduled_chat_summary():
    bot = _pick_bot()
    if not bot:
        logger.warning("群聊总结定时任务跳过: 当前没有可用 Bot", "群聊总结")
        return

    subscriptions = await get_enabled_subscriptions()
    if not subscriptions:
        return

    current_end = _local_now().replace(minute=0, second=0, microsecond=0)
    if current_end.hour % SUBSCRIPTION_PUSH_HOURS != 0:
        return

    batch_end = current_end
    batch_start = batch_end - timedelta(hours=SUBSCRIPTION_PUSH_HOURS)
    for subscription in subscriptions:
        try:
            await _push_batch_summary_for_subscription(
                bot,
                subscription,
                batch_start=batch_start,
                batch_end=batch_end,
            )
        except Exception as e:
            logger.error(
                f"执行群聊总结失败 group={subscription['group_id']}, batch={batch_start:%Y-%m-%d %H}-{batch_end:%H}: {e}",
                "群聊总结",
            )

from nonebot import get_driver  # noqa: E402

driver = get_driver()
driver.on_startup(init_db)
