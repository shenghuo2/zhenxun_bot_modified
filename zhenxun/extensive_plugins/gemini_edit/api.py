"""
Gemini API 调用模块 - 解耦设计
支持图片编辑和生成
"""

import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .config import GEMINI_API_BASE, GEMINI_API_KEY, GEMINI_MODEL


@dataclass
class GeminiResponse:
    """Gemini API 响应结构"""

    text: str
    image_urls: list[str]  # URL 或 base64 数据
    image_base64_list: list[str]  # base64 图片数据
    total_tokens: int
    duration: float


class GeminiClient:
    """Gemini API 客户端"""

    def __init__(
        self,
        api_base: str = GEMINI_API_BASE,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        text: str,
        image_base64_list: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> GeminiResponse:
        """
        发送聊天请求

        Args:
            text: 用户输入的文本
            image_base64_list: 可选的图片 base64 列表（格式: data:image/jpeg;base64,...）
            system_prompt: 可选的系统提示词

        Returns:
            GeminiResponse: 包含回复文本、图片URL列表、token数和耗时
        """
        messages = []

        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 构建用户消息内容
        if image_base64_list:
            # 多模态消息：使用数组格式
            content: list[dict[str, Any]] = []
            if text:
                content.append({"type": "text", "text": text})
            for img_b64 in image_base64_list:
                content.append({"type": "image_url", "image_url": {"url": img_b64}})
            messages.append({"role": "user", "content": content})
        else:
            # 纯文本消息：使用字符串格式
            messages.append({"role": "user", "content": text})

        url = f"{self.api_base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": messages,
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=data)

        duration = time.time() - start_time

        # 检查响应状态
        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"API 请求失败 ({response.status_code}): {error_text}")

        result = response.json()

        # 检查是否有错误
        if "error" in result:
            raise Exception(f"API 错误: {result['error']}")

        # 解析响应
        total_tokens = 0
        usage = result.get("usage")
        if usage:
            total_tokens = usage.get("total_tokens", 0)

        response_text = ""
        response_images = []
        response_base64 = []

        choices = result.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            response_text = message.get("content", "")

            # 提取图片 URL 和 base64 数据
            response_images = self._extract_image_urls(response_text)
            response_base64 = self._extract_base64_images(response_text)

        return GeminiResponse(
            text=response_text,
            image_urls=response_images,
            image_base64_list=response_base64,
            total_tokens=total_tokens,
            duration=duration,
        )

    @staticmethod
    def _extract_image_urls(text: str) -> list[str]:
        """从文本中提取图片 URL"""
        # 匹配常见图片 URL 模式
        patterns = [
            # 通用 URL（不限扩展名，因为有些图片 URL 没有扩展名）
            r'https?://[^\s<>"{}|\\^`\[\]\)]+',
            # Markdown 图片格式 ![...](url)
            r"!\[.*?\]\((https?://[^\s\)]+)\)",
        ]

        urls = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)

        # 过滤掉明显不是图片的 URL
        image_urls = []
        for url in urls:
            # 清理 URL 末尾的标点符号
            url = url.rstrip(".,;:!?")
            # 检查是否可能是图片 URL
            if any(
                ext in url.lower()
                for ext in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".webp",
                    "image",
                    "img",
                    "photo",
                ]
            ):
                image_urls.append(url)
            elif "/images/" in url or "/image/" in url or "cdn" in url:
                image_urls.append(url)

        return list(set(image_urls))  # 去重

    @staticmethod
    def _extract_base64_images(text: str) -> list[str]:
        """从文本中提取 base64 图片数据"""
        # 匹配 Markdown 格式的 base64 图片: ![...](data:image/...;base64,...)
        pattern = r"!\[.*?\]\((data:image/[^;]+;base64,[A-Za-z0-9+/=]+)\)"
        matches = re.findall(pattern, text)
        return matches


# 默认客户端实例
default_client = GeminiClient()


async def download_image_as_base64(url: str) -> str | None:
    """
    下载图片并转换为 base64 格式

    Args:
        url: 图片 URL

    Returns:
        str: base64 编码的图片（格式: data:image/jpeg;base64,...）
    """
    import base64

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                content = response.content
                # 检测图片类型
                content_type = response.headers.get("content-type", "image/jpeg")
                if "png" in content_type:
                    mime_type = "image/png"
                elif "gif" in content_type:
                    mime_type = "image/gif"
                elif "webp" in content_type:
                    mime_type = "image/webp"
                else:
                    mime_type = "image/jpeg"
                # 转换为 base64
                b64_data = base64.b64encode(content).decode("utf-8")
                return f"data:{mime_type};base64,{b64_data}"
    except Exception:
        pass
    return None


async def gemini_chat(
    text: str,
    image_base64_list: list[str] | None = None,
    system_prompt: str | None = None,
) -> GeminiResponse:
    """
    便捷函数：使用默认客户端发送聊天请求

    Args:
        text: 用户输入的文本
        image_base64_list: 可选的图片 base64 列表
        system_prompt: 可选的系统提示词

    Returns:
        GeminiResponse: 响应结果
    """
    return await default_client.chat(text, image_base64_list, system_prompt)
