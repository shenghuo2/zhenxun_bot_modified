# data_source.py
import re
import feedparser
import time
import json

from requests.exceptions import RequestException
from zhenxun.services.log import logger

# 配置
rss_anning_url = 'http://192.168.123.27:1200/telegram/channel/anningloliGroups'  # RSS源URL
ManyACG_RSS = "https://manyacg.top/atom.xml"



MAX_RETRIES = 5  # 最大重试次数

PROCESSED_GUIDS_FILE = "processed_guids.json"
# 读取已处理的guid
def load_processed_guids():
    try:
        with open(PROCESSED_GUIDS_FILE, 'r', encoding='utf-8') as file:
            processed_guids = json.load(file)
            return set(processed_guids)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或无法读取，返回空集合
        return set()

# 保存已处理的guid
def save_processed_guids(processed_guids):
    with open(PROCESSED_GUIDS_FILE, 'w', encoding='utf-8') as file:
        json.dump(list(processed_guids), file)

# 用于追踪已处理的条目的guid
processed_guids = load_processed_guids()
# 解析RSS的函数，添加重试机制
def parse_rss(rss_url:str):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                return feed.entries
            else:
                logger.warning("No entries found in RSS feed.")
                return []
        except RequestException as e:
            retries += 1
            logger.error(f"  ({retries}/{MAX_RETRIES})... 错误: {e}")
            time.sleep(5)  # 等待5秒后重试
    logger.error(f"超过最大重试次数 ({MAX_RETRIES})，无法连接到RSS源。")
    return []

# 从description中提取图片URL的函数
def extract_image_urls(description):
    """
    从RSS条目的description中提取图片URL
    """
    image_urls = re.findall(r'src="(https:\/\/[^\"]+)"', description)
    return image_urls

# 获取新条目的函数
def get_new_entries_GUID(entries):
    """
    返回所有未处理过的条目（根据guid检查）
    """
    new_entries = []
    for entry in entries:
        if entry.guid not in processed_guids:
            processed_guids.add(entry.guid)  # 标记该条目为已处理
            new_entries.append(entry)
    save_processed_guids(processed_guids)  # 每次处理后保存

    return new_entries

def get_new_entries_ID(entries):
    """
    返回所有未处理过的条目（根据id检查）
    """
    new_entries = []
    for entry in entries:
        if entry.id not in processed_guids:
            processed_guids.add(entry.id)  # 标记该条目为已处理
            logger.info(f"entry.id:{entry.id}", "rss_pix_push_log")
            new_entries.append(entry)
    save_processed_guids(processed_guids)  # 每次处理后保存
    return new_entries


def mian():
    logger.info("Checking for RSS updates...","rss解析")
    try:
        entries = parse_rss()
        # print(len(entries),entries)
        if entries:
            latest_entry = entries[0]  # 获取最新的一条RSS条目

            # 提取description中的图片链接
            description = latest_entry.description
            image_urls = extract_image_urls(description)
            print(image_urls)
            if image_urls:
                # 获取第一个图片URL
                image_url = image_urls[0]
                logger.info(f"图片URL: {image_url}")
    except Exception as e:
        logger.error(f"检查RSS更新失败: {e}")
        
# mian()