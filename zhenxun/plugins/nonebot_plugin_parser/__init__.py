import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import nonebot
from nonebot import get_driver, logger, require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")

from .config import Config, pconfig
from .matchers import clear_result_cache
from .utils import FILE_ROUTE_PREFIX, safe_unlink

__plugin_meta__ = PluginMetadata(
    name="链接分享解析 Alconna 版",
    description="支持B站|抖音|快手|微博|小红书|YouTube|TikTok|Twitter|AcFun|NGA",
    usage=(
        "发送支持平台的(BV号/链接/小程序/卡片)即可\n"
        "其他命令:\n"
        "  bm BV号 <分集> (下载B站音频)\n"
        "  ym 链接 (下载油管音频)\n"
        "  blogin (扫码获取B站凭据)"
    ),
    type="application",
    homepage="https://github.com/fllesser/nonebot-plugin-parser",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna", "nonebot_plugin_uninfo"),
    extra={
        "author": "fllesser",
        "email": "fllessive@gmail.com",
        "homepage": "https://github.com/fllesser/nonebot-plugin-parser",
    },
)

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

file_router = APIRouter(prefix=FILE_ROUTE_PREFIX)


@file_router.get("/{filename}")
async def download_file(filename: str):
    cache_dir = pconfig.cache_dir.resolve()
    file = (cache_dir / filename).resolve()
    if file.parent != cache_dir or not file.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(file, filename=filename)


@get_driver().on_startup
async def _():
    nonebot.get_app().include_router(file_router)


@scheduler.scheduled_job("cron", hour=1, minute=0, id="parser-clean-local-cache")
async def clean_plugin_cache():
    try:
        files = [f for f in pconfig.cache_dir.iterdir() if f.is_file()]
        if not files:
            logger.info("No cache files to clean")
            return

        # 并发删除文件
        tasks = [safe_unlink(file) for file in files]
        await asyncio.gather(*tasks)

        logger.success(f"Successfully cleaned {len(files)} cache files")
    except Exception:
        logger.exception("Error while cleaning cache files")

    # 资源清理完毕后，清理 result 缓存
    clear_result_cache()
