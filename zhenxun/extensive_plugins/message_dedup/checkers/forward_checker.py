from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..utils import get_forward_fingerprint
from . import build_dup_reply, check_or_store


async def check_forward(
    event: MessageEvent, session: Uninfo, bot: Bot, message: Message
) -> Message | bool:
    """检查转发消息是否重复。
    返回 Message 表示有重复需要发送，True 表示已处理无重复，False 表示不是转发消息。

    指纹方案：取每条子消息的 (time, real_seq) 拼接后 SHA-256。
    这两个字段跨群转发时完全一致，单条子消息额外加入 user_id 和 group_id。
    """
    if not any(seg.type == "forward" for seg in message):
        return False

    group_id = str(session.group.id)
    message_id = str(event.message_id)
    sender_id = str(event.user_id)

    forward_message_id = message[0].data.get("id")
    sha256 = await get_forward_fingerprint(forward_message_id, bot)
    if not sha256:
        logger.debug(
            f"转发消息 {forward_message_id} 无法生成指纹，跳过查重",
            "message_dedup",
        )
        return True

    result = await check_or_store(sha256, group_id, message_id, sender_id)
    if result.is_dup:
        return build_dup_reply(
            result, event.user_id,
            f"在{result.time_diff_str}就有人发过了喵（第{result.hit_count}次发了捏）",
        )
    else:
        logger.info(
            f"已存储转发消息 {message_id} sha256={sha256} group={group_id} sender={sender_id}",
            "message_dedup",
        )
    return True
