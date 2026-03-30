from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..db import AsyncSessionLocal, find_existing_message, store_message
from ..utils import (
    build_reply_image_seg,
    compute_sha256,
    extract_file_unique,
    get_time_diff_str,
)


def _is_video_or_forward(message: Message) -> bool:
    return any(seg.type in ("forward", "video") for seg in message)


async def check_video(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查普通视频消息是否重复。
    返回 Message 表示有重复需要发送，True 表示已处理无重复，False 表示非视频消息。
    """
    if not _is_video_or_forward(message):
        return False

    # 转发消息由 forward_checker 处理，这里只处理 video
    if any(seg.type == "forward" for seg in message):
        return False

    group_id = str(session.group.id)
    message_id = str(event.message_id)
    raw = event.raw_message

    sha = extract_file_unique(raw) or compute_sha256(raw)

    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha, group_id)
        if existing:
            diff = get_time_diff_str(existing.timestamp)
            return Message(
                MessageSegment.reply(existing.message_id)
                + MessageSegment.text(f"在{diff}就有人发过了喵")
                + build_reply_image_seg()
            )
        else:
            await store_message(db, message_id, sha, group_id)
            logger.info(
                f"已存储视频消息 {message_id} sha256={sha} group={group_id}",
                "message_dedup",
            )
    return True
