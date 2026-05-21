"""
GPT-Image-2 API 客户端
支持 txt2img (/images/generations) 和 img2img (/images/edits)
"""

from dataclasses import dataclass, field
import time
from typing import Any

import httpx

from .config import REQUEST_TIMEOUT


@dataclass
class ImageGenerationResult:
    images: list[str] = field(default_factory=list)
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration: float = 0.0


class GPTImageClient:
    def __init__(self, provider: dict):
        self.name = provider["name"]
        self.base_url = provider["base_url"].rstrip("/")
        self.api_key = provider["api_key"]
        self.model = provider["model"]
        self.returns_b64 = provider.get("returns_b64", True)

    async def txt2img(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "medium",
        n: int = 1,
    ) -> ImageGenerationResult:
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }

        start_time = time.time()
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)

        duration = time.time() - start_time

        if resp.status_code != 200:
            body = resp.text[:200]
            raise Exception(f"[{self.name}] API 请求失败 ({resp.status_code}): {body}")

        data = resp.json()
        if "error" in data:
            raise Exception(f"[{self.name}] API 错误: {data['error']}")

        images, total_tokens, prompt_tokens, completion_tokens = self._parse_response(
            data
        )
        return ImageGenerationResult(
            images=images,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration=duration,
        )

    async def img2img(
        self,
        prompt: str,
        image_datas: list[tuple[bytes, str]],
        size: str = "1024x1024",
        quality: str = "medium",
        n: int = 1,
    ) -> ImageGenerationResult:
        url = f"{self.base_url}/images/edits"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        data_fields: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": str(n),
        }

        # 构建 multipart 上传
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for key, value in data_fields.items():
            files.append((key, (None, str(value).encode(), "text/plain")))

        for i, (img_bytes, mime_type) in enumerate(image_datas):
            ext = mime_type.split("/")[-1] if "/" in mime_type else "jpg"
            filename = f"image_{i + 1}.{ext}"
            files.append(("image", (filename, img_bytes, mime_type)))

        start_time = time.time()
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, files=files)

        duration = time.time() - start_time

        if resp.status_code != 200:
            body = resp.text[:200]
            raise Exception(f"[{self.name}] API 请求失败 ({resp.status_code}): {body}")

        data = resp.json()
        if "error" in data:
            raise Exception(f"[{self.name}] API 错误: {data['error']}")

        images, total_tokens, prompt_tokens, completion_tokens = self._parse_response(
            data
        )
        return ImageGenerationResult(
            images=images,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration=duration,
        )

    def _parse_response(self, data: dict) -> tuple[list[str], int, int, int]:
        images = []
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        usage = data.get("usage", {})
        if usage:
            total_tokens = usage.get("total_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            completion_tokens = usage.get(
                "completion_tokens", usage.get("output_tokens", 0)
            )

        for item in data.get("data", []):
            b64 = item.get("b64_json")
            if b64:
                images.append(f"base64://{b64}")
            else:
                url = item.get("url")
                if url:
                    images.append(url)

        return images, total_tokens, prompt_tokens, completion_tokens


async def download_image_bytes(url: str) -> tuple[bytes, str] | None:
    """下载 QQ 图片, 返回 (bytes, mime_type) 用于 multipart 上传"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                if ";" in content_type:
                    content_type = content_type.split(";")[0].strip()
                return resp.content, content_type
    except Exception:
        pass
    return None


def find_provider(name: str) -> dict | None:
    from .config import PROVIDERS

    for p in PROVIDERS:
        if p["name"] == name:
            return p
    return None
