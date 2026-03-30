from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..db import (AsyncSessionLocal, find_existing_message,
                  increment_hit_count, store_message)
from ..utils import (build_reply_image_seg, get_forward_fingerprint,
                     get_time_diff_str)


async def check_forward(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查转发消息是否重复。
    返回 Message 表示有重复需要发送，True 表示已处理无重复，False 表示不是转发消息。

    指纹方案：取每条子消息的 (time, real_seq) 拼接后 SHA-256。
    这两个字段跨群转发时完全一致，至少需要 2 条子消息。
    """
    if not any(seg.type == "forward" for seg in message):
        return False

    group_id = str(session.group.id)
    message_id = str(event.message_id)

    forward_message_id = message[0].data.get("id")
    sha256 = await get_forward_fingerprint(forward_message_id, bot)
    if not sha256:
        logger.debug(
            f"转发消息 {forward_message_id} 无法生成指纹，跳过查重",
            "message_dedup",
        )
        return True  # 无法生成指纹，跳过但不阻断

    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha256, group_id)
        if existing:
            count = await increment_hit_count(db, existing)
            diff = get_time_diff_str(existing.timestamp)
            reply = Message(
                MessageSegment.reply(existing.message_id)
                + MessageSegment.at(event.user_id)
                + MessageSegment.text(f"在{diff}就有人发过了喵（第{count}次发了捏）")
                + build_reply_image_seg()
            )
            return reply
        else:
            await store_message(db, message_id, sha256, group_id)
            logger.info(
                f"已存储转发消息 {message_id} sha256={sha256} group={group_id}",
                "message_dedup",
            )
    return True
