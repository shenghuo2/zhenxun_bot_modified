from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..db import AsyncSessionLocal, find_existing_message, store_message
from ..utils import (build_reply_image_seg, compute_sha256,
                     get_forward_messages, get_time_diff_str)


async def check_forward(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查转发消息是否重复。
    返回 Message 表示有重复需要发送，True 表示已处理无重复，False 表示不是转发消息。
    """
    if not any(seg.type == "forward" for seg in message):
        return False

    group_id = str(session.group.id)
    message_id = str(event.message_id)

    forward_message_id = message[0].data.get("id")
    forward_messages = await get_forward_messages(forward_message_id, bot)
    concatenated = "+".join(forward_messages)
    logger.info(
        f"聊天记录 拼接后的消息: {concatenated}",
        "message_dedup",
        session=session,
    )
    sha256 = compute_sha256(concatenated)

    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha256, group_id)
        if existing:
            diff = get_time_diff_str(existing.timestamp)
            reply = Message(
                MessageSegment.reply(existing.message_id)
                + MessageSegment.at(event.user_id)
                + MessageSegment.text(f"在{diff}就有人发过了喵")
                + build_reply_image_seg()
            )
            return reply  # 返回要发送的消息
        else:
            await store_message(db, message_id, sha256, group_id)
            logger.info(
                f"已存储转发消息 {message_id} sha256={sha256} group={group_id}",
                "message_dedup",
            )
    return True  # 已处理，无重复
