from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..utils import (contains_bilibili_url, extract_bilibili_card_info,
                     extract_bilibili_url, resolve_bilibili_video_id)
from . import build_dup_reply, check_or_store


def make_video_sha(video_id: str) -> str:
    return f"bilibili_video_{video_id}"


async def check_and_store_video(
    event: MessageEvent,
    group_id: str,
    video_id: str,
    video_title: str,
    message_id: str,
    sender_id: str,
) -> Message | None:
    """查库并返回重复提示消息，如果没有重复则存储并返回 None。"""
    sha = make_video_sha(video_id)
    result = await check_or_store(sha, group_id, message_id, sender_id)
    if result.is_dup:
        return build_dup_reply(
            result, event.user_id,
            f"视频《{video_title}》在{result.time_diff_str}就有人发过了喵（第{result.hit_count}次发了捏）",
        )
    else:
        logger.info(
            f"已存储B站视频 {message_id} video_id={video_id} group={group_id} sender={sender_id}",
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
    sender_id = str(event.user_id)

    # 1. 检查 JSON 卡片
    card_info = await extract_bilibili_card_info(message)
    if card_info:
        reply = await check_and_store_video(
            event, group_id, card_info["video_id"], card_info["title"], message_id, sender_id
        )
        return reply if reply else True

    # 2. 检查文本链接（只取纯文本段，跳过图片/媒体等）
    text_parts = [seg.data.get("text", "") for seg in message if seg.type == "text"]
    raw_text = "".join(text_parts)
    if contains_bilibili_url(raw_text):
        bili_url = extract_bilibili_url(raw_text)
        if bili_url:
            info = await resolve_bilibili_video_id(bili_url)
            if info:
                reply = await check_and_store_video(
                    event, group_id, info["video_id"], info["title"], message_id, sender_id
                )
                return reply if reply else True

    return False
