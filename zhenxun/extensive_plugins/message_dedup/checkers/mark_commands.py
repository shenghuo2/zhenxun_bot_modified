import asyncio

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot.permission import SUPERUSER
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from ..config import get_cfg
from ..db import (AsyncSessionLocal, delete_message_record,
                  find_existing_message, find_message_by_id,
                  increment_hit_count, store_message)
from ..utils import (build_reply_image_seg, compute_sha256,
                     contains_bilibili_url, extract_bilibili_card_info,
                     extract_bilibili_url, get_time_diff_str, int_to_datetime,
                     resolve_bilibili_video_id)

# ── 辅助：发送后自动撤回 ─────────────────────────────────

async def _send_and_recall(matcher, bot: Bot, text: str, delay: int = 5):
    result = await matcher.send(text)
    msg_id = (
        result.get("message_id") if isinstance(result, dict) else getattr(result, "message_id", None)
    )
    if msg_id:
        await asyncio.sleep(delay)
        try:
            await bot.delete_msg(message_id=msg_id)
        except Exception:
            pass


# ── #标记 ────────────────────────────────────────────────

mark_cmd = on_command("#标记", priority=5, block=True)


@mark_cmd.handle()
async def handle_mark(event: MessageEvent, bot: Bot, session: Uninfo):
    if not get_cfg("ENABLE_MARK_COMMAND"):
        return

    if not session.group:
        await mark_cmd.finish("该命令仅限群聊使用")
        return

    if not event.reply:
        await mark_cmd.finish(f"该命令需要回复一条消息,杂鱼{session.user.nickname}！")
        return

    group_id = str(session.group.id)
    replied_id = str(event.reply.message_id)
    original_message: Message = event.reply.message
    original_raw = event.reply.raw_message
    reply_ts = int_to_datetime(event.reply.time)

    # ── 1. 尝试 B站视频卡片 ──
    card_info = await extract_bilibili_card_info(original_message)
    if card_info:
        video_id = card_info["video_id"]
        video_title = card_info["title"]
        sha = f"bilibili_video_{video_id}"
        async with AsyncSessionLocal() as db:
            existing = await find_existing_message(db, sha, group_id)
            if existing:
                count = await increment_hit_count(db, existing)
                diff = get_time_diff_str(existing.timestamp)
                await mark_cmd.finish(
                    Message(
                        MessageSegment.reply(existing.message_id)
                        + MessageSegment.text(
                            f"视频《{video_title}》在{diff}就有人标记过了，还标记，杂鱼~（第{count}次发了捏）"
                        )
                        + build_reply_image_seg()
                    )
                )
            else:
                await store_message(db, replied_id, sha, group_id, timestamp=reply_ts)
                await _send_and_recall(mark_cmd, bot, f"视频《{video_title}》标记成功，五秒后撤回本消息~")
                await mark_cmd.finish()
        return

    # ── 2. 尝试 B站文本链接 ──
    if contains_bilibili_url(original_raw):
        bili_url = extract_bilibili_url(original_raw)
        if bili_url:
            info = await resolve_bilibili_video_id(bili_url)
            if info:
                video_id = info["video_id"]
                video_title = info["title"]
                sha = f"bilibili_video_{video_id}"
                async with AsyncSessionLocal() as db:
                    existing = await find_existing_message(db, sha, group_id)
                    if existing:
                        count = await increment_hit_count(db, existing)
                        diff = get_time_diff_str(existing.timestamp)
                        await mark_cmd.finish(
                            Message(
                                MessageSegment.reply(existing.message_id)
                                + MessageSegment.text(
                                    f"视频《{video_title}》在{diff}就有人标记过了，还标记，杂鱼~（第{count}次发了捏）"
                                )
                                + build_reply_image_seg()
                            )
                        )
                    else:
                        await store_message(db, replied_id, sha, group_id, timestamp=reply_ts)
                        await _send_and_recall(
                            mark_cmd, bot, f"视频《{video_title}》标记成功，五秒后撤回本消息~"
                        )
                        await mark_cmd.finish()
                return

    # ── 3. 图片标记 ──
    parts = []
    for seg in original_message:
        if seg.data.get("summary"):
            await mark_cmd.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text("哪来的神人给表情包打标记...")
                )
            )
            return
        if seg.type == "image":
            fu = seg.data.get("file_unique")
            if fu:
                parts.append(fu)

    if not parts:
        await mark_cmd.finish("没有检测到图片或视频消息，杂鱼♥")
        return

    concatenated = "+".join(parts)
    sha = compute_sha256(concatenated)
    logger.info(f"标记 拼接后的消息: {concatenated}", "message_dedup", session=session)

    async with AsyncSessionLocal() as db:
        existing = await find_existing_message(db, sha, group_id)
        if existing:
            count = await increment_hit_count(db, existing)
            diff = get_time_diff_str(existing.timestamp)
            await mark_cmd.finish(
                Message(
                    MessageSegment.reply(existing.message_id)
                    + MessageSegment.text(f"该图片在{diff}就有人标记过了，还标记，杂鱼~（第{count}次发了捏）")
                    + build_reply_image_seg()
                )
            )
        else:
            await store_message(db, replied_id, sha, group_id, timestamp=reply_ts)
            await _send_and_recall(mark_cmd, bot, "标记成功，五秒后撤回本消息~")
            await mark_cmd.finish()


# ── #删除标记 ────────────────────────────────────────────

delete_mark_cmd = on_command("#删除标记", priority=5, block=True, permission=SUPERUSER)


@delete_mark_cmd.handle()
async def handle_delete_mark(event: MessageEvent, bot: Bot):
    if not get_cfg("ENABLE_MARK_COMMAND"):
        return

    if not event.reply:
        await delete_mark_cmd.finish("该命令需要回复一条消息。")
        return

    replied_id = str(event.reply.message_id)
    async with AsyncSessionLocal() as db:
        deleted = await delete_message_record(db, replied_id)
        if deleted:
            await _send_and_recall(delete_mark_cmd, bot, "消息标记已删除！")
        else:
            await delete_mark_cmd.finish("未找到该消息的标记记录。")
