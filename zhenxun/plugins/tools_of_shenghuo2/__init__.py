import html
import json

from nonebot import on_regex
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import (GroupMessageEvent, Message,
                                         MessageEvent, MessageSegment)
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Alconna, UniMessage, on_alconna
from nonebot_plugin_session import EventSession

from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

from .utils import get_deepseek_balance, is_ad_message

__plugin_meta__ = PluginMetadata(
    name="shenghuo2的工具集",
    description="实用工具集合（by shenghuo2）",
    usage="""    #deepseek余额 - 查询DeepSeek账户余额
    #获取图片 - 回复表情包消息，获取原图
    #换头像 [图片] - 更换QQ头像
    """.strip(),
    extra=PluginExtraData(
        author="shenghuo2",
        version="1.0",
    ).dict(),
)


balance_matcher = on_alconna(Alconna("#deepseek余额"), priority=5, block=True)


@balance_matcher.handle()
async def _(bot: Bot, session: EventSession):
    msg, code = await get_deepseek_balance()

    if code != 200:
        await MessageUtils.build_message(msg).finish()
        return

    result_msg = UniMessage.text(msg)
    await result_msg.send()

    logger.info("DeepSeek余额查询成功")


# 添加获取图片功能
get_image_matcher = on_alconna(Alconna("#获取图片"), priority=5, block=True)


@get_image_matcher.handle()
async def handle_get_image(bot: Bot, session: EventSession, event: MessageEvent):
    # 检查是否有回复消息
    if not event.reply:
        await get_image_matcher.finish(
            MessageSegment.text("请回复一条包含表情包的消息")
        )
        return

    # 获取被回复的消息内容
    original_message = event.reply.message

    # 检查回复的消息是否包含图片，并且是表情包
    image_found = False

    for segment in original_message:
        if segment.type == "image":
            # 检查是否为表情包
            if segment.data.get("summary"):
                image_found = True
                # 获取图片URL
                image_url = segment.data.get("url", "")

                if image_url:
                    # 发送原图
                    # logger.info("表情包原图获取成功")
                    await get_image_matcher.finish(
                        Message(
                            MessageSegment.image(image_url)
                            + MessageSegment.text(image_url)
                        )
                    )

                else:
                    await get_image_matcher.finish(
                        MessageSegment.text("获取图片URL失败")
                    )

    if not image_found:
        await get_image_matcher.finish(
            MessageSegment.text("回复的消息不包含表情包图片")
        )


# 换头像功能（仅限超级用户）
change_avatar_matcher = on_regex(
    r"^#换头像\s*", priority=5, block=True, permission=SUPERUSER
)


@change_avatar_matcher.handle()
async def handle_change_avatar(bot: Bot, event: MessageEvent):
    """处理换头像命令（仅限超级用户）"""
    # 从消息中提取图片
    image_url = None
    for segment in event.message:
        if segment.type == "image":
            image_url = segment.data.get("url", "") or segment.data.get("file", "")
            if image_url:
                break

    if not image_url:
        await change_avatar_matcher.finish("请在命令中附带图片")
        return

    try:
        # 尝试调用 set_qq_avatar API
        try:
            await bot.call_api("set_qq_avatar", file=image_url)
        except Exception:
            await bot.call_api("set_qq_avatar", url=image_url)

        await MessageUtils.build_message("头像更换成功！").send(reply_to=True)
        logger.info("QQ头像更换成功")

    except Exception as e:
        logger.error(f"QQ头像更换失败: {e}")
        await MessageUtils.build_message(f"头像更换失败: {str(e)}").send(reply_to=True)


# ============ 转发消息广告过滤（回复转发消息后发送 #广告过滤） ============


def _build_content_from_message(msg: dict) -> Message:
    """从 get_forward_msg 返回的子消息构造 Message 对象。

    关键：图片消息用 url 字段作为 file 参数，
    因为原始 file 字段只是文件名（如 xxx.jpg），NapCat 无法定位。
    """
    message_list = msg.get("message")
    if not message_list or not isinstance(message_list, list):
        raw = html.unescape(str(msg.get("raw_message", "")).strip())
        return Message(raw) if raw else Message("[空消息]")

    result = Message()
    for seg in message_list:
        seg_type = seg.get("type", "")
        seg_data = seg.get("data", {})

        if seg_type == "image":
            # 用 url 作为 file，NapCat 可以从 URL 下载图片
            url = seg_data.get("url", "")
            if url:
                result += MessageSegment.image(file=url)
            else:
                # fallback 到原始 file 字段
                result += MessageSegment.image(file=seg_data.get("file", ""))
        elif seg_type == "text":
            result += MessageSegment.text(seg_data.get("text", ""))
        elif seg_type == "face":
            result += MessageSegment("face", {"id": seg_data.get("id", "")})
        elif seg_type == "at":
            result += MessageSegment.at(seg_data.get("qq", ""))
        else:
            # 其他类型原样保留
            result += MessageSegment(seg_type, seg_data)

    return result if result else Message("[空消息]")

ad_filter_matcher = on_alconna(
    Alconna("#广告过滤"), aliases={"#去广告"}, priority=5, block=True
)


@ad_filter_matcher.handle()
async def handle_ad_filter(bot: Bot, event: MessageEvent):
    """回复一条合并转发消息，发送 #广告过滤 即可过滤其中的广告"""
    if not event.reply:
        await ad_filter_matcher.finish("请回复一条合并转发消息后再使用此命令")
        return

    # 从被回复的消息中找到转发消息的 forward id
    original_message = event.reply.message
    forward_id = None
    for seg in original_message:
        if seg.type == "forward":
            forward_id = seg.data.get("id")
            break

    if not forward_id:
        await ad_filter_matcher.finish("回复的消息不是合并转发消息")
        return

    try:
        response: dict = await bot.call_api(
            "get_forward_msg", message_id=forward_id
        )
    except Exception as e:
        logger.error(f"获取转发消息失败: {e}", "广告过滤")
        await ad_filter_matcher.finish(f"获取转发消息失败: {e}")
        return

    messages = response.get("messages", [])
    if not messages:
        await ad_filter_matcher.finish("转发消息内容为空")
        return

    # 分离广告和正常消息
    clean_msgs = []
    ad_count = 0
    for msg in messages:
        if is_ad_message(msg):
            ad_count += 1
            ad_title = ""
            for seg in msg.get("message", []):
                if seg.get("type") == "json":
                    try:
                        card = json.loads(seg.get("data", {}).get("data", ""))
                        contact = card.get("meta", {}).get("contact", {})
                        ad_title = (
                            card.get("meta", {}).get("news", {}).get("title", "")
                            or contact.get("nickname", "")
                            or contact.get("tag", "")
                            or card.get("prompt", "")
                        )
                    except Exception:
                        pass
            logger.info(
                f"检测到广告消息: {ad_title or '未知广告'}",
                "广告过滤",
            )
        else:
            clean_msgs.append(msg)

    if ad_count == 0:
        await ad_filter_matcher.finish("未检测到广告消息")
        return

    logger.info(
        f"转发消息 {forward_id} 中检测到 {ad_count} 条广告，"
        f"剩余 {len(clean_msgs)} 条正常消息",
        "广告过滤",
    )

    if not clean_msgs:
        await ad_filter_matcher.finish("转发消息中全部都是广告，没有正常内容")
        return

    # 构造新的合并转发节点（带原始时间戳）
    nodes = []
    for msg in clean_msgs:
        sender = msg.get("sender", {})
        user_id = str(sender.get("user_id") or msg.get("user_id") or bot.self_id)
        nickname = (
            sender.get("nickname")
            or sender.get("card")
            or msg.get("nickname")
            or msg.get("name")
            or user_id
        )
        timestamp = msg.get("time", 0)

        # 优先从 message 数组构造 content，确保图片用 url 作为 file 参数
        content = _build_content_from_message(msg)

        nodes.append(
            MessageSegment("node", {
                "name": str(nickname),
                "uin": user_id,
                "content": content,
                "time": str(timestamp),
            })
        )

    if not nodes:
        return

    # 发送提示 + 清理后的转发消息
    try:
        is_group = isinstance(event, GroupMessageEvent)
        if is_group:
            await bot.send_group_msg(
                group_id=event.group_id,
                message=Message(
                    MessageSegment.text(
                        f"已过滤 {ad_count} 条广告，剩余 {len(clean_msgs)} 条正常消息："
                    )
                ),
            )
            await bot.call_api(
                "send_group_forward_msg",
                group_id=event.group_id,
                messages=Message(nodes),
            )
        else:
            await bot.send_private_msg(
                user_id=event.user_id,
                message=Message(
                    MessageSegment.text(
                        f"已过滤 {ad_count} 条广告，剩余 {len(clean_msgs)} 条正常消息："
                    )
                ),
            )
            await bot.call_api(
                "send_private_forward_msg",
                user_id=event.user_id,
                messages=Message(nodes),
            )
        logger.info("已发送过滤广告后的转发消息", "广告过滤")
    except Exception as e:
        logger.error(f"发送过滤后转发消息失败: {e}", "广告过滤")
        await ad_filter_matcher.finish(f"发送失败: {e}")
