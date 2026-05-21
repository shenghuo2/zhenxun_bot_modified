import datetime
from dataclasses import dataclass

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..db import (AsyncSessionLocal, find_existing_message,
                  increment_hit_count, store_message)
from ..utils import build_reply_image_seg, get_time_diff_str


@dataclass
class DupCheckResult:
    """查重结果"""
    is_dup: bool
    existing_message_id: str | None = None
    hit_count: int = 1
    time_diff_str: str | None = None
    senders: list[str] | None = None


async def check_or_store(
    sha: str,
    group_id: str,
    message_id: str,
    sender_id: str | None = None,
    timestamp: datetime.datetime | None = None,
) -> DupCheckResult:
    """核心查重/存储逻辑，返回结果供调用方自行构造回复。"""
    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha, group_id)
        if existing:
            count = await increment_hit_count(db, existing, sender_id)
            diff = get_time_diff_str(existing.timestamp)
            prev_senders = []
            if existing.sender_id:
                all_senders = existing.sender_id.split(",")
                prev_senders = all_senders[:-1] if len(all_senders) > 1 else all_senders
            return DupCheckResult(
                is_dup=True,
                existing_message_id=existing.message_id,
                hit_count=count,
                time_diff_str=diff,
                senders=prev_senders,
            )
        else:
            await store_message(db, message_id, sha, group_id, sender_id, timestamp)
            return DupCheckResult(is_dup=False)


def build_dup_reply(
    result: DupCheckResult,
    user_id: int,
    text: str,
) -> Message:
    """构造查重回复消息（含 @当前用户 + 之前发送者 + 图片）。"""
    msg = (
        MessageSegment.reply(result.existing_message_id)
        + MessageSegment.at(user_id)
        + MessageSegment.text(f" {text}")
    )
    if result.senders:
        senders_str = "、".join(result.senders)
        msg += MessageSegment.text(f"\n之前的发送者是：{senders_str}")
    msg += build_reply_image_seg()
    return Message(msg)
