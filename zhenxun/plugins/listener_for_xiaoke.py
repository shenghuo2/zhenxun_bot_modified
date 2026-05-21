# from nonebot import on_message, get_driver
# from nonebot.adapters.onebot.v11 import (
#     Bot,
#     Event,
#     Message,
#     MessageSegment,
#     GroupMessageEvent,
# )
# from nonebot.permission import SUPERUSER
# from nonebot.plugin import PluginMetadata
# from zhenxun.configs.utils import Command, PluginExtraData, RegisterConfig, Task
# from zhenxun.services.log import logger

# # Uninfo
# from nonebot_plugin_uninfo import Uninfo

# # 插件元数据
# __plugin_meta__ = PluginMetadata(
#     name="转发图片插件",
#     description="监听指定群和用户的图片消息并转发到另一个群聊",
#     usage="""指令：
#         无指令，通过自动监听指定群聊和用户的图片消息，将图片转发到目标群。
#     """.strip(),
#     extra=PluginExtraData(
#         author="GPT",
#         version="0.1",
#         superuser_help="""配置目标群聊和用户进行图片转发操作""",
#         commands=[],
#         tasks=[Task(module="forward_image", name="转发图片任务")],
#     ).to_dict(),
# )


# # 设置需要监听的群号和用户QQ号
# TARGET_GROUP_ID = 696707598  # 源群号
# TARGET_USER_ID = 54297198  # 目标用户QQ号
# # TARGET_GROUP_ID = 912045649  # 源群号
# # TARGET_USER_ID = 1308357113  # 目标用户QQ号
# FORWARD_GROUP_ID = 787599185  # 转发图片的目标群号

# # 创建监听消息的 on_message 事件处理器


# async def _rule(session: Uninfo) -> bool:
#     # 从配置中获取群号白名单

#     if session.group.id != "ban696707598":
#         return False  # 如果群不在白名单中，忽略该消息
#     return True  # 如果群在白名单中，处理消息


# _matcher = on_message(block=False, rule=_rule)


# @_matcher.handle()
# async def handle_message(bot: Bot, event: Event):
#     # 新增：先检查是否是群消息事件
#     if not isinstance(event, GroupMessageEvent):
#         return  # 如果不是群消息事件，直接返回不做处理

#     # 将事件类型转换为GroupMessageEvent以访问group_id属性
#     group_event = event  # type: GroupMessageEvent

#     # 检查消息是否来自指定群聊和用户
#     # logger.info(f"event.group_id:{type(group_event.group_id)} {group_event.group_id}, event.user_id: {type(group_event.user_id)} {group_event.user_id}")

#     if (
#         group_event.group_id == TARGET_GROUP_ID
#         and group_event.user_id == TARGET_USER_ID
#     ):
#         # 检查消息是否包含图片
#         message = event.message
#         image_urls = [
#             segment
#             for segment in message
#             if isinstance(segment, MessageSegment) and segment.type == "image"
#         ]

#         if image_urls:
#             # 如果消息中包含图片，提取图片URL并转发
#             for image_url in image_urls:
#                 image_segment = MessageSegment.image(image_url.data["url"])
#                 # 将图片发送到目标群
#                 await bot.send_group_msg(
#                     group_id=FORWARD_GROUP_ID, message=image_segment
#                 )
