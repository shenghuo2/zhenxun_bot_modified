"""
Gemini 改图插件
命令: #大香蕉改图
支持图片编辑和生成
- 每人每天限制3次（superuser跳过限制）
- 记录群总使用次数和花费
"""

import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .api import download_image_as_base64, gemini_chat
from .config import GEMINI_COST_PER_CALL
from .usage_tracker import DAILY_LIMIT, check_user_limit, record_usage

__plugin_meta__ = PluginMetadata(
    name="大香蕉改图",
    description="使用 Gemini 模型进行图片编辑和生成，每人每天3次",
    usage="#大香蕉改图 [描述]，可回复图片或直接发送图片",
    extra=PluginExtraData(
        author="",
        version="0.2",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#大香蕉改图 [描述]"),
        ],
    ).to_dict(),
)


_gemini_edit = on_command("#大香蕉改图", priority=5, block=True)


async def is_superuser(event: MessageEvent) -> bool:
    """检查是否为 superuser"""
    from nonebot import get_driver

    return str(event.user_id) in get_driver().config.superusers


async def extract_reply_content(event: MessageEvent) -> tuple[str, list[str]]:
    """
    从回复消息中提取文本和图片 URL

    使用 event.reply 属性获取回复消息

    Returns:
        tuple[str, list[str]]: (回复消息的文本, 图片URL列表)
    """
    reply_text = ""
    image_urls = []

    # 使用 event.reply 获取回复消息
    reply = event.reply
    if not reply:
        return reply_text, image_urls

    reply_message = reply.message
    logger.debug(f"回复消息内容: {reply_message}")

    # 从回复消息中提取内容
    for seg in reply_message:
        if seg.type == "image":
            url = seg.data.get("url")
            if url:
                image_urls.append(url)
        elif seg.type == "text":
            text = seg.data.get("text", "")
            if text:
                reply_text += text

    return reply_text, image_urls


async def download_images_to_base64(image_urls: list[str]) -> list[str]:
    """
    下载图片并转换为 base64 格式

    Args:
        image_urls: 图片 URL 列表

    Returns:
        list[str]: base64 编码的图片列表
    """
    base64_list = []
    for url in image_urls:
        b64 = await download_image_as_base64(url)
        if b64:
            base64_list.append(b64)
            logger.debug(f"图片下载成功: {url[:50]}...")
        else:
            logger.warning(f"图片下载失败: {url}")
    return base64_list


def clean_response_text(text: str, image_urls: list[str]) -> str:
    """
    清理响应文本，移除图片生成相关的提示信息
    """
    import re

    # 如果有图片生成，移除相关的提示文本
    if image_urls:
        # 移除 "I generated images with the prompt: '...'" 这类文本
        text = re.sub(
            r"I generated images? with the prompt:.*?['\"].*?['\"]\s*",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # 移除 Markdown 图片语法 ![...](url)
        text = re.sub(r"!\[.*?\]\(https?://[^)]+\)\s*", "", text)
        # 移除独立的图片 URL 行
        text = re.sub(
            r"^https?://\S+\.(?:jpg|jpeg|png|gif|webp)\S*$",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )

    # 清理多余的空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


@_gemini_edit.handle()
async def handle_gemini_edit(bot: Bot, event: MessageEvent):
    """使用 Gemini 生成/编辑图片"""
    user_id = str(event.user_id)
    group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None

    # 检查使用限制（superuser 跳过）
    if not await is_superuser(event):
        can_use, daily_count = check_user_limit(user_id)
        if not can_use:
            await _gemini_edit.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(
                        f"今日使用次数已达上限({DAILY_LIMIT}次)，明天再来吧~"
                    )
                )
            )
            return

    # 开始计时
    start_time = time.time()

    raw_text = event.get_message().extract_plain_text().strip()
    prompt = raw_text.replace("#大香蕉改图", "").strip()

    # 提取回复消息的图片
    _, reply_images = await extract_reply_content(event)

    # 从当前消息中提取图片
    current_images = []
    for seg in event.message:
        if seg.type == "image":
            url = seg.data.get("url")
            if url:
                current_images.append(url)

    image_urls = current_images + reply_images

    if not prompt and not image_urls:
        await _gemini_edit.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请输入图片描述或回复/发送图片")
            )
        )
        return

    try:
        # 下载图片并转换为 base64
        image_base64_list = []
        if image_urls:
            image_base64_list = await download_images_to_base64(image_urls)

        # 构建生成图片的提示词
        if image_base64_list:
            # 有输入图片，进行图片编辑
            if prompt:
                full_prompt = f"{prompt}"
            else:
                full_prompt = ""
        else:
            # 纯文本生成
            full_prompt = f"{prompt}"

        # 调用 Gemini API
        response = await gemini_chat(
            text=full_prompt,
            image_base64_list=image_base64_list,
        )

        # 计算总耗时
        total_duration = time.time() - start_time

        # 输出图片
        msg = Message()
        msg += MessageSegment.reply(event.message_id)

        has_images = False

        # 优先使用 base64 图片
        if response.image_base64_list:
            for b64_data in response.image_base64_list:
                msg += MessageSegment.image(b64_data)
            has_images = True
        # 其次使用 URL 图片
        elif response.image_urls:
            for url in response.image_urls:
                msg += MessageSegment.image(url)
            has_images = True

        if has_images:
            # 记录使用次数和花费
            usage_stats = record_usage(user_id, group_id, GEMINI_COST_PER_CALL)

            # 添加统计信息
            stats = f"\n---\n耗时 {total_duration:.2f}s"
            if response.total_tokens > 0:
                stats += f"，使用 {response.total_tokens} token"
            stats += f"，消耗 {GEMINI_COST_PER_CALL:.2f}￥"
            # 显示群统计
            if group_id:
                stats += f"\n群总计: {usage_stats['group_total_count']}次，共花费 {usage_stats['group_total_cost']:.2f}￥"
            msg += MessageSegment.text(stats)
        else:
            # 输出详细信息帮助调试
            text_preview = response.text[:500] if response.text else "(空)"
            debug_info = f"未能生成图片\n响应文本:\n{text_preview}"
            msg += MessageSegment.text(debug_info)

        await _gemini_edit.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception(f"Gemini 改图失败: {e}")
        err_msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"Gemini 改图失败: {e}")
        )
        await _gemini_edit.finish(err_msg)
