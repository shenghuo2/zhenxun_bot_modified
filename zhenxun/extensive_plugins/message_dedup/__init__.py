from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.exception import FinishedException
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

from zhenxun.services.log import logger

from .config import CONFIG_DEFS, MODULE, get_cfg
from .db import close_db, init_db

__plugin_meta__ = PluginMetadata(
    name="消息查重",
    description="模块化消息查重：转发消息、B站视频、普通视频，均可独立开关",
    usage="""
    自动检测群内重复消息并提示，支持以下类型（均可通过配置独立开关）：
    1. 转发消息查重
    2. B站视频查重（标准链接、短链接、BV/AV号、JSON卡片、小程序）
    3. 普通视频消息查重

    命令：
    - #标记：回复一条消息，将其标记为已发送过（支持图片和B站视频）
    - #删除标记：回复一条消息，删除其标记记录（仅限超级用户）
    """,
    extra={
        "author": "shenghuo2",
        "version": "0.9.0",
        "plugin_type": "DEPENDANT",
        "menu_type": "其他",
        "configs": CONFIG_DEFS,
    },
)


# ── 规则：群白名单过滤 ───────────────────────────────────

async def _rule(session: Uninfo) -> bool:
    if not session.group:
        return False  # 只在群聊中生效
    whitelist = get_cfg("GROUP_WHITELIST")
    if whitelist:
        whitelist_str = {str(g) for g in whitelist}
        if str(session.group.id) not in whitelist_str:
            return False
    return True


# ── 主消息监听 ───────────────────────────────────────────

_matcher = on_message(priority=1, block=False, rule=_rule)


@_matcher.handle()
async def handle_message(event: MessageEvent, session: Uninfo, bot: Bot):
    message = event.message

    # 1. 转发消息查重
    if get_cfg("ENABLE_FORWARD_CHECK"):
        from .checkers.forward_checker import check_forward

        result = await check_forward(event, session, bot, message)
        if result is not False:
            if isinstance(result, bool):
                return  # 已处理，无重复
            # result 是 Message，发送重复提示
            try:
                await _matcher.finish(result)
            except FinishedException:
                pass
            except Exception as e:
                logger.error(f"发送转发查重回复失败: {e}", "message_dedup")
            return

    # 2. B站视频查重
    if get_cfg("ENABLE_BILIBILI_CHECK"):
        from .checkers.bilibili_checker import check_bilibili

        result = await check_bilibili(event, session, bot, message)
        if result is not False:
            if result is True:
                return  # 已处理，无重复
            try:
                await _matcher.finish(result)
            except FinishedException:
                pass
            except Exception as e:
                logger.error(f"发送B站查重回复失败: {e}", "message_dedup")
            return

    # 3. 普通视频消息查重
    if get_cfg("ENABLE_VIDEO_CHECK"):
        from .checkers.video_checker import check_video

        result = await check_video(event, session, bot, message)
        if result is not False:
            if result is True:
                return
            try:
                await _matcher.finish(result)
            except FinishedException:
                pass
            except Exception as e:
                logger.error(f"发送视频查重回复失败: {e}", "message_dedup")
            return


# ── 注册 #标记 / #删除标记（导入即注册） ──────────────────

from .checkers import mark_commands as _mark  # noqa: F401, E402

# ── 生命周期 ─────────────────────────────────────────────

driver = get_driver()
driver.on_startup(init_db)
driver.on_shutdown(close_db)
