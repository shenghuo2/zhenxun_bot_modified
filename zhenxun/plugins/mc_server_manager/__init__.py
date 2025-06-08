import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Alconna, Args, on_alconna
from nonebot_plugin_session import EventSession
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

__plugin_meta__ = PluginMetadata(
    name="MC服务器管理",
    description="管理Minecraft服务器列表",
    usage="""
    usage：
        管理Minecraft服务器列表
        指令：
            #server add <服务器名称> <IP地址> [描述]
            #server edit <服务器名称> <新IP地址> [新描述]
            #server del <服务器名称>
            #server list
        示例：
            #server add 我的服务器 127.0.0.1:25565 一个很棒的服务器
            #server edit 我的服务器 192.168.1.100:25565 更新后的服务器
            #server del 我的服务器
            #server list
    """.strip(),
    extra={
        "author": "Assistant",
        "version": "1.1",
        "configs": []
    },
)

# 服务器数据文件路径
SERVER_DATA_FILE = Path(__file__).parent / "servers.json"


def load_servers():
    """加载服务器列表"""
    try:
        if SERVER_DATA_FILE.exists():
            with open(SERVER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logger.error(f"加载服务器列表失败: {e}", "MC服务器管理")
        return {}


def save_servers(servers):
    """保存服务器列表"""
    try:
        # 确保目录存在
        SERVER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SERVER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(servers, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存服务器列表失败: {e}", "MC服务器管理")
        return False


def validate_ip(ip_address):
    """验证IP地址格式（支持端口）"""
    # 匹配 IP:port 或 域名:port 或 IP 或 域名
    pattern = r'^([a-zA-Z0-9.-]+)(:[0-9]{1,5})?$'
    return re.match(pattern, ip_address) is not None


# 服务器管理命令（支持多种操作）
server_manager = on_alconna(
    Alconna("#server", Args["action", str]["name?", str]["ip?", str]["description?", str]),
    priority=5,
    block=True,
)


@server_manager.handle()
async def handle_server_command(session: EventSession, action: str, name: Optional[str] = None, ip: Optional[str] = None, description: Optional[str] = None):
    """处理服务器相关命令"""
    try:
        if action == "add":
            if not name or not ip:
                await MessageUtils.build_message("❌ 格式错误！\n正确格式：#server add <服务器名称> <IP地址> [描述]").send()
                return
            
            # 验证IP格式
            if not validate_ip(ip):
                await MessageUtils.build_message("❌ IP地址格式不正确！\n支持格式：IP地址、域名、IP:端口、域名:端口").send()
                return
            
            # 加载现有服务器列表
            servers = load_servers()
            
            # 检查服务器名称是否已存在
            if name in servers:
                await MessageUtils.build_message(f"❌ 服务器名称 '{name}' 已存在！\n使用 #server edit {name} <新IP> [新描述] 来编辑").send()
                return
            
            # 添加新服务器
            servers[name] = {
                "ip": ip,
                "description": description or "暂无描述",
                "added_by": session.id1 or "未知用户",
                "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存到文件
            if save_servers(servers):
                msg = f"✅ 服务器添加成功！\n\n"
                msg += f"🏷️ 名称：{name}\n"
                msg += f"🌐 地址：{ip}\n"
                msg += f"📝 描述：{description or '暂无描述'}"
                await MessageUtils.build_message(msg).send()
            else:
                await MessageUtils.build_message("❌ 保存服务器信息失败！").send()
        
        elif action == "edit":
            if not name:
                await MessageUtils.build_message("❌ 格式错误！\n正确格式：#server edit <服务器名称> <新IP地址> [新描述]").send()
                return
            
            # 加载现有服务器列表
            servers = load_servers()
            
            # 检查服务器是否存在
            if name not in servers:
                await MessageUtils.build_message(f"❌ 服务器 '{name}' 不存在！\n使用 #server list 查看现有服务器").send()
                return
            
            # 如果提供了新IP，验证格式
            if ip and not validate_ip(ip):
                await MessageUtils.build_message("❌ IP地址格式不正确！\n支持格式：IP地址、域名、IP:端口、域名:端口").send()
                return
            
            # 更新服务器信息
            old_info = servers[name].copy()
            if ip:
                servers[name]["ip"] = ip
            if description is not None:
                servers[name]["description"] = description
            servers[name]["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            servers[name]["modified_by"] = session.id1 or "未知用户"
            
            # 保存到文件
            if save_servers(servers):
                msg = f"✅ 服务器 '{name}' 编辑成功！\n\n"
                msg += f"🏷️ 名称：{name}\n"
                if ip:
                    msg += f"🌐 地址：{old_info['ip']} → {ip}\n"
                else:
                    msg += f"🌐 地址：{servers[name]['ip']}\n"
                if description is not None:
                    msg += f"📝 描述：{old_info['description']} → {description}\n"
                else:
                    msg += f"📝 描述：{servers[name]['description']}\n"
                msg += f"🕒 修改时间：{servers[name]['last_modified']}"
                await MessageUtils.build_message(msg).send()
            else:
                await MessageUtils.build_message("❌ 保存服务器信息失败！").send()
        
        elif action == "del" or action == "delete":
            if not name:
                await MessageUtils.build_message("❌ 格式错误！\n正确格式：#server del <服务器名称>").send()
                return
            
            # 加载现有服务器列表
            servers = load_servers()
            
            # 检查服务器是否存在
            if name not in servers:
                await MessageUtils.build_message(f"❌ 服务器 '{name}' 不存在！\n使用 #server list 查看现有服务器").send()
                return
            
            # 删除服务器
            deleted_server = servers.pop(name)
            
            # 保存到文件
            if save_servers(servers):
                msg = f"✅ 服务器删除成功！\n\n"
                msg += f"🏷️ 已删除：{name}\n"
                msg += f"🌐 地址：{deleted_server['ip']}\n"
                msg += f"📝 描述：{deleted_server['description']}"
                await MessageUtils.build_message(msg).send()
            else:
                await MessageUtils.build_message("❌ 删除服务器失败！").send()
        
        elif action == "list":
            servers = load_servers()
            
            if not servers:
                await MessageUtils.build_message("📋 服务器列表为空\n\n使用 #server add <名称> <IP> [描述] 来添加服务器").send()
                return
            
            msg = "📋 Minecraft服务器列表\n\n"
            for i, (server_name, server_info) in enumerate(servers.items(), 1):
                msg += f"{i}. 🏷️ {server_name}\n"
                msg += f"   🌐 {server_info['ip']}\n"
                msg += f"   📝 {server_info['description']}\n"
                if 'last_modified' in server_info:
                    msg += f"   🕒 最后修改：{server_info['last_modified']}\n"
                msg += "\n"
            
            msg += f"📊 共 {len(servers)} 个服务器"
            await MessageUtils.build_message(msg).send()
        
        else:
            help_msg = "❌ 未知命令！\n\n支持的命令：\n"
            help_msg += "• #server add <名称> <IP> [描述] - 添加服务器\n"
            help_msg += "• #server edit <名称> <新IP> [新描述] - 编辑服务器\n"
            help_msg += "• #server del <名称> - 删除服务器\n"
            help_msg += "• #server list - 查看服务器列表"
            await MessageUtils.build_message(help_msg).send()
    
    except Exception as e:
        logger.error(f"处理服务器命令时发生错误: {e}", "MC服务器管理")
        await MessageUtils.build_message("❌ 处理命令时发生错误，请稍后重试").send()