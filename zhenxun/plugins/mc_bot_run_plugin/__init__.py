import json
import os
from pathlib import Path
import tempfile
import time
import traceback

from arclet.alconna import Alconna, Args
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import MultiVar, on_alconna
from nonebot_plugin_session import EventSession
import paramiko

from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

__plugin_meta__ = PluginMetadata(
    name="MC Bot运行插件",
    description="通过SSH发送MC命令到远程服务器",
    usage="""
    usage：
        通过SSH发送MC命令到远程服务器
        
        用户命令：
            #mcrun <mcid> <command>
        支持的命令：
            spawn - 生成/重生命令
            kill - 停止命令
        示例：
            #mcrun player123 spawn
            #mcrun admin kill
        
        管理员命令（仅超级用户）：
            #mcrun_whitelist list - 查看白名单
            #mcrun_whitelist add <用户ID> - 添加用户到白名单
            #mcrun_whitelist remove <用户ID> - 从白名单移除用户
        
        注意：只有白名单中的用户才能使用 #mcrun 命令，且仅支持 spawn 和 kill 命令
    """.strip(),  # noqa: W293
    extra={"author": "shenghuo2", "version": "0.1.1", "configs": []},
)

# SSH配置
SSH_HOST = "host"
SSH_USER = "username"
# 如果使用密钥认证，设置密钥路径
SSH_KEY_PATH = Path(__file__).parent / "id_rsa"

# 白名单文件路径
WHITELIST_FILE = Path(__file__).parent / "whitelist.json"


def load_whitelist() -> set[str]:
    """加载白名单"""
    try:
        if WHITELIST_FILE.exists():
            with open(WHITELIST_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("users", []))
        return set()
    except Exception as e:
        logger.error(f"加载白名单失败: {e}", "MC Bot运行插件")
        return set()


def save_whitelist(whitelist: set[str]) -> bool:
    """保存白名单"""
    try:
        data = {"users": list(whitelist)}
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存白名单失败: {e}", "MC Bot运行插件")
        return False


def is_user_in_whitelist(user_id: str) -> bool:
    """检查用户是否在白名单中"""
    whitelist = load_whitelist()
    return user_id in whitelist


# MC Bot运行命令
mc_run_matcher = on_alconna(
    Alconna("#mcrun", Args["mcid", str]["command", MultiVar(str, "+")]),
    priority=5,
    block=True,
)


@mc_run_matcher.handle()
async def handle_mc_run(session: EventSession, mcid: str, command: list[str]):
    """处理MC运行命令"""
    try:
        # 获取用户信息
        user_id = session.id1 or "unknown"

        # 检查用户是否在白名单中
        if not is_user_in_whitelist(user_id):
            await MessageUtils.build_message(
                "❌ 权限不足！\n您不在白名单中，无法使用此命令。\n请联系管理员添加您到白名单。"
            ).send(reply_to=True)
            return

        # 将命令列表转换为字符串
        command_str = " ".join(command)

        if not mcid.strip() or not command_str.strip():
            await MessageUtils.build_message(
                "❌ 参数不能为空！\n正确格式：#mcrun <mcid> <command>"
            ).send(reply_to=True)
            return

        # 验证命令是否为允许的命令
        allowed_commands = ["spawn", "kill"]
        first_command = command[0].lower() if command else ""

        if first_command not in allowed_commands:
            await MessageUtils.build_message(
                f"❌ 不允许的命令！\n仅支持以下命令：{', '.join(allowed_commands)}\n当前命令：{first_command}"
            ).send(reply_to=True)
            return

        # 创建临时文件，指定临时目录避免权限问题
        temp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(temp_dir, f"mcbot_{mcid}_{int(time.time())}.txt")

        # 写入命令字符串到临时文件
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(f"{command_str}\n")

        try:
            # 使用paramiko进行SFTP文件传输
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )  # 自动接受主机密钥

            # 连接到SSH服务器
            if SSH_KEY_PATH and os.path.exists(SSH_KEY_PATH):
                ssh.connect(
                    SSH_HOST,
                    username=SSH_USER,
                    key_filename=str(SSH_KEY_PATH),
                    timeout=30,
                )
            else:
                ssh.connect(SSH_HOST, username=SSH_USER, timeout=30)

            # 使用SFTP上传文件
            sftp = ssh.open_sftp()
            remote_path = f"/home/{SSH_USER}/mc_bot/{mcid}.txt"
            sftp.put(tmp_file_path, remote_path)
            sftp.close()
            ssh.close()

            await MessageUtils.build_message(
                f"✅ MC命令发送成功！\n📋 MCID: {mcid}\n💬 命令: {command_str}\n🌐 已发送到: {SSH_HOST}"
            ).send(reply_to=True)

            logger.info(
                f"用户 {user_id} 成功发送MC命令: {mcid} {command_str}",
                "MC Bot运行插件",
            )

        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"清理临时文件失败: {cleanup_error}", "MC Bot运行插件")

    except Exception as e:
        error_details = traceback.format_exc()
        await MessageUtils.build_message(
            f"❌ 执行失败！\n错误信息: {e!s}\n\n详细错误:\n{error_details}"
        ).send(reply_to=True)
        logger.error(
            f"MC命令执行异常: {e}\n详细错误: {error_details}", "MC Bot运行插件"
        )


# 白名单管理命令（仅超级用户）
whitelist_matcher = on_alconna(
    Alconna("#mcrun_whitelist", Args["action", str]["user_id?", str]),
    priority=5,
    block=True,
    permission=SUPERUSER,
)


@whitelist_matcher.handle()
async def handle_whitelist(
    session: EventSession, action: str, user_id: str | None = None
):
    """处理白名单管理命令"""
    try:
        action = action.lower()

        if action == "list":
            # 查看白名单
            whitelist = load_whitelist()
            if not whitelist:
                await MessageUtils.build_message("📋 白名单为空").send(reply_to=True)
                return

            user_list = "\n".join([f"• {uid}" for uid in sorted(whitelist)])
            await MessageUtils.build_message(
                f"📋 当前白名单用户 ({len(whitelist)}人):\n{user_list}"
            ).send(reply_to=True)

        elif action == "add":
            # 添加用户到白名单
            if not user_id:
                await MessageUtils.build_message(
                    "❌ 请指定要添加的用户ID\n格式：#mcrun_whitelist add <用户ID>"
                ).send(reply_to=True)
                return

            whitelist = load_whitelist()
            if user_id in whitelist:
                await MessageUtils.build_message(f"⚠️ 用户 {user_id} 已在白名单中").send(
                    reply_to=True
                )
                return

            whitelist.add(user_id)
            if save_whitelist(whitelist):
                await MessageUtils.build_message(
                    f"✅ 已将用户 {user_id} 添加到白名单"
                ).send(reply_to=True)
                logger.info(f"用户 {user_id} 已添加到白名单", "MC Bot运行插件")
            else:
                await MessageUtils.build_message("❌ 保存白名单失败").send(
                    reply_to=True
                )

        elif action == "remove" or action == "del":
            # 从白名单移除用户
            if not user_id:
                await MessageUtils.build_message(
                    "❌ 请指定要移除的用户ID\n格式：#mcrun_whitelist remove <用户ID>"
                ).send(reply_to=True)
                return

            whitelist = load_whitelist()
            if user_id not in whitelist:
                await MessageUtils.build_message(f"⚠️ 用户 {user_id} 不在白名单中").send(
                    reply_to=True
                )
                return

            whitelist.remove(user_id)
            if save_whitelist(whitelist):
                await MessageUtils.build_message(
                    f"✅ 已将用户 {user_id} 从白名单移除"
                ).send(reply_to=True)
                logger.info(f"用户 {user_id} 已从白名单移除", "MC Bot运行插件")
            else:
                await MessageUtils.build_message("❌ 保存白名单失败").send(
                    reply_to=True
                )

        else:
            # 显示帮助信息
            help_text = (
                "📋 白名单管理命令：\n"
                "• #mcrun_whitelist list - 查看白名单\n"
                "• #mcrun_whitelist add <用户ID> - 添加用户到白名单\n"
                "• #mcrun_whitelist remove <用户ID> - 从白名单移除用户\n\n"
                "💡 只有白名单中的用户才能使用 #mcrun 命令"
            )
            await MessageUtils.build_message(help_text).send(reply_to=True)

    except Exception as e:
        error_details = traceback.format_exc()
        await MessageUtils.build_message(
            f"❌ 白名单操作失败！\n错误信息: {e!s}\n\n详细错误:\n{error_details}"
        ).send(reply_to=True)
        logger.error(
            f"白名单操作异常: {e}\n详细错误: {error_details}", "MC Bot运行插件"
        )
