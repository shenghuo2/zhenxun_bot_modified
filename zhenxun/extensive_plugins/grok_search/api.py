"""
Grok API 调用模块 - 解耦设计
支持文本和图片输入，支持图片生成
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
from nonebot.log import logger

from .config import (GROK_API_BASE, GROK_API_KEY, GROK_MODEL,
                     load_runtime_config, save_runtime_config)

# 当前使用的模型（运行时可修改）
_runtime_config = load_runtime_config()
current_search_model: str = _runtime_config["search_model"]
current_edit_model: str = _runtime_config["edit_model"]


@dataclass
class GrokResponse:
    """Grok API 响应结构"""

    text: str
    image_urls: list[str]
    total_tokens: int
    duration: float


@dataclass
class GrokModel:
    """Grok 模型信息"""

    id: str
    owned_by: str | None = None


class GrokClient:
    """Grok API 客户端"""

    def __init__(
        self,
        api_base: str = GROK_API_BASE,
        api_key: str = GROK_API_KEY,
        model: str = GROK_MODEL,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        text: str,
        image_base64_list: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> GrokResponse:
        """
        发送聊天请求

        Args:
            text: 用户输入的文本
            image_base64_list: 可选的图片 base64 列表（格式: data:image/jpeg;base64,...）
            system_prompt: 可选的系统提示词

        Returns:
            GrokResponse: 包含回复文本、图片URL列表、token数和耗时
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
            error_text = self._format_response_debug(response)
            raise Exception(f"API 请求失败 ({response.status_code}): {error_text}")

        result = self._parse_response_json(response)

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

        choices = result.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            response_text = self._extract_text_content(message.get("content", ""))

            # 检查是否有图片 URL
            response_images = self._extract_image_urls(response_text)

        return GrokResponse(
            text=response_text,
            image_urls=response_images,
            total_tokens=total_tokens,
            duration=duration,
        )

    @staticmethod
    def _format_response_debug(response: httpx.Response, max_len: int = 500) -> str:
        """格式化响应信息，便于排查非预期响应"""
        content_type = response.headers.get("content-type", "unknown")
        body = response.text.strip() or "<empty>"
        if len(body) > max_len:
            body = f"{body[:max_len]}...(truncated)"
        return f"content-type={content_type}, body={body}"

    def _parse_response_json(self, response: httpx.Response) -> dict[str, Any]:
        """解析响应 JSON，兼容空体/非 JSON/SSE 流式格式"""
        raw_text = response.text.strip()
        content_type = response.headers.get("content-type", "unknown")

        if not raw_text:
            raise Exception(
                f"API 返回空响应 (status={response.status_code}, content-type={content_type})"
            )

        try:
            result = response.json()
            if isinstance(result, dict):
                return result
            raise Exception(f"API 响应格式异常: 根节点类型为 {type(result).__name__}")
        except json.JSONDecodeError:
            pass

        sse_result = self._parse_sse_response(raw_text)
        if sse_result is not None:
            return sse_result

        snippet = raw_text[:500]
        if len(raw_text) > 500:
            snippet += "...(truncated)"
        raise Exception(
            f"API 返回非 JSON 数据 (status={response.status_code}, "
            f"content-type={content_type}): {snippet}"
        )

    @staticmethod
    def _parse_sse_response(raw_text: str) -> dict[str, Any] | None:
        """尝试解析 text/event-stream 响应并转成标准 chat/completions 结构"""
        if "data:" not in raw_text:
            return None

        events: list[dict[str, Any]] = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)

        if not events:
            return None

        # 若单条事件本身就是完整 JSON，直接返回
        if len(events) == 1 and isinstance(events[0].get("choices"), list):
            return events[0]

        merged_text_parts: list[str] = []
        usage: dict[str, Any] = {}

        for event in events:
            event_usage = event.get("usage")
            if isinstance(event_usage, dict):
                usage = event_usage

            choices = event.get("choices")
            if not isinstance(choices, list) or not choices:
                continue
            first = choices[0]
            if not isinstance(first, dict):
                continue

            # 非流式的 message 内容
            message = first.get("message")
            if isinstance(message, dict):
                full_text = GrokClient._extract_text_content(message.get("content", ""))
                if full_text:
                    merged_text_parts = [full_text]
                    continue

            # 流式的 delta 内容
            delta = first.get("delta")
            if isinstance(delta, dict):
                delta_text = GrokClient._extract_text_content(delta.get("content", ""))
                if delta_text:
                    merged_text_parts.append(delta_text)

        merged_text = "".join(merged_text_parts).strip()
        return {
            "choices": [{"message": {"content": merged_text}}],
            "usage": usage,
        }

    @staticmethod
    def _extract_text_content(content: Any) -> str:
        """兼容字符串和多段结构化 content，统一提取为文本"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if not isinstance(item, dict):
                    continue
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts)

        return ""

    @staticmethod
    def _extract_image_urls(text: str) -> list[str]:
        """从文本中提取图片 URL"""
        # 匹配常见图片 URL 模式
        patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s<>"{}|\\^`\[\]]*)?',
            r"!\[.*?\]\((https?://[^\s)]+)\)",  # Markdown 图片格式
        ]

        urls = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)

        return list(set(urls))  # 去重

    async def list_models(self) -> list[GrokModel]:
        """获取 /v1/models 模型列表。"""
        url = f"{self.api_base}/v1/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            error_text = self._format_response_debug(response)
            raise Exception(f"获取模型列表失败 ({response.status_code}): {error_text}")

        result = self._parse_response_json(response)
        if "error" in result:
            raise Exception(f"API 错误: {result['error']}")

        return self._parse_models_response(result)

    @staticmethod
    def _parse_models_response(result: dict[str, Any]) -> list[GrokModel]:
        """兼容 OpenAI 风格和简单列表风格的模型列表响应。"""
        raw_models = result.get("data", result.get("models", []))
        if isinstance(raw_models, dict):
            raw_models = list(raw_models.values())
        if not isinstance(raw_models, list):
            return []

        models: list[GrokModel] = []
        seen: set[str] = set()
        for item in raw_models:
            model_id = ""
            owned_by = None
            if isinstance(item, str):
                model_id = item.strip()
            elif isinstance(item, dict):
                raw_id = item.get("id") or item.get("name") or item.get("model")
                if isinstance(raw_id, str):
                    model_id = raw_id.strip()
                raw_owned_by = item.get("owned_by") or item.get("owner")
                if isinstance(raw_owned_by, str) and raw_owned_by.strip():
                    owned_by = raw_owned_by.strip()

            if model_id and model_id not in seen:
                models.append(GrokModel(id=model_id, owned_by=owned_by))
                seen.add(model_id)

        return models

    async def generate_image(
        self,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
    ) -> GrokResponse:
        """
        生成图片

        Args:
            prompt: 图片描述文本
            n: 生成图片数量
            size: 图片尺寸

        Returns:
            GrokResponse: 包含图片URL列表
        """
        url = f"{self.api_base}/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "size": size,
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=data)

        duration = time.time() - start_time

        if response.status_code != 200:
            error_text = self._format_response_debug(response)
            raise Exception(f"图片生成失败 ({response.status_code}): {error_text}")

        result = self._parse_response_json(response)

        if "error" in result:
            raise Exception(f"API 错误: {result['error']}")

        # 提取图片 URLs
        image_urls = []
        data_list = result.get("data", [])
        for item in data_list:
            if isinstance(item, dict) and "url" in item:
                image_urls.append(item["url"])

        return GrokResponse(
            text="",
            image_urls=image_urls,
            total_tokens=0,
            duration=duration,
        )

    async def edit_image(
        self,
        image_base64: str,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
    ) -> GrokResponse:
        """
        编辑图片

        Args:
            image_base64: 原始图片的 base64 编码
            prompt: 编辑描述文本
            n: 生成图片数量
            size: 图片尺寸

        Returns:
            GrokResponse: 包含图片URL列表
        """
        url = f"{self.api_base}/v1/images/edits"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "image": image_base64,
            "prompt": prompt,
            "n": n,
            "size": size,
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=data)

        duration = time.time() - start_time

        if response.status_code != 200:
            error_text = self._format_response_debug(response)
            raise Exception(f"图片编辑失败 ({response.status_code}): {error_text}")

        result = self._parse_response_json(response)

        if "error" in result:
            raise Exception(f"API 错误: {result['error']}")

        # 提取图片 URLs
        image_urls = []
        data_list = result.get("data", [])
        for item in data_list:
            if isinstance(item, dict) and "url" in item:
                image_urls.append(item["url"])

        return GrokResponse(
            text="",
            image_urls=image_urls,
            total_tokens=0,
            duration=duration,
        )


# 默认客户端实例
default_client = GrokClient(model=current_search_model)


def get_search_model() -> str:
    """获取搜索使用的模型"""
    return current_search_model


def set_search_model(model: str) -> None:
    """设置搜索使用的模型"""
    global current_search_model
    current_search_model = model
    save_runtime_config(current_search_model, current_edit_model)


def get_edit_model() -> str:
    """获取改图使用的模型"""
    return current_edit_model


def set_edit_model(model: str) -> None:
    """设置改图使用的模型"""
    global current_edit_model
    current_edit_model = model
    save_runtime_config(current_search_model, current_edit_model)


# 向后兼容的函数
def get_current_model() -> str:
    """获取当前使用的模型（向后兼容）"""
    return current_search_model


def set_current_model(model: str) -> None:
    """设置当前使用的模型（向后兼容）"""
    set_search_model(model)


def _get_client(model: str | None = None) -> GrokClient:
    """按需创建指定模型客户端，避免并发请求互相改写默认客户端状态。"""
    if model:
        return GrokClient(model=model)
    return default_client


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
            logger.warning(f"图片下载失败 status={response.status_code}, url={url[:120]}")
    except Exception as e:
        logger.warning(f"图片下载异常 url={url[:120]}: {e}")
    return None


async def grok_chat(
    text: str,
    image_base64_list: list[str] | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
) -> GrokResponse:
    """
    便捷函数：使用默认客户端发送聊天请求

    Args:
        text: 用户输入的文本
        image_base64_list: 可选的图片 base64 列表
        model: 可选的模型名称，不指定则使用当前模型
        system_prompt: 可选的系统提示词

    Returns:
        GrokResponse: 响应结果
    """
    client = _get_client(model)
    return await client.chat(text, image_base64_list, system_prompt)


async def grok_generate_image(
    prompt: str,
    model: str | None = None,
    n: int = 1,
    size: str = "1024x1024",
) -> GrokResponse:
    """
    便捷函数：生成图片

    Args:
        prompt: 图片描述文本
        model: 可选的模型名称，不指定则使用当前改图模型
        n: 生成图片数量
        size: 图片尺寸

    Returns:
        GrokResponse: 响应结果
    """
    client = _get_client(model)
    return await client.generate_image(prompt, n, size)


async def grok_edit_image(
    image_base64: str,
    prompt: str,
    model: str | None = None,
    n: int = 1,
    size: str = "1024x1024",
) -> GrokResponse:
    """
    便捷函数：编辑图片

    Args:
        image_base64: 原始图片的 base64 编码
        prompt: 编辑描述文本
        model: 可选的模型名称，不指定则使用当前改图模型
        n: 生成图片数量
        size: 图片尺寸

    Returns:
        GrokResponse: 响应结果
    """
    client = _get_client(model)
    return await client.edit_image(image_base64, prompt, n, size)


async def grok_list_models() -> list[GrokModel]:
    """便捷函数：获取可用模型列表"""
    return await default_client.list_models()
