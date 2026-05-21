from nonebot import on_command, get_bot
from nonebot.adapters.onebot.v11 import MessageSegment,Bot, Event
# from nonebot.adapters import Bot
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
import logging
# finished exception
from nonebot.exception import FinishedException

logger = logging.getLogger(__name__)

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="DebugForward",
    description="通过#debugforward命令获取转发的消息内容",
    usage="#debugforward <转发消息ID>"
)

# 定义一个调试命令，名称为debugforward
debug_forward_cmd_v2 = on_command("debugforward", aliases={"#debugforward"}, priority=5,permission=SUPERUSER)

# 命令处理函数
@debug_forward_cmd_v2.handle()
async def handle_debug_forward_cmd_v2(event:Event,bot:Bot):
    # 获取命令参数，假设用户输入的格式为 #debugforward <转发消息ID>
    args = str(event.get_message()).strip().split()
    await debug_forward_cmd_v2.send(f"args: {args}")
    if not args[1].isdigit():
        await debug_forward_cmd_v2.finish("请输入有效的转发消息ID！")
    
    forward_message_id = args[1]

    try:
        # 获取转发消息
        # bot = get_bot()
        forward_message = await bot.call_api(api="get_forward_msg",message_id=forward_message_id)
        logger.info(f"forward_message: {forward_message}","dbg")
        if forward_message:
            # 提取消息内容和消息ID
            data = f"转发的消息内容: {str(forward_message)}\n"
                #    f"转发消息的message_id: {forward_message['message_id']}"
            await debug_forward_cmd_v2.finish(data)
        else:
            await debug_forward_cmd_v2.finish("未找到该转发消息！")
    except FinishedException:
        pass
    
    except Exception as e:
        logger.error(f"获取转发消息失败: {e}")
        await debug_forward_cmd_v2.finish(f"获取转发消息失败: {e}")

debug_call_api= on_command("debugcallapi", aliases={"#debugcallapi"}, priority=5,permission=SUPERUSER)

# 命令处理函数
@debug_call_api.handle()
async def handle_debug_call_api(event: Event, bot: Bot):
    # 获取命令参数，假设用户输入的格式为 #debugcallapi <api> <args>
    args = str(event.get_message()).strip().split()
    await debug_call_api.send(f"args: {args}")
    if len(args) < 2:
        await debug_call_api.finish("请输入有效的api和参数！")
    
    api = args[1]
    params = args[2:]

    # 将参数转换为字典
    params_dict = {}
    for param in params:
        key, value = param.split("=")
        params_dict[key] = value.strip('"')

    try:
        # 调用api
        result = await bot.call_api(api=api, **params_dict)
        await debug_call_api.send(str(params_dict))
        logger.info(f"result: {result}", "dbg")
        if result:
            # 提取消息内容和消息ID
            data = f"调用api: {api} 返回结果: {str(result)}\n"
            await debug_call_api.finish(data)
        else:
            await debug_call_api.finish("调用api失败！")
    except FinishedException:
        pass
    
    except Exception as e:
        logger.error(f"调用api失败: {e}")
        await debug_call_api.finish(f"调用api失败: {e}")
        
        
# from nonebot import on_notice
# from nonebot.adapters.onebot.v12 import GroupMessageEvent, GroupMemberIncreaseEvent, NoticeEvent
# from typing import Any, Literal, Optional, List, Dict


# class EmojiLikeEvent(NoticeEvent):
#     """群消息表情点赞事件"""

#     # 定义事件的详细类型
#     detail_type: Literal["group_msg_emoji_like"]
#     group_id: str  # 群组ID
#     user_id: str  # 点赞的用户ID
#     likes: List[Dict[str, int]]  # 点赞的表情信息，包含emoji_id和count

#     # def __init__(self, data: Dict):
#     #     super().__init__(data)
#     #     self.detail_type = data["notice_type"]
#     #     self.group_id = str(data["group_id"])
#     #     self.user_id = str(data["user_id"])
#     #     self.likes = data["likes"]  # 例如：[{"emoji_id": "76", "count": 1}]

#     # def __str__(self):
#     #     return f"EmojiLikeEvent(group_id={self.group_id}, user_id={self.user_id}, likes={self.likes})"


# @on_notice("group_msg_emoji_like")
# async def handle_emoji_like(event: EmojiLikeEvent):
#     user_id = event.user_id
#     group_id = event.group_id
#     likes = event.likes
#     print(f"用户 {user_id} 在群 {group_id} 点了表情赞: {likes}")
