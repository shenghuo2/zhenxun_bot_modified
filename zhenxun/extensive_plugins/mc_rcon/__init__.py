"""
Minecraft RCON 白名单管理插件
命令: #白名单操作 [列表|添加|删除] {id}
"""

from mcrcon import MCRcon
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .config import ALLOWED_GROUP_IDS, RCON_HOST, RCON_PASSWORD, RCON_PORT, SERVER_NAME

__plugin_meta__ = PluginMetadata(
    name="MC白名单管理",
    description="通过 RCON 管理 Minecraft 服务器白名单",
    usage="#白名单操作 [列表|添加|删除] {id}",
    extra=PluginExtraData(
        author="",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#白名单操作 [列表|添加|删除] {id}"),
        ],
    ).to_dict(),
)


def _check_group(event: MessageEvent) -> bool:
    """检查是否在允许的群中"""
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.group_id in ALLOWED_GROUP_IDS


def _rcon_command(cmd: str) -> str:
    """执行 RCON 命令并返回响应"""
    with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
        return mcr.command(cmd)


def _format_msg(content: str) -> str:
    """格式化输出消息，带服务器名称前缀"""
    return f"【{SERVER_NAME}】白名单操作\n{content}"


_whitelist_cmd = on_command("#白名单操作", priority=5, block=True)

USAGE_TEXT = "命令格式: #白名单操作 [列表|添加|删除] {id}\n- 列表: 查看白名单\n- 添加 <玩家ID>: 添加白名单\n- 删除 <玩家ID>: 移除白名单（仅管理员）"


@_whitelist_cmd.handle()
async def handle_whitelist(bot: Bot, event: MessageEvent):
    # 检查群权限
    if not _check_group(event):
        return

    raw_text = event.get_message().extract_plain_text().strip()
    args = raw_text.replace("#白名单操作", "").strip().split()

    # 无参数，提示用法
    if not args:
        await _whitelist_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(_format_msg(USAGE_TEXT))
            )
        )
        return

    action = args[0]
    player_id = args[1] if len(args) > 1 else None

    if action == "列表":
        await _handle_list(event)
    elif action == "添加":
        await _handle_add(event, player_id)
    elif action == "删除":
        await _handle_remove(bot, event, player_id)
    else:
        await _whitelist_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(_format_msg(USAGE_TEXT))
            )
        )


async def _handle_list(event: MessageEvent):
    """处理白名单列表查询"""
    try:
        response = _rcon_command("whitelist list")
        # 解析响应: "There are N whitelisted player(s): p1, p2, p3"
        if ":" in response:
            parts = response.split(":", 1)
            players = parts[1].strip()
            if players:
                content = f"白名单列表:\n{players}"
            else:
                content = "白名单列表为空"
        elif "no whitelisted" in response.lower() or "0 whitelisted" in response.lower():
            content = "白名单列表为空"
        else:
            content = f"白名单列表:\n{response}"
    except Exception as e:
        logger.exception(f"RCON 白名单列表查询失败: {e}")
        content = f"查询失败: {e}"

    await _whitelist_cmd.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(_format_msg(content))
        )
    )


async def _handle_add(event: MessageEvent, player_id: str | None):
    """处理添加白名单"""
    if not player_id:
        await _whitelist_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(
                    _format_msg("请指定要添加的玩家ID\n用法: #白名单操作 添加 <玩家ID>")
                )
            )
        )
        return

    try:
        response = _rcon_command(f"whitelist add {player_id}")
        # 解析响应: "Added xxx to the whitelist"
        if "Added" in response and "whitelist" in response:
            content = f"添加成功: {player_id}"
        else:
            content = f"添加失败: {response}"
    except Exception as e:
        logger.exception(f"RCON 白名单添加失败: {e}")
        content = f"添加失败: {e}"

    await _whitelist_cmd.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(_format_msg(content))
        )
    )


async def _handle_remove(bot: Bot, event: MessageEvent, player_id: str | None):
    """处理移除白名单（需要 superuser 权限）"""
    # 检查 superuser 权限
    if not await SUPERUSER(bot, event):
        await _whitelist_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(_format_msg("删除白名单需要管理员权限"))
            )
        )
        return

    if not player_id:
        await _whitelist_cmd.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(
                    _format_msg("请指定要删除的玩家ID\n用法: #白名单操作 删除 <玩家ID>")
                )
            )
        )
        return

    try:
        response = _rcon_command(f"whitelist remove {player_id}")
        # 解析响应: "Removed xxx from the whitelist"
        if "Removed" in response and "whitelist" in response:
            content = f"移除成功: {player_id}"
        else:
            content = f"移除失败: {response}"
    except Exception as e:
        logger.exception(f"RCON 白名单移除失败: {e}")
        content = f"移除失败: {e}"

    await _whitelist_cmd.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(_format_msg(content))
        )
    )
