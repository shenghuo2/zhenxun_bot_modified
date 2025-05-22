from nonebot.adapters import Bot
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Alconna, Arparma, UniMessage, on_alconna
from nonebot_plugin_session import EventSession
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment

from zhenxun.services.log import logger
from zhenxun.configs.utils import PluginExtraData
from zhenxun.utils.message import MessageUtils
from .utils import get_deepseek_balance


__plugin_meta__ = PluginMetadata(
    name="shenghuo2的工具集",
    description="实用工具集合（by shenghuo2）",
    usage="""
    #deepseek余额 - 查询DeepSeek账户余额
    #获取图片 - 回复表情包消息，获取原图
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
    
    logger.info(
        f"DeepSeek余额查询成功",
        user_id=session.id1,
        platform=session.platform
    )

# 添加获取图片功能
get_image_matcher = on_alconna(Alconna("#获取图片"), priority=5, block=True)

@get_image_matcher.handle()
async def handle_get_image(bot: Bot, session: EventSession, event: MessageEvent):
    # 检查是否有回复消息
    if not event.reply:
        await get_image_matcher.finish(MessageSegment.text("请回复一条包含表情包的消息"))
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
                    await get_image_matcher.finish(Message(MessageSegment.image(image_url)))
                    
                    logger.info(
                        f"表情包原图获取成功",
                        user_id=session.id1,
                        platform=session.platform
                    )
                else:
                    await get_image_matcher.finish(MessageSegment.text("获取图片URL失败"))
    
    if not image_found:
        await get_image_matcher.finish(MessageSegment.text("回复的消息不包含表情包图片"))
