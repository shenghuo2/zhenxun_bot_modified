from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from pathlib import Path
from typing import Any, Literal

from nonebot import logger
from nonebot.adapters import Event
from nonebot.matcher import current_bot, current_event
from nonebot_plugin_alconna import SupportAdapter, uniseg
from nonebot_plugin_alconna.uniseg import (
    CustomNode,
    File,
    Image,
    Reference,
    Segment,
    Text,
    UniMessage,
    Video,
    Voice,
)

from .config import pconfig
from .utils import get_file_url

# from .exception import TipException

ForwardNodeInner = str | Segment | UniMessage
"""转发消息节点内部允许的类型"""

EMOJI_MAP = {
    "fail": ("10060", "❌"),
    "resolving": ("424", "👀"),
    "done": ("144", "🎉"),
}
"""emoji 映射"""

ID_ADAPTERS = {
    adapter
    for adapter in (
        getattr(SupportAdapter, "onebot11", None),
        getattr(SupportAdapter, "qq", None),
        getattr(SupportAdapter, "milky", None),
    )
    if adapter is not None
}
"""支持的传入 emoji id 发送 reaction 的适配器"""


class UniHelper:
    @staticmethod
    def construct_forward_message(
        segments: Sequence[ForwardNodeInner],
        user_id: str | None = None,
    ) -> Reference:
        """构造转发消息"""
        if user_id is None:
            user_id = current_bot.get().self_id

        nodes: list[CustomNode] = []
        for seg in segments:
            if isinstance(seg, str):
                content = UniMessage([Text(seg)])
            elif isinstance(seg, Segment):
                content = UniMessage([seg])
            else:
                content = seg
            node = CustomNode(uid=user_id, name=pconfig.nickname, content=content)
            nodes.append(node)

        return Reference(nodes=nodes)

    @staticmethod
    def img_seg(
        file: Path | bytes,
    ) -> Image:
        """图片 Seg"""
        if isinstance(file, bytes):
            return Image(raw=file)

        if pconfig.use_base64:
            return Image(raw=file.read_bytes())
        else:
            return Image(path=file)

    @staticmethod
    def record_seg(audio_path: Path) -> Voice:
        """语音 Seg"""
        if pconfig.use_base64:
            return Voice(raw=audio_path.read_bytes())
        else:
            return Voice(path=audio_path)

    @classmethod
    def video_seg(
        cls,
        video_path: Path,
        thumbnail: Path | None = None,
    ) -> Video | File | Text:
        """视频 Seg"""
        # 检测文件大小
        file_size_byte_count = int(video_path.stat().st_size)
        if file_size_byte_count == 0:
            return Text("视频为空文件")
        elif file_size_byte_count > 100 * 1024 * 1024:
            # 转为文件 Seg(通过 URL, 避免超大文件上传)
            return cls.file_seg(video_path, display_name=video_path.name)
        elif file_size_byte_count > pconfig.video_url_size_threshold * 1024 * 1024:
            # 超过阈值, 使用 HTTP URL 直发, 避免跨机器传输大文件
            return Video(url=get_file_url(video_path))
        else:
            if pconfig.use_base64:
                video = Video(raw=video_path.read_bytes())
                if thumbnail and thumbnail.stat().st_size > 0:
                    video.thumbnail = cls.img_seg(thumbnail.read_bytes())
                return video
            else:
                video = Video(path=video_path)
                if thumbnail and thumbnail.stat().st_size > 0:
                    video.thumbnail = cls.img_seg(thumbnail)
                return video

    @staticmethod
    def file_seg(
        file: Path,
        display_name: str | None = None,
    ) -> File:
        """文件 Seg"""
        if not display_name:
            display_name = file.name

        if file.stat().st_size > pconfig.video_url_size_threshold * 1024 * 1024:
            # 超过阈值, 使用 HTTP URL 直发
            return File(url=get_file_url(file), name=display_name)

        if pconfig.use_base64:
            return File(raw=file.read_bytes(), name=display_name)
        else:
            return File(path=file, name=display_name)

    @classmethod
    async def message_reaction(
        cls,
        event: Event,
        status: Literal["fail", "resolving", "done"],
    ) -> None:
        """发送消息回应"""
        # 兼容旧版 alconna(如 0.54), 缺少 reaction API 时静默跳过
        if not all(
            hasattr(uniseg, attr)
            for attr in ("get_message_id", "get_target", "message_reaction")
        ):
            return

        message_id = uniseg.get_message_id(event)
        target = uniseg.get_target(event)

        emoji = EMOJI_MAP[status][0 if target.adapter in ID_ADAPTERS else 1]

        try:
            await uniseg.message_reaction(emoji, message_id=message_id)
        except Exception:
            logger.opt(exception=True).warning(f"reaction {emoji} to {message_id} failed, maybe not support")

    @classmethod
    def with_reaction(cls, func: Callable[..., Awaitable[Any]]):
        """自动回应装饰器"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            event = current_event.get()
            await cls.message_reaction(event, "resolving")

            try:
                result = await func(*args, **kwargs)
            # except TipException as e:
            #     await UniMessage.text(e.message).send()
            #     raise
            except Exception:
                await cls.message_reaction(event, "fail")
                raise

            await cls.message_reaction(event, "done")
            return result

        return wrapper
