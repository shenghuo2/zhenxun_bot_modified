"""
OpenAI 图像生成插件
命令: #画图 [描述]
使用 OpenAI 格式的 /images/generations 接口生成图片
"""

import base64
import time

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .config import API_BASE, API_KEY, MODEL

__plugin_meta__ = PluginMetadata(
    name="AI 画图",
    description="使用 OpenAI 格式接口生成图片",
    usage="#画图 [描述]",
    extra=PluginExtraData(
        author="",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#画图 [描述]"),
        ],
    ).to_dict(),
)

_image_gen = on_command("#画图", priority=5, block=True)


async def generate_image(prompt: str) -> dict:
    """
    调用 OpenAI 格式的 /images/generations 接口生成图片

    Args:
        prompt: 图片描述

    Returns:
        dict: API 响应数据
    """
    url = f"{API_BASE}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


@_image_gen.handle()
async def handle_image_gen(bot: Bot, event: MessageEvent):
    """处理图片生成请求"""
    raw_text = event.get_message().extract_plain_text().strip()
    prompt = raw_text.replace("#画图", "").strip()

    if not prompt:
        await _image_gen.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请输入图片描述，例如: #画图 一只在月球上的猫")
            )
        )
        return

    start_time = time.time()

    try:
        await _image_gen.send(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("正在生成图片，请稍候...")
            )
        )

        result = await generate_image(prompt)
        total_duration = time.time() - start_time

        msg = Message()
        msg += MessageSegment.reply(event.message_id)

        data_list = result.get("data", [])
        if not data_list:
            msg += MessageSegment.text("未能生成图片")
            await _image_gen.finish(msg)
            return

        has_image = False
        for item in data_list:
            # 优先使用 b64_json
            b64 = item.get("b64_json")
            if b64:
                msg += MessageSegment.image(f"base64://{b64}")
                has_image = True
            else:
                # 其次使用 url
                url = item.get("url")
                if url:
                    msg += MessageSegment.image(url)
                    has_image = True

        if has_image:
            stats = f"\n---\n耗时 {total_duration:.2f}s"
            msg += MessageSegment.text(stats)
        else:
            msg += MessageSegment.text("未能生成图片")

        await _image_gen.finish(msg)

    except FinishedException:
        pass
    except httpx.HTTPStatusError as e:
        logger.exception(f"图像生成 API 请求失败: {e}")
        body = e.response.text[:300] if e.response else ""
        err_msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"图像生成失败 (HTTP {e.response.status_code}): {body}")
        )
        await _image_gen.finish(err_msg)
    except Exception as e:
        logger.exception(f"图像生成失败: {e}")
        err_msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"图像生成失败: {e}")
        )
        await _image_gen.finish(err_msg)
