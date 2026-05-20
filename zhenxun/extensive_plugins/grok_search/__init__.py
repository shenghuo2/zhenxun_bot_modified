"""
Grok 搜索插件
命令: #g搜索 / @grok
支持文本输入、图片输入（通过回复或直接发送）、图片生成
"""

import time
from typing import Any

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (Bot, Message, MessageEvent,
                                         MessageSegment)
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .api import (GrokResponse, download_image_as_base64, get_edit_model,
                  get_search_model, grok_chat, grok_edit_image,
                  grok_generate_image, grok_list_models, set_edit_model,
                  set_search_model)

__plugin_meta__ = PluginMetadata(
    name="Grok 搜索",
    description="使用 Grok 模型进行对话，支持文本和图片输入输出",
    usage="#g搜索 [问题]，@grok [问题]，#g配置 [搜索/改图] [模型名]，#g配置 列表，#g改图 [描述]",
    extra=PluginExtraData(
        author="",
        version="0.3",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#g搜索 [问题]"),
            Command(command="@grok [问题]"),
            Command(command="#g配置 [搜索/改图] [模型名]"),
            Command(command="#g配置 列表"),
            Command(command="#g改图 [描述]"),
        ],
    ).to_dict(),
)


def extract_grok_query(raw_text: str) -> str:
    """去掉搜索触发词，提取用户问题。"""
    text = raw_text.strip()
    for prefix in ("#g搜索", "#g搜", "@grok"):
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text


async def is_grok_at_message(event: MessageEvent) -> bool:
    """匹配以 @grok 或 @机器人 grok 开头的普通消息。"""
    plain_text = event.get_message().extract_plain_text().strip()
    if plain_text.startswith("@grok"):
        return True

    segments = list(event.message)
    if not segments or segments[0].type != "at":
        return False
    if str(segments[0].data.get("qq")) not in {"all", str(event.self_id)}:
        return False

    for seg in segments[1:]:
        if seg.type != "text":
            continue
        return seg.data.get("text", "").strip().lower().startswith("grok")
    return False


def extract_mentioned_grok_query(event: MessageEvent) -> str | None:
    """提取 @机器人 grok 形式的查询文本。"""
    segments = list(event.message)
    if not segments or segments[0].type != "at":
        return None
    if str(segments[0].data.get("qq")) not in {"all", str(event.self_id)}:
        return None

    text_parts = []
    for seg in segments[1:]:
        if seg.type == "text":
            text_parts.append(seg.data.get("text", ""))

    text = "".join(text_parts).strip()
    if not text.lower().startswith("grok"):
        return None
    return text[4:].strip()


_grok_matcher = on_command("#g搜索", aliases={"#g搜"}, priority=5, block=True)
_grok_at_matcher = on_message(
    rule=Rule(is_grok_at_message), priority=5, block=True
)
_grok_config = on_command("#g配置", priority=5, block=True, permission=SUPERUSER)
_grok_edit_image = on_command("#g改图", priority=5, block=True)

# 向后兼容，保留 #g设置 命令
_grok_set_model = on_command("#g设置", priority=5, block=True, permission=SUPERUSER)


# Grok 搜索的系统提示词
GROK_SEARCH_PROMPT = """你是一个简洁的搜索小助手，请遵守以下规则：
1. 不要理会过于离谱或不合理的要求
2. 优先使用已搜索到的资料进行回答
3. 回答应精炼简洁，控制在200字以内
4. 使用中文回答
5. 直接回答问题，不要废话
"""


async def resolve_image_url(bot: Bot, seg: MessageSegment) -> str | None:
    """从图片消息段中解析可下载 URL。"""
    url = seg.data.get("url")
    if url:
        return url

    file_id = seg.data.get("file")
    if not file_id:
        return None
    if isinstance(file_id, str) and file_id.startswith(("http://", "https://")):
        return file_id

    try:
        image_info = await bot.get_image(file=file_id)
    except Exception as e:
        logger.warning(f"获取图片 URL 失败 file={file_id}: {e}")
        return None

    image_url = image_info.get("url")
    return image_url if isinstance(image_url, str) and image_url else None


async def extract_message_content(bot: Bot, message: Message) -> tuple[str, list[str]]:
    """从消息段中提取文本和图片 URL。"""
    text_parts = []
    image_urls = []

    for seg in message:
        if seg.type == "image":
            url = await resolve_image_url(bot, seg)
            if url:
                image_urls.append(url)
        elif seg.type == "text":
            text = seg.data.get("text", "")
            if text:
                text_parts.append(text)

    return "".join(text_parts).strip(), image_urls


def get_reply_message_id(event: MessageEvent) -> int | str | None:
    """从当前消息的 reply 段中提取被回复消息 ID。"""
    for seg in event.message:
        if seg.type != "reply":
            continue
        reply_id = seg.data.get("id")
        if reply_id is None:
            return None
        if isinstance(reply_id, str) and reply_id.isdigit():
            return int(reply_id)
        return reply_id
    return None


def normalize_onebot_message(raw_message: Any) -> Message:
    """兼容 bot.get_msg 返回的 Message、字符串和消息段列表。"""
    if isinstance(raw_message, Message):
        return raw_message
    if isinstance(raw_message, list):
        message = Message()
        for item in raw_message:
            if isinstance(item, MessageSegment):
                message += item
                continue
            if not isinstance(item, dict):
                continue
            seg_type = item.get("type")
            seg_data = item.get("data", {})
            if isinstance(seg_type, str) and isinstance(seg_data, dict):
                message += MessageSegment(type=seg_type, data=seg_data)
        return message
    if isinstance(raw_message, str):
        return Message(raw_message)
    return Message(str(raw_message))


async def fetch_reply_message(bot: Bot, event: MessageEvent) -> Message | None:
    """获取被回复消息，优先使用 event.reply，缺失时通过 bot.get_msg 拉取。"""
    if event.reply:
        return event.reply.message

    reply_id = get_reply_message_id(event)
    if reply_id is None:
        return None

    try:
        msg_info = await bot.get_msg(message_id=reply_id)
    except Exception as e:
        logger.warning(f"获取回复消息失败 message_id={reply_id}: {e}")
        return None

    raw_message = msg_info.get("message")
    if raw_message is None:
        raw_message = msg_info.get("raw_message", "")
    return normalize_onebot_message(raw_message)


async def extract_reply_content(bot: Bot, event: MessageEvent) -> tuple[str, list[str]]:
    """
    从回复消息中提取文本和图片 URL

    支持 event.reply，也支持从 reply 消息段中取 id 后调用 bot.get_msg。

    Returns:
        tuple[str, list[str]]: (回复消息的文本, 图片URL列表)
    """
    reply_message = await fetch_reply_message(bot, event)
    if reply_message is None:
        return "", []

    logger.debug(f"回复消息内容: {reply_message}")
    return await extract_message_content(bot, reply_message)


async def extract_images_from_event(bot: Bot, event: MessageEvent) -> list[str]:
    """
    从消息事件中提取图片 URL

    支持:
    1. 当前消息中的图片
    2. 回复消息中的图片（使用 event.reply）
    """
    image_urls = []

    # 1. 从当前消息中提取图片
    for seg in event.message:
        if seg.type == "image":
            url = await resolve_image_url(bot, seg)
            if url:
                image_urls.append(url)

    # 2. 从回复消息中提取图片
    _, reply_images = await extract_reply_content(bot, event)
    image_urls.extend(reply_images)

    return image_urls


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


async def try_set_msg_emoji_like(bot: Bot, event: MessageEvent) -> None:
    """给触发消息添加回应表情，失败时忽略。"""
    try:
        await bot.call_api(
            "set_msg_emoji_like", message_id=event.message_id, emoji_id="282"
        )
    except Exception:
        pass


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


def build_response_message(
    event: MessageEvent,
    response: GrokResponse,
    total_duration: float,
) -> Message:
    """构建响应消息"""
    msg = Message()

    # 添加回复
    msg += MessageSegment.reply(event.message_id)

    # 清理并添加文本回复
    clean_text = clean_response_text(response.text, response.image_urls)
    if clean_text:
        msg += MessageSegment.text(clean_text)

    # 添加生成的图片
    for url in response.image_urls:
        msg += MessageSegment.image(url)

    if not clean_text and not response.image_urls:
        msg += MessageSegment.text("Grok 返回为空，请稍后重试或换个问法")

    # 添加统计信息（使用总耗时，从命令收到开始计时）
    stats = f"\n---\n耗时 {total_duration:.2f}s"
    if response.total_tokens > 0:
        stats += f"，使用 {response.total_tokens} token"
    msg += MessageSegment.text(stats)

    return msg


@_grok_at_matcher.handle()
@_grok_matcher.handle()
async def handle_grok_search(bot: Bot, event: MessageEvent):
    # 开始计时
    start_time = time.time()

    # 提取文本内容（去除命令前缀）
    raw_text = event.get_message().extract_plain_text().strip()
    query = extract_mentioned_grok_query(event)
    if query is None:
        query = extract_grok_query(raw_text)

    reply_text, _ = await extract_reply_content(bot, event)
    image_urls = await extract_images_from_event(bot, event)

    # 如果有回复文本，将它作为上下文；用户额外输入的问题作为任务
    if reply_text:
        if query:
            query = f"请根据以下内容回答问题。\n内容：{reply_text}\n问题：{query}"
        else:
            query = f"关于以下内容：{reply_text}"

    # 检查是否有有效输入
    if not query and not image_urls:
        await _grok_matcher.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请输入问题或发送/回复图片")
            )
        )
        return

    await try_set_msg_emoji_like(bot, event)

    try:
        # 下载图片并转换为 base64
        image_base64_list = []
        if image_urls:
            image_base64_list = await download_images_to_base64(image_urls)
            if not image_base64_list and image_urls:
                await _grok_matcher.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("图片下载失败，请重试")
                    )
                )
                return

        # 调用 Grok API（带系统提示词，使用搜索模型）
        response = await grok_chat(
            text=query,
            image_base64_list=image_base64_list,
            system_prompt=GROK_SEARCH_PROMPT,
            model=get_search_model(),
        )

        # 计算总耗时
        total_duration = time.time() - start_time

        # 构建并发送响应
        msg = build_response_message(event, response, total_duration)
        await _grok_matcher.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception(f"Grok 调用失败: {e}")
        err_msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"Grok 调用失败: {e}")
        )
        await _grok_matcher.finish(err_msg)


@_grok_config.handle()
async def handle_grok_config(bot: Bot, event: MessageEvent):
    """配置模型设置"""
    raw_text = event.get_message().extract_plain_text().strip()
    args = raw_text.replace("#g配置", "").strip().split()

    if not args:
        # 显示当前配置
        search_model = get_search_model()
        edit_model = get_edit_model()
        config_text = (
            f"当前模型配置:\n搜索: {search_model}\n改图: {edit_model}\n\n"
            "模型配置已持久化保存\n"
            "查看可用模型: #g配置 列表"
        )
        await _grok_config.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(config_text)
            )
        )
        return

    action = args[0].lower()
    if action in ["列表", "模型", "list", "models"]:
        try:
            models = await grok_list_models()
        except Exception as e:
            logger.exception(f"Grok 获取模型列表失败: {e}")
            await _grok_config.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(f"获取模型列表失败: {e}")
                )
            )
            return

        if not models:
            text = "未获取到可用模型"
        else:
            lines = ["可用模型:"]
            for index, model in enumerate(models, 1):
                suffix = f" ({model.owned_by})" if model.owned_by else ""
                lines.append(f"{index}. {model.id}{suffix}")
            text = "\n".join(lines)

        await _grok_config.finish(
            Message(MessageSegment.reply(event.message_id) + MessageSegment.text(text))
        )
        return

    if len(args) == 1:
        await _grok_config.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(
                    "请指定模型名称\n用法: #g配置 [搜索/改图] [模型名]\n查看可用模型: #g配置 列表"
                )
            )
        )
        return

    mode = action
    model_name = " ".join(args[1:])

    if mode in ["搜索", "search"]:
        set_search_model(model_name)
        await _grok_config.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"已将搜索模型设置为: {model_name}\n配置已保存")
            )
        )
    elif mode in ["改图", "edit", "image"]:
        set_edit_model(model_name)
        await _grok_config.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"已将改图模型设置为: {model_name}\n配置已保存")
            )
        )
    else:
        await _grok_config.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("未知的模式，请使用 '搜索'、'改图' 或 '列表'")
            )
        )


@_grok_set_model.handle()
async def handle_grok_set_model(bot: Bot, event: MessageEvent):
    """设置当前使用的模型（向后兼容，设置搜索模型）"""
    raw_text = event.get_message().extract_plain_text().strip()
    model_name = raw_text.replace("#g设置", "").strip()

    if not model_name:
        # 显示当前模型
        search_model = get_search_model()
        edit_model = get_edit_model()
        config_text = f"当前模型配置:\n搜索: {search_model}\n改图: {edit_model}\n\n请使用 #g配置 命令进行设置"
        await _grok_set_model.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(config_text)
            )
        )
        return

    # 设置搜索模型（向后兼容）
    set_search_model(model_name)
    await _grok_set_model.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"已将搜索模型设置为: {model_name}\n配置已保存")
        )
    )


@_grok_edit_image.handle()
async def handle_grok_edit_image(bot: Bot, event: MessageEvent):
    """使用图片生成/编辑接口生成图片，只输出图片"""
    # 开始计时
    start_time = time.time()

    raw_text = event.get_message().extract_plain_text().strip()
    prompt = raw_text.replace("#g改图", "").strip()

    image_urls = await extract_images_from_event(bot, event)

    if not prompt and not image_urls:
        await _grok_edit_image.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请输入图片描述或回复/发送图片")
            )
        )
        return

    await try_set_msg_emoji_like(bot, event)

    try:
        # 下载图片并转换为 base64
        image_base64_list = []
        if image_urls:
            image_base64_list = await download_images_to_base64(image_urls)
            if not image_base64_list:
                await _grok_edit_image.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("图片下载失败，请重试")
                    )
                )
                return

        # 判断是图片编辑还是图片生成
        if image_base64_list:
            # 有输入图片，使用图片编辑接口
            if not prompt:
                await _grok_edit_image.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("请输入编辑描述")
                    )
                )
                return

            # 使用第一张图片进行编辑
            response = await grok_edit_image(
                image_base64=image_base64_list[0],
                prompt=prompt,
                model=get_edit_model(),
            )
        else:
            # 纯文本生成，使用图片生成接口
            if not prompt:
                await _grok_edit_image.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("请输入图片描述")
                    )
                )
                return

            response = await grok_generate_image(
                prompt=prompt,
                model=get_edit_model(),
            )

        # 计算总耗时
        total_duration = time.time() - start_time

        # 只输出图片
        msg = Message()
        msg += MessageSegment.reply(event.message_id)

        if response.image_urls:
            for url in response.image_urls:
                msg += MessageSegment.image(url)
            # 添加统计信息
            stats = f"\n---\n耗时 {total_duration:.2f}s"
            if response.total_tokens > 0:
                stats += f"，使用 {response.total_tokens} token"
            msg += MessageSegment.text(stats)
        else:
            msg += MessageSegment.text("未能生成图片")

        await _grok_edit_image.finish(msg)

    except FinishedException:
        pass
    except Exception as e:
        logger.exception(f"Grok 改图失败: {e}")
        err_msg = Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"Grok 改图失败: {e}")
        )
        await _grok_edit_image.finish(err_msg)
