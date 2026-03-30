from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..db import AsyncSessionLocal, find_existing_message, store_message
from ..utils import (
    build_reply_image_seg,
    contains_bilibili_url,
    extract_bilibili_card_info,
    extract_bilibili_url,
    get_time_diff_str,
    resolve_bilibili_video_id,
)


def _make_video_sha(video_id: str) -> str:
    return f"bilibili_video_{video_id}"


async def _check_and_reply(
    event: MessageEvent,
    group_id: str,
    video_id: str,
    video_title: str,
    message_id: str,
) -> Message | None:
    """查库并返回重复提示消息，如果没有重复则存储并返回 None。"""
    sha = _make_video_sha(video_id)
    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha, group_id)
        if existing:
            diff = get_time_diff_str(existing.timestamp)
            return Message(
                MessageSegment.reply(existing.message_id)
                + MessageSegment.at(event.user_id)
                + MessageSegment.text(f"视频《{video_title}》在{diff}就有人发过了喵")
                + build_reply_image_seg()
            )
        else:
            await store_message(db, message_id, sha, group_id)
            logger.info(
                f"已存储B站视频 {message_id} video_id={video_id} group={group_id}",
                "message_dedup",
            )
            return None


async def check_bilibili(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查B站视频是否重复。
    返回 Message 表示有重复需要发送，True 表示已处理无重复，False 表示非B站消息。
    """
    group_id = str(session.group.id)
    message_id = str(event.message_id)

    # 1. 检查 JSON 卡片
    card_info = await extract_bilibili_card_info(message)
    if card_info:
        reply = await _check_and_reply(
            event, group_id, card_info["video_id"], card_info["title"], message_id
        )
        return reply if reply else True

    # 2. 检查文本链接
    raw_text = event.raw_message
    if contains_bilibili_url(raw_text):
        bili_url = extract_bilibili_url(raw_text)
        if bili_url:
            info = await resolve_bilibili_video_id(bili_url)
            if info:
                reply = await _check_and_reply(
                    event, group_id, info["video_id"], info["title"], message_id
                )
                return reply if reply else True

    return False
