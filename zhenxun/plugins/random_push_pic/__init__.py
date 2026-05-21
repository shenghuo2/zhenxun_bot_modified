
import random
import nonebot
from nonebot import on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot_plugin_alconna import Alconna, Arparma, UniMessage, on_alconna

import requests
import asyncio

from nonebot.plugin import PluginMetadata
from zhenxun.configs.utils import Command, PluginExtraData, RegisterConfig, Task

from .data_source import *
# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="随机推送图片",
    description="通过 API 随机推送图片到群聊",
    usage="""指令：
        随机推送图片 - 随机推送 0 到 3 张图片
    """.strip(),
    extra=PluginExtraData(
        author="GPT",
        version="0.1",
        superuser_help="""重置推送图片设置""",
        commands=[Command(command="随机推送图片")],
        tasks=[Task(module="random_push_pic", name="随机推送图片")],
        configs=[  # 配置项
            RegisterConfig(
                key="PUSH_GROUPS",
                value=None,
                help="配置可以接收图片推送的群聊ID（例如：[123456789, 987654321]）",
            ),
        ],
    ).to_dict(),
)


# 随机时间间隔发送 0 到 3 张图片
async def send_random_images(bot: Bot, group_id: int):
    while True:
        # 随机确定发送图片的数量，0到3张
        num_images = random.randint(0, 3)
        image_urls = []

        for _ in range(num_images):
            image_url = get_image_from_lolicon_api()
            if image_url:
                image_urls.append(image_url)

        # 发送图片消息
        if image_urls:
            # 构建消息内容，使用 MessageSegment 构造图片发送内容
            images_message = []
            for url in image_urls:
                images_message.append(MessageSegment.image(url))

            # 发送消息
            await bot.send_group_msg(group_id=group_id, message=images_message)

        # 随机时间间隔：随机 10-60 秒
        random_sleep_time = random.randint(10, 60)  # 随机 10-60 秒
        await asyncio.sleep(random_sleep_time)




_matcher = on_alconna(Alconna("测试随机色图发送"), priority=5, block=True)


@_matcher.handle()
async def _(bot: Bot, arparma: Arparma):
    image_url = get_image_from_lolicon_api()
    if image_url:
        await _matcher.finish(MessageSegment.image(image_url))
    else:
        await _matcher.finish("获取图片失败"+str(image_url))