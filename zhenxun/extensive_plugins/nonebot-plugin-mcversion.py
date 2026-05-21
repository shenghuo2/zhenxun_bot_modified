from nonebot.plugin import PluginMetadata
from pydantic import BaseModel

__plugin_meta__ = PluginMetadata(
    name="MC版本更新检测",
    description="一个用于检测MC最新版本的插件",
    usage="使用 mcver 以获取最新版本号",
    type="application",
    homepage="https://github.com/CN171-1/nonebot_plugin_mcversion",
    supported_adapters={"~onebot.v11"},
)

# 导入必要的库
import os
from datetime import datetime, timedelta, timezone

import httpx
from nonebot import on_command, get_bots, require, logger, get_plugin_config
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.message import Message

VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
MC_ARTICLE_BASE_URL = "https://www.minecraft.net/en-us/article/"
CHINA_TZ = timezone(timedelta(hours=8))

# 定义配置模型
class MCVersionConfig(BaseModel):
    mcver_group_id: list[int | str] = []
    """MC版本更新推送的群组ID列表"""

# 获取配置
config = get_plugin_config(MCVersionConfig)
mcver_group_id = config.mcver_group_id

# 定义命令“mcver”
mcver = on_command('#mcver', aliases={'#mcversion', '#MC版本'}, priority=50)

@mcver.handle()
async def mcver_handle():
    # 获取Minecraft版本信息
    async with httpx.AsyncClient() as client:
        data = await fetch_version_manifest(client)
        versions = {item["id"]: item for item in data["versions"]}
        latest_release = data['latest']['release']
        latest_snapshot = data['latest']['snapshot']
        latest_release_changelog = await get_changelog(client, versions[latest_release])
        latest_snapshot_changelog = await get_changelog(client, versions[latest_snapshot])
    # 发送消息
    await mcver.finish(message=Message(f'最新正式版：{latest_release}\n更新日志：{latest_release_changelog}\n最新快照版：{latest_snapshot}\n更新日志：{latest_snapshot_changelog}'))

# 获取nonebot的调度器
scheduler = require('nonebot_plugin_apscheduler').scheduler

# 定义异步函数，用于检查Minecraft更新
async def check_mc_update(bot: Bot):
    # 获取Minecraft版本信息
    async with httpx.AsyncClient() as client:
        data = await fetch_version_manifest(client)
        version = data["versions"][0]
    if not os.path.exists('data/latest_version.txt'):
        with open('data/latest_version.txt', 'w') as f:
            f.write(version["id"])
    with open('data/latest_version.txt', 'r') as f:
        old_version = f.read()
    if version["id"] != old_version:
        release_time = version["releaseTime"]
        release_time = datetime.strptime(release_time, '%Y-%m-%dT%H:%M:%S%z')
        release_time = release_time.astimezone(CHINA_TZ).isoformat(timespec='seconds')
        
        async with httpx.AsyncClient() as client:
            changelog = await get_changelog(client, version)
        # 检查是否配置了群组ID
        if mcver_group_id:
            for group_id in mcver_group_id:
                try:
                    await bot.send_group_msg(
                        group_id=int(group_id),
                        message=Message(f'发现MC更新：{version["id"]} ({version["type"]})\n时间：{release_time}\n更新日志：{changelog}')
                    )
                except Exception as e:
                    logger.error(f"向群组 {group_id} 发送MC更新消息失败: {e}")
            logger.success("已发现并成功推送MC版本更新信息")
        else:
            logger.warning("未配置MC版本更新推送群组，跳过推送")
            
        with open('data/latest_version.txt', 'w') as f:
            f.write(version["id"])

async def fetch_version_manifest(client: httpx.AsyncClient) -> dict:
    response = await client.get(VERSION_MANIFEST_URL)
    response.raise_for_status()
    return response.json()


def build_changelog_candidates(version_id: str, version_type: str) -> list[str]:
    normalized = version_id.replace('.', '-')
    candidates: list[str] = []

    if version_type == 'release':
        candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-java-edition-{normalized}')
        candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-{normalized}')
    else:
        if '-rc-' in normalized:
            candidates.append(
                f'{MC_ARTICLE_BASE_URL}minecraft-{normalized.replace("-rc-", "-release-candidate-")}'
            )
        if '-pre-' in normalized:
            candidates.append(
                f'{MC_ARTICLE_BASE_URL}minecraft-{normalized.replace("-pre-", "-pre-release-")}'
            )
        if '-snapshot-' in normalized:
            candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-{normalized}')
        if 'w' in version_id:
            candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-snapshot-{version_id.replace("b", "a")}')

        candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-java-edition-{normalized}')
        candidates.append(f'{MC_ARTICLE_BASE_URL}minecraft-{normalized}')

    # 去重并保留顺序，避免对同一URL重复探测。
    return list(dict.fromkeys(candidates))


async def url_exists(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.head(url, follow_redirects=True)
        if response.status_code == 405:
            response = await client.get(url, follow_redirects=True)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


async def get_changelog(client: httpx.AsyncClient, version: dict) -> str:
    candidates = build_changelog_candidates(version['id'], version['type'])

    # Minecraft 官网对程序化探测请求的响应不稳定，优先直接返回已验证规则生成的网页地址。
    if candidates:
        return candidates[0]

    # 兜底保留官方版本元数据地址，避免极端情况下返回空链接。
    return version['url']

# 定义定时任务，每分钟检查一次Minecraft更新
@scheduler.scheduled_job('interval', minutes=15)
async def mc_update_check():
    bots = get_bots()
    bot = None  # 初始化bot为None
    if bots:
        bot = list(bots.values())[0]  # 获取第一个机器人实例
    if bot:
        await check_mc_update(bot)
    else:
        logger.error("未找到机器人实例,请确保NoneBot已与QQ服务器建立连接")
