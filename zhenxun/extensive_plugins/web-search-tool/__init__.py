import asyncio
import httpx
import json
from typing import Any, Dict, Tuple

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import PluginExtraData, Command
from zhenxun.utils.enum import PluginType

# Kimi (Moonshot) API
from openai import AsyncOpenAI as KimiClient

# Doubao (Volcengine Ark) API
from openai import OpenAI as ArkClient

# 载入密钥配置
from .config import ARK_API_KEY, KIMI_API_KEY
# try:
#     # 直接复用示例中的 Kimi API Key
#     from .test_kimi import api_key as KIMI_API_KEY
# except Exception:
#     import os
#     KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")


__plugin_meta__ = PluginMetadata(
    name="Web 搜索工具集成",
    description="提供 #高级搜索 与 #搜索 两个命令，联网搜索并输出总 token 数",
        usage=(
            "#高级搜索 [问题]",
            "#搜索 [问题]",
        ),
    extra=PluginExtraData(
        author="",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#高级搜索 [问题]"),
            Command(command="#搜索 [问题]"),
        ],
    ).to_dict(),
)


system_prompt = """
你是AI个人助手，负责解答用户的各种问题。你的主要职责是：
1. 信息准确性守护者：确保提供的信息准确无误。
2. 搜索成本优化师：在信息准确性和搜索成本之间找到最佳平衡。
# 任务说明
## 1. 联网意图判断
当用户提出的问题涉及以下情况时，需使用 `web_search` 进行联网搜索：
- 时效性：问题需要最新或实时的信息。
- 知识盲区：问题超出当前知识范围，无法准确解答。
- 信息不足：现有知识库无法提供完整或详细的解答。
## 2. 联网后回答
- 在回答中，优先使用已搜索到的资料。
- 应该精炼，避免冗长的回答，用户应该只需要一个200字以下的答案。
"""


# ============ Kimi (Moonshot) ============
async def kimi_search(query: str) -> Tuple[int, int, str]:
    """使用 Kimi (Moonshot) 接口进行搜索，并返回 web_search 调用次数、total_tokens 与回复文本"""
    client = KimiClient(base_url="https://api.moonshot.cn/v1", api_key=KIMI_API_KEY)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    total_tokens: int = 0
    web_search_count: int = 0
    answer_text: str = ""

    while True:
        completion = await client.chat.completions.create(
            model="moonshot-v1-128k",
            messages=messages,
            temperature=0.3,
            tools=[
                {
                    "type": "builtin_function",
                    "function": {"name": "$web_search"},
                }
            ],
        )
        if completion.usage and completion.usage.total_tokens is not None:
            total_tokens += completion.usage.total_tokens

        choice = completion.choices[0]
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            # 执行工具并将结果回填
            for tool_call in choice.message.tool_calls or []:
                if tool_call.function.name == "$web_search":
                    web_search_count += 1
                args: Dict[str, Any] = json.loads(tool_call.function.arguments)
                tool_result = args  # 直接返回参数，保持与示例一致
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(tool_result),
                    }
                )
            continue

        answer_text = choice.message.content or ""
        break

    return web_search_count, total_tokens, answer_text


# ============ Doubao (Volcengine Ark) ============
async def doubao_search(query: str) -> Tuple[int, str]:
    """使用 Doubao (Ark) 接口进行搜索，并返回 total_tokens 与回复文本"""
    url = "https://ark.cn-beijing.volces.com/api/v3/responses"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "doubao-seed-1-6-250615",
        "stream": False,
        "tools": [{"type": "web_search"}],
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt+"\nsource_types请尽量使用search_engine",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{query}",
                    }
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()  # 如果请求失败则抛出异常
        result = response.json()

    total_tokens = result.get("usage", {}).get("total_tokens", 0)
    output_text = ""
    for item in result.get("output", []):
        if item.get("type") == "message" and item.get("role") == "assistant":
            for content_item in item.get("content", []):
                if content_item.get("type") == "output_text":
                    output_text = content_item.get("text", "")
                    break
            if output_text:
                break

    if not output_text:
        raise ValueError("Doubao API 返回的响应中没有有效的回答文本。")

    return total_tokens, output_text


# 命令：kimi搜索
_kimi_matcher = on_command("#高级搜索", priority=5, block=False, permission=SUPERUSER)


@_kimi_matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    query = event.get_message().extract_plain_text().strip()
    try:
        web_search_count, total_tokens, answer = await kimi_search(query)
        msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(
                f"{answer}\n本次调用共进行 {web_search_count} 次搜索，使用 {total_tokens} token"
            )
        )
        await _kimi_matcher.finish(msg)
    except FinishedException:
        pass
    except Exception as e:
        err = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"Kimi 调用失败: {e}")
        )
        await _kimi_matcher.finish(err)


# 命令：doubao搜索
_doubao_matcher = on_command("#搜索", priority=5, block=False, permission=SUPERUSER)


@_doubao_matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    query = event.get_message().extract_plain_text().strip()
    try:
        total_tokens, answer = await doubao_search(query)
        msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"{answer}\n本次调用共使用 {total_tokens} token")
        )
        await _doubao_matcher.finish(msg)
    except FinishedException:
        pass
    except Exception as e:
        logger.exception(f"Doubao 调用失败，错误：{e}")
        err = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"Doubao 调用失败，请检查后台日志。")
        )
        await _doubao_matcher.finish(err)