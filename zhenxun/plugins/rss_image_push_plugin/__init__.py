# main_plugin.py
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot_plugin_apscheduler import scheduler
from zhenxun.services.log import logger
from time import sleep
# 从data_source.py导入parse_rss和extract_image_urls函数
from .data_source import parse_rss, extract_image_urls, get_new_entries_GUID, get_new_entries_ID, rss_anning_url, ManyACG_RSS

# 配置
target_group_id = 787599185  # 目标群聊ID

# 定义定时任务，每分钟检查一次RSS更新
# @scheduler.scheduled_job("interval", minutes=5)

# async def rss_image_forward_job():
#     logger.info("Checking for RSS updates...","rss_pix_push")
#     try:
#         # anning_entries = parse_rss(rss_anning_url)  # 获取anning RSS条目
#         ManyACG_entries = parse_rss(ManyACG_RSS)  # 获取ManyACG RSS条目
#         # anning_new_entries = get_new_entries_GUID(anning_entries)  # 获取新的条目
#         ManyACG_new_entries = get_new_entries_ID(ManyACG_entries)  # 获取新的条目
#         # logger.info(str(ManyACG_new_entries),"rss_pix_push")
#         # if anning_new_entries:
#             # await send_image_to_group(anning_new_entries)  # 发送新的图片到群聊
#         if ManyACG_new_entries:
#             await send_image_to_group(ManyACG_new_entries)  # 发送新的图片到群聊
#         # if anning_new_entries == [] and ManyACG_new_entries == []:
#         #     logger.info("No new RSS entries available.")
#     except Exception as e:
#         logger.error(f"检查RSS更新失败: {e}")


async def send_image_to_group(new_entries):
    """
    
    """
    bot = get_bot()
    for entry in new_entries:
        # 提取description中的所有图片链接
         
        if getattr(entry, 'content', None):
            data = entry.content[0].value
        else:    
            data = entry.description
        
        image_urls = extract_image_urls(data)
        
        if image_urls:
            # 遍历所有图片URL并逐一发送
            for image_url in image_urls:
                try:
                    message = Message(
                                        MessageSegment.image(image_url)
                                        +
                                        MessageSegment.text(f"{entry.title}\n")
                                        )
                    # 发送图片消息到指定群聊
                    sleep(1)
                    await bot.send_group_msg(group_id=target_group_id, message=message)
                    logger.info(f"图片转发成功: {image_url}")
                except Exception as e:
                    logger.error(f"发送图片时出错: {e}")
                    # await bot.send_group_msg(group_id=target_group_id, message=f"发送图片时出错，这是图片的URL:{image_url}")
        else:
            logger.warning(f"No images found in the new RSS entry: {entry.title}")


# # 启动时的初始化检查
# @scheduler.scheduled_job("interval", minutes=5)
# async def init_rss_check():
#     logger.info("启动RSS图片转发任务...")
#     await rss_image_forward_job()
