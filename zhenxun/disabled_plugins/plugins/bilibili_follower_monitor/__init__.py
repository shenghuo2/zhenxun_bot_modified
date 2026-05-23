import json
import os
from datetime import datetime
from pathlib import Path
from nonebot import get_bot
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Alconna, on_alconna
from nonebot_plugin_session import EventSession
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

from .data_source import get_snow_lotus_comparison, SnowLotusComparator

__plugin_meta__ = PluginMetadata(
    name="雪莲粉丝对比",
    description="比较东洋雪莲和東雪莲Official的粉丝数",
    usage="""
    usage：
        比较两个雪莲账号的粉丝数差距
        指令：
            #雪莲
        示例：
            #雪莲
    """.strip(),
    extra={
        "author": "Assistant",
        "version": "0.1",
        "configs": []
    },
)

# 目标群组ID
TARGET_GROUPS = [787599185, 912045649, 555741990]

# 粉丝差距阈值（当差距达到这些值时推送消息）
THRESHOLD_VALUES = [200, 100, 50, 20, 10, 0, -100]

# 缓存文件路径
CACHE_FILE = Path(__file__).parent / "cache_data.json"

# 记录已推送的阈值，避免重复推送
pushed_thresholds = set()

# 历史数据缓存
cache_data = {
    "pushed_thresholds": [],
    "last_follower_data": {},
    "last_check_time": None
}


def load_cache():
    """从文件加载缓存数据"""
    global pushed_thresholds, cache_data
    
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 恢复推送阈值状态
            pushed_thresholds = set(cache_data.get("pushed_thresholds", []))
            
            logger.info(f"成功加载缓存数据，已推送阈值: {pushed_thresholds}", "雪莲监控")
        else:
            logger.info("缓存文件不存在，使用默认设置", "雪莲监控")
    except Exception as e:
        logger.error(f"加载缓存数据失败: {e}", "雪莲监控")
        # 使用默认值
        pushed_thresholds = set()
        cache_data = {
            "pushed_thresholds": [],
            "last_follower_data": {},
            "last_check_time": None
        }


def save_cache():
    """保存缓存数据到文件"""
    global pushed_thresholds, cache_data
    
    try:
        # 更新缓存数据
        cache_data["pushed_thresholds"] = list(pushed_thresholds)
        
        # 确保目录存在
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.debug("缓存数据已保存", "雪莲监控")
    except Exception as e:
        logger.error(f"保存缓存数据失败: {e}", "雪莲监控")


def get_formatted_time():
    """获取格式化的当前时间"""
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")


# 启动时加载缓存
load_cache()

# 雪莲粉丝对比
snow_lotus_compare = on_alconna(
    Alconna("#雪莲"),
    priority=5,
    block=True,
)


@snow_lotus_compare.handle()
async def _(session: EventSession):
    """雪莲粉丝对比"""
    try:
        result = await get_snow_lotus_comparison()
        # 在结果中添加查询时间
        current_time = get_formatted_time()
        result_with_time = f"{result}\n\n🕐 查询时间: {current_time}"
        await MessageUtils.build_message(result_with_time).send()
    except Exception as e:
        logger.error(f"雪莲粉丝对比失败: {e}")
        await MessageUtils.build_message("获取数据失败，请稍后重试").send()


# @scheduler.scheduled_job("interval", seconds=20, id="snow_lotus_monitor")
async def monitor_snow_lotus_followers():
    """定时监控雪莲粉丝数差距"""
    global pushed_thresholds, cache_data
    
    try:
        logger.info("开始检查雪莲粉丝数差距...", "雪莲监控")
        
        # 获取两个用户的粉丝数据
        results = {}
        from .data_source import USERS
        
        for name, mid in USERS.items():
            stat = await SnowLotusComparator.get_user_stat(mid)
            if stat:
                results[name] = {
                    "mid": mid,
                    "follower": stat.get("follower", 0),
                    "following": stat.get("following", 0)
                }
            else:
                logger.warning(f"获取 {name} 的数据失败", "雪莲监控")
                return
        
        if len(results) != 2:
            logger.warning("数据获取不完整", "雪莲监控")
            return
        
        # 更新缓存中的粉丝数据
        import time
        cache_data["last_follower_data"] = results
        cache_data["last_check_time"] = time.time()
        
        # 计算粉丝差距
        user_keys = list(USERS.keys())
        dongyang_key = user_keys[0]  # "东洋雪莲"
        dongxue_key = user_keys[1]   # "東雪莲Official"
        
        dongyang = results[dongyang_key]
        dongxue = results[dongxue_key]
        
        follower_diff = dongyang["follower"] - dongxue["follower"]
        abs_diff = abs(follower_diff)
        
        logger.info(f"当前粉丝差距: {follower_diff}", "雪莲监控")
        
        # 检查是否达到推送阈值
        for threshold in THRESHOLD_VALUES:
            # 对于负数阈值，检查東雪莲Official是否领先超过该阈值
            if threshold < 0:
                if follower_diff <= threshold and threshold not in pushed_thresholds:
                    await send_threshold_notification(dongyang, dongxue, follower_diff, threshold)
                    pushed_thresholds.add(threshold)
                    logger.info(f"已推送阈值 {threshold} 的通知", "雪莲监控")
                    break
            # 对于正数阈值，检查差距是否缩小到该阈值以内
            else:
                if abs_diff <= threshold and threshold not in pushed_thresholds:
                    await send_threshold_notification(dongyang, dongxue, follower_diff, threshold)
                    pushed_thresholds.add(threshold)
                    logger.info(f"已推送阈值 {threshold} 的通知", "雪莲监控")
                    break
        
        # 如果差距变化，清除不再适用的阈值
        old_pushed = pushed_thresholds.copy()
        new_pushed = set()
        for threshold in pushed_thresholds:
            if threshold < 0:
                # 负数阈值：如果东洋雪莲重新领先，清除该阈值
                if follower_diff > threshold:
                    new_pushed.add(threshold)
            else:
                # 正数阈值：如果差距重新扩大，清除该阈值
                if abs_diff <= threshold:
                    new_pushed.add(threshold)
        pushed_thresholds = new_pushed
        
        # 如果推送状态发生变化，保存缓存
        if old_pushed != pushed_thresholds or cache_data.get("last_check_time") != time.time():
            save_cache()
        
    except Exception as e:
        logger.error(f"监控雪莲粉丝数时发生错误: {e}", "雪莲监控")


async def send_threshold_notification(dongyang_data, dongxue_data, diff, threshold):
    """发送阈值通知到指定群组"""
    try:
        bot = get_bot()
        current_time = get_formatted_time()
        
        # 构建消息内容
        if threshold == 0:
            msg = "🚨 重要提醒！雪莲粉丝数已持平！🚨\n\n"
        elif threshold < 0:
            msg = f"📢 雪莲粉丝差距提醒！\n\n東雪莲Official已反超 {abs(diff):,} 人（阈值: {threshold}）\n\n"
        else:
            msg = f"📢 雪莲粉丝差距提醒！\n\n粉丝差距已缩小至 {abs(diff):,} 人（阈值: {threshold}）\n\n"
        
        msg += f"🔹 东洋雪莲: {dongyang_data['follower']:,} 粉丝\n"
        msg += f"🔹 東雪莲Official: {dongxue_data['follower']:,} 粉丝\n\n"
        
        if dongyang_data["follower"] > dongxue_data["follower"]:
            msg += f"📊 东洋雪莲领先 {abs(diff):,} 粉丝"
        elif dongyang_data["follower"] < dongxue_data["follower"]:
            msg += f"📊 東雪莲Official领先 {abs(diff):,} 粉丝"
        else:
            msg += "📊 两人粉丝数完全相同！"
        
        # 添加纪念时间
        msg += f"\n\n🕐 时间: {current_time}"
        
        # 发送到指定群组
        for group_id in TARGET_GROUPS:
            try:
                await bot.send_group_msg(
                    group_id=group_id,
                    message=Message(MessageSegment.text(msg))
                )
                logger.info(f"成功发送通知到群 {group_id}", "雪莲监控")
            except Exception as e:
                logger.error(f"发送通知到群 {group_id} 失败: {e}", "雪莲监控")
                
    except Exception as e:
        logger.error(f"发送阈值通知时发生错误: {e}", "雪莲监控")