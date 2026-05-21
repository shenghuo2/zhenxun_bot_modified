import ast
import html
import json
import re
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (Bot, GroupMessageEvent, Message,
                                         MessageEvent, MessageSegment)
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import (Alconna, AlconnaMatcher, Args, Match,
                                    on_alconna)
from nonebot_plugin_uninfo import Uninfo

CHUNK_SIZE = 2000
NODES_PER_FORWARD = 10
DEBUG_DATA_DIR = Path(__file__).parent / "debugdata"


def _extract_bracket_block(data: str, start: int) -> tuple[str, int] | None:
    """从 start 位置提取一段匹配的括号块（支持 { } 和 [ ]），返回 (子串, 结束位置)"""
    open_ch = data[start]
    close_ch = '}' if open_ch == '{' else ']'
    depth = 0
    in_str = False
    str_quote = None
    escape = False
    for i in range(start, len(data)):
        c = data[i]
        if escape:
            escape = False
            continue
        if c == '\\' and in_str:
            escape = True
            continue
        if not in_str and c in ('"', "'"):
            in_str = True
            str_quote = c
            continue
        if in_str and c == str_quote:
            in_str = False
            continue
        if in_str:
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return data[start:i + 1], i + 1
    return None


def _try_parse_and_format(candidate: str) -> str | None:
    """尝试将候选字符串作为 Python literal 或 JSON 解析并格式化"""
    # 先尝试 ast.literal_eval（处理单引号、True/False/None 等 Python repr）
    try:
        obj = ast.literal_eval(candidate)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # 再尝试 json.loads
    try:
        obj = json.loads(candidate)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return None


def _format_debug_data(data: str) -> str:
    """HTML entity 解码，并尝试将其中的 JSON / Python literal 片段格式化"""
    data = html.unescape(data)
    result = []
    i = 0
    while i < len(data):
        if data[i] in ('{', '['):
            block = _extract_bracket_block(data, i)
            if block:
                candidate, end = block
                formatted = _try_parse_and_format(candidate)
                if formatted:
                    result.append(formatted)
                    i = end
                    continue
        result.append(data[i])
        i += 1
    return ''.join(result)


async def send_long_text(bot: Bot, event: MessageEvent, data: str):
    """将长文本按 CHUNK_SIZE 分割，每 NODES_PER_FORWARD 条打包一个合并转发发送"""
    chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    nodes = [
        MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname="Debug",
            content=Message(MessageSegment.text(chunk)),
        )
        for chunk in chunks
    ]
    # 按 NODES_PER_FORWARD 分批发送
    for i in range(0, len(nodes), NODES_PER_FORWARD):
        batch = nodes[i:i + NODES_PER_FORWARD]
        if isinstance(event, GroupMessageEvent):
            await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=batch)
        else:
            await bot.call_api("send_private_forward_msg", user_id=event.user_id, messages=batch)

# 创建一个debug命令，仅限超级用户
debug_cmd = on_command("#debugcmd", priority=5, block=True, permission=SUPERUSER)

@debug_cmd.handle()
async def handle_debugcmd(event: MessageEvent, bot: Bot, session: Uninfo):
    # 获取用户输入的消息并去除命令前缀
    message_content = event.raw_message
    data = f"message_content : {message_content}\n" + \
           f"message_type : {event.message_type}\n"
    message_segment_type =  "&".join([str(segment.type) for segment in event.message])
    data+= f"message_segment_type : {message_segment_type}"
    # 返回命令信息
    # bot.get_msg
    await debug_cmd.finish(data)


# 创建一个debugreply命令，获取回复消息的信息
debug_reply_cmd = on_command("#debugreply", priority=5, block=True, permission=SUPERUSER)

@debug_reply_cmd.handle()
async def handle_debugreply(event: MessageEvent, bot: Bot, session: Uninfo):
    # 获取被回复的消息（如果有）
    replied_message = event.reply
    if not replied_message:
        await debug_reply_cmd.finish("没有回复的消息，无法获取信息！")
        return

    message_type = replied_message.message_type
    message = replied_message.message
    message_id = replied_message.message_id
    message_real_id = replied_message.real_id if replied_message.real_id else None
    # 返回被回复消息的相关信息
    data = f"message_type : {message_type}\n" + \
           f"message : {message}\n" + \
           f"message_id : {message_id}"
    if message_real_id:
        data += f"\nmessage_real_id : {message_real_id}"

    # 判断是否带 local 参数
    raw_args = event.raw_message.strip().split()
    save_local = len(raw_args) >= 2 and raw_args[1].lower() == "local"

    if save_local:
        DEBUG_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 判断回复的消息是否包含 forward 段
        forward_seg = next((seg for seg in replied_message.message if seg.type == "forward"), None)
        if forward_seg:
            fwd_id = forward_seg.data.get("id", message_id)
            file_name = f"fwd_{fwd_id}.log"
        else:
            file_name = f"msg_{message_id}.log"
        file_path = DEBUG_DATA_DIR / file_name
        file_path.write_text(_format_debug_data(data), encoding="utf-8")
        await debug_reply_cmd.finish(f"已保存到 {file_path}")
    else:
        await send_long_text(bot, event, data)



# 创建一个debugmessage命令，从参数获取message_id ，用bot.get_msg获取消息信息，输出一些信息
debug_message_cmd = on_command("#debugmessage", priority=5, block=True, permission=SUPERUSER)

@debug_message_cmd.handle()
async def handle_debugmessage(event: MessageEvent, bot: Bot):
    # 获取用户输入的消息并去除命令前缀
    args = event.raw_message.strip().split()
    if len(args) < 2:
        await debug_message_cmd.finish("请提供message_id")
        return
    
    message_id = args[1]
    
    try:
        # 使用bot.get_msg获取消息信息
        message_info = await bot.get_msg(message_id=message_id)
        data = f"message : {message_info}\n"
            #    f"message : {message_info['message']}\n" + \
            #    f"sender : {message_info['sender']}\n" + \
            #    f"time : {message_info['time']}"
        await send_long_text(bot, event, data)
    except FinishedException:
        pass
    except Exception as e:
        logger.error(f"获取消息信息失败: {e}")
        await debug_message_cmd.finish(f"获取消息信息失败: {e}")

