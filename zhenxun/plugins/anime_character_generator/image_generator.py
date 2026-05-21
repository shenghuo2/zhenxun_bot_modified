"""NovelAI 图像生成"""

import re
from pathlib import Path

try:
    from novelai_python import ApiCredential, GenerateImageInfer, ImageGenerateResp
    from novelai_python.sdk.ai.generate_image import Model, Sampler, UCPreset
    from pydantic import SecretStr
except ImportError:
    ApiCredential = None
    GenerateImageInfer = None
    ImageGenerateResp = None
    Model = None
    Sampler = None
    UCPreset = None
    SecretStr = None

from nonebot import logger

from .config import config


def _sanitize_filename(text: str, max_length: int = 50) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", text)
    # 限制长度
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized.strip()


async def generate_image(prompt: str, save_path: str | None = None) -> str | None:
    """生成图像

    Args:
        prompt: 提示词
        save_path: 保存路径，可选（如果不提供，将自动生成到 image_cache 文件夹）

    Returns:
        保存的图像文件路径，失败返回None
    """

    if not ApiCredential:
        logger.error("novelai_python 库未安装")
        return None

    if not config.api_token:
        logger.error("API Token 未配置")
        return None

    try:
        if not config.api_token or not GenerateImageInfer:
            logger.warning("图像生成功能已禁用")
            return None
        session = ApiCredential(api_token=SecretStr(config.api_token))

        gen = GenerateImageInfer.build_generate(
            prompt=prompt,
            model=Model.NAI_DIFFUSION_4_5_CURATED,
            sampler=Sampler.K_EULER_ANCESTRAL,
            ucPreset=UCPreset.TYPE0,
            qualityToggle=True,
            variety_boost=True,
            steps=28,
        )

        resp: ImageGenerateResp = await gen.request(session=session)

        if resp.files:
            file_name, file_data = resp.files[0]

            # 获取 seed 信息
            seed = "unknown"
            try:
                # 使用 ImageGenerateResp 的 query_params 方法获取 seed
                seed = resp.query_params("seed", "unknown")
            except Exception:
                # 如果 query_params 方法失败，尝试其他方式
                if (
                    hasattr(resp, "meta")
                    and hasattr(resp.meta, "raw_request")
                    and resp.meta.raw_request
                ):
                    seed = resp.meta.raw_request.get("seed", "unknown")
                elif hasattr(resp, "meta") and hasattr(resp.meta, "parameters"):
                    seed = getattr(resp.meta.parameters, "seed", "unknown")
                elif hasattr(resp, "meta"):
                    seed = getattr(resp.meta, "seed", "unknown")

            # 如果没有提供保存路径，自动生成
            if not save_path:
                # 创建 image_cache 文件夹（相对于脚本位置）
                script_dir = Path(__file__).parent
                cache_dir = script_dir / "image_cache"
                cache_dir.mkdir(exist_ok=True)

                # 清理 prompt 用于文件名
                clean_prompt = _sanitize_filename(prompt)

                # 生成文件名：seed_prompt.png
                filename = f"{seed}_{clean_prompt}.png"
                save_path = cache_dir / filename

            # 确保父目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(save_path, "wb") as f:
                f.write(file_data)

            logger.success(f"图像已保存: {save_path}")
            return str(save_path)

    except Exception as e:
        logger.error(f"生成图像失败: {e}")

    return None


async def test_generate():
    """测试生成"""
    if not config.api_token:
        print("请先配置 API Token")
        return None

    result = await generate_image("1girl, anime, beautiful")
    if result:
        print(f"生成成功，保存到: {result}")
        return result
    else:
        print("生成失败")
        return None


# if __name__ == "__main__":
#     asyncio.run(test_generate())
