"""NovelAI 配置"""

from pydantic import BaseModel


class NovelAIConfig(BaseModel):
    """NovelAI 配置"""

    api_token: str = "pst-V7xHX4Kf55ryIqLS6y1qk9uYF1Cpd9hkN3R0UWGf52GZ5YMaezX4ptkqiNYexpuV"  # NovelAI API Token
    default_model: str = "nai-diffusion-4-5-curated"  # 默认模型
    enable_image_generation: bool = True  # 是否启用图像生成功能


# 全局配置实例
config = NovelAIConfig()


def update_config(api_token: str = "", enable: bool = True) -> None:
    """更新配置"""
    global config
    if api_token:
        config.api_token = api_token
        config.enable_image_generation = enable


def is_configured() -> bool:
    """检查是否已配置"""
    return bool(config.api_token and config.enable_image_generation)
