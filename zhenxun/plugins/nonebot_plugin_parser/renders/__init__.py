import importlib

from nonebot import logger

from .base import BaseRenderer
from .default import DefaultRenderer

RENDERER: type[BaseRenderer] | None = None

from ..config import pconfig
from ..constants import RenderType
from ..utils import is_module_available


def _load_common_renderer() -> type[BaseRenderer]:
    try:
        from .common import CommonRenderer

        return CommonRenderer
    except ImportError:
        logger.warning("common 渲染器依赖缺失(需要 apilmoji/pillow>=11), 已回退到 default 渲染器")
        return DefaultRenderer


match pconfig.render_type:
    case RenderType.common:
        RENDERER = _load_common_renderer()
    case RenderType.default:
        RENDERER = DefaultRenderer
    case RenderType.htmlrender:
        if is_module_available("nonebot_plugin_htmlrender"):
            from .htmlrender import HtmlRenderer

            RENDERER = HtmlRenderer
        else:
            logger.warning("未安装 `nonebot_plugin_htmlrender`, 已回退到 common 渲染器")
            RENDERER = _load_common_renderer()
    case RenderType.htmlkit:
        logger.warning("htmlkit 渲染器尚实现，已回退到 default 渲染器")
        RENDERER = DefaultRenderer


def get_renderer(platform: str) -> type[BaseRenderer]:
    """根据平台名称获取对应的 Renderer 类"""
    if RENDERER:
        return RENDERER

    module = importlib.import_module("." + platform, package=__name__)
    return getattr(module, "Renderer")
