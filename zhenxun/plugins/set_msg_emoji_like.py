from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Bot
from nonebot.permission import SUPERUSER
import random
import asyncio

# 处理回应逻辑
async def process_message(bot: Bot, event: MessageEvent, param: str):
    param = param.strip()

    # 获取消息的 message_id，如果有回复消息，使用回复的消息ID
    if event.reply:
        replied_message = event.reply
        message_id = replied_message.message_id
    else:
        message_id = event.message_id

    # 检查回应类型
    if '-' in param:  # 如果是范围格式 1-10
        try:
            start, end = map(int, param.split('-'))
        except ValueError:
            await bot.send(event, "参数格式错误，应该是 1-10 这样的格式。")
            return
        for i in range(start, end + 1):
            await asyncio.sleep(random.uniform(0.2, 1))  # 随机延时
            await bot.call_api("set_msg_emoji_like", message_id=message_id, emoji_id=str(i), set='True')
    else:  # 如果是单一数字
        try:
            num = int(param)
            await bot.call_api("set_msg_emoji_like", message_id=message_id, emoji_id=str(num), set='True')
        except ValueError:
            await bot.send(event, "请输入有效的数字（1-10）。")

# 设置回应命令的响应器
# @on_command("set_msg_emoji_like")

set_msg_emoji_like = on_command("回应", aliases={"#回应"}, priority=5, permission=SUPERUSER)

@set_msg_emoji_like.handle()
async def handle_emoji_response(bot: Bot, event: MessageEvent):
    # 获取命令的参数，假设命令格式为 "#回应 参数"
    param = event.message.extract_plain_text()[3:].strip()  # 去掉 #回应 部分，获取参数

    if param:
        await process_message(bot, event, param)
    else:
        await bot.send(event, "请输入有效的参数！")


face_ids = [
    4, 5, 8, 9, 10, 12, 14, 16, 21, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34, 38, 39, 41, 42, 43, 49, 53, 60, 63, 66, 74, 75, 76, 78, 79, 85, 89, 96, 97, 98, 99, 100, 101, 102, 103, 104, 106, 109, 111, 116, 118, 120, 122, 123, 124, 125, 129, 144, 147, 171, 173, 174, 175, 176, 179, 180, 181, 182, 183, 201, 203, 212, 214, 219, 222, 227, 232, 240, 243, 246, 262, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 277, 278, 281, 282, 284, 285, 287, 289, 290, 293, 294, 297, 298, 299, 305, 306, 307, 314, 315, 318, 319, 320, 322, 324, 326, 9728, 9749, 9786, 10024, 10060, 10068, 127801, 127817, 127822, 127827, 127836, 127838, 127847, 127866, 127867, 127881, 128027, 128046, 128051, 128053, 128074, 128076, 128077, 128079, 128089, 128102, 128104, 128147, 128157, 128164, 128166, 128168, 128170, 128235, 128293, 128513, 128514, 128516, 128522, 128524, 128527, 128530, 128531, 128532, 128536, 128538, 128540, 128541, 128557, 128560, 128563
]

# 处理骚扰命令逻辑
async def process_harassment(bot: Bot, event: MessageEvent):
    # 获取消息的 message_id，如果有回复消息，使用回复的消息ID
    if event.reply:
        replied_message = event.reply
        message_id = replied_message.message_id
    else:
        message_id = event.message_id

    # 随机选择 20 个不同的 face_id
    selected_face_ids = random.sample(face_ids, 20)

    # 执行 20 次 set_msg_emoji_like 操作
    for face_id in selected_face_ids:
        await bot.call_api("set_msg_emoji_like", message_id=message_id, emoji_id=str(face_id), set='True')
        await asyncio.sleep(random.uniform(0.2, 1))  # 随机延时

# 设置骚扰命令的响应器
set_msg_emoji_like = on_command("#骚扰", priority=5)

@set_msg_emoji_like.handle()
async def handle_harassment(bot: Bot, event: MessageEvent):
    await process_harassment(bot, event)