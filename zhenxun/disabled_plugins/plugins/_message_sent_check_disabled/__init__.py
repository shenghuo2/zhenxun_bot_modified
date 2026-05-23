import asyncio
import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiohttp
from nonebot import get_driver, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from zhenxun.configs.config import Config
from zhenxun.services.log import logger
from zhenxun.utils.user_agent import get_user_agent

from ..parse_bilibili.information_container import InformationContainer
from ..parse_bilibili.parse_url import parse_bili_url

# 初始化 SQLAlchemy 部分
DATABASE_PATH = Path(__file__).parent / "messages.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
Base = declarative_base()
utcnow = lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


# 定义数据库模型
class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False, unique=True)
    message_sha256 = Column(String, nullable=False)
    group_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=utcnow)


# 创建数据库引擎和会话
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 初始化数据库
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="message_sent_check",
    description="记录所有非纯文字的消息的sha256和消息id，检测重复消息并自动回复，支持B站视频查重",
    usage="""
    自动记录消息的 sha256 和消息ID，存储到SQLite数据库中。若检测到重复消息，自动回复提示。

    功能：
    1. 自动检测转发消息、视频消息的重复
    2. 自动检测B站视频链接的重复（支持标准链接、短链接、BV号、AV号）
    3. 自动检测B站视频卡片分享的重复
    4. 支持手动标记图片和B站视频（包括视频卡片）

    命令：
    - #标记：回复一条消息，将其标记为已发送过（支持图片和B站视频）
    - #删除标记：回复一条消息，删除其标记记录（仅限超级用户）
    """,
    extra={
        "author": "shenghuo2",
        "version": "0.7.1",
        "plugin_type": "DEPENDANT",
        "menu_type": "其他",
        "configs": [
            {
                "module": "message_sent_check",
                "key": "GROUP_WHITELIST",
                "value": [],
                "default_value": [],
                "help": "指定启用该插件的群（群号列表）。如果群号在列表中，插件会启用。",
                "type": list,
            }
        ],
    },
)


# 计算sha256的函数
def compute_sha256(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


# 存储消息记录到数据库的异步函数
async def store_message(
    session: AsyncSession,
    message_id: str,
    sha256: str,
    group_id: str,
    timestamp: datetime.datetime | None = None,
):
    message_record = MessageRecord(
        message_id=message_id,
        message_sha256=sha256,
        group_id=group_id,
        timestamp=timestamp or utcnow(),
    )
    session.add(message_record)
    await session.commit()


# 查询数据库中是否已有相同的sha256和群ID
async def find_existing_message(
    session: AsyncSession, sha256: str, group_id: str
) -> MessageRecord:
    result = await session.execute(
        select(MessageRecord).filter_by(message_sha256=sha256, group_id=group_id)
    )
    return result.scalars().first()


# 通过 message_id 查询是否存在记录的函数
async def find_message_by_id(
    session: AsyncSession, message_id: str
) -> MessageRecord | None:
    result = await session.execute(
        select(MessageRecord).filter_by(message_id=message_id)
    )
    return result.scalars().first()


# 删除消息记录的异步函数
async def delete_message(session: AsyncSession, message_id: str):
    result = await session.execute(
        select(MessageRecord).filter_by(message_id=message_id)
    )
    message_record = result.scalars().first()
    if message_record:
        await session.delete(message_record)
        await session.commit()


# 判断是否为纯文本消息
def is_pure_text(message: MessageEvent):
    return all(segment.type == "text" for segment in message)


# 插件的消息处理逻辑
async def _rule(session: Uninfo) -> bool:
    # 从配置中获取群号白名单
    group_whitelist = Config.get_config("message_sent_check", "GROUP_WHITELIST")

    # 私聊消息没有 group 属性，直接返回 True
    if not session.group:
        return True

    if group_whitelist and session.group.id not in group_whitelist:
        return False  # 如果群不在白名单中，忽略该消息
    return True  # 如果群在白名单中，处理消息


def is_valid_message(message_content: str) -> bool:
    """
    判断消息是否为需要处理的图片、视频或转发消息，
    同时忽略包含表情包的消息。
    """
    # 检查消息是否是图片、视频或转发消息
    if message_content.startswith("[CQ:video,") or message_content.startswith(
        "[CQ:forward,"
    ):
        return True
    return False


# 用正则提取图片的 file_unique 字段
def extract_file_unique(message_content: str) -> str:
    match = re.search(r"file_unique=([a-fA-F0-9]+)", message_content)
    if match:
        return match.group(1)
    return None  # 如果没有匹配到，返回 None


# 获取转发消息的内容
async def get_forward_messages(forward_message_id: str, bot: Bot) -> list:
    try:
        response: dict = await bot.call_api(
            "get_forward_msg", message_id=forward_message_id
        )
        messages = response.get("messages", [])
        # 提取 raw_message 或 file_unique（用于图片）
        return [
            msg["raw_message"]
            if "file_unique" not in msg
            else extract_file_unique(msg["raw_message"])
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error fetching forward messages: {e}")
        return []


import html  # 导入html模块来解码HTML实体


# 获取转发消息的内容
async def get_forward_messages(forward_message_id: str, bot: Bot) -> list:
    try:
        # 获取转发消息
        response: dict = await bot.call_api(
            "get_forward_msg", message_id=forward_message_id
        )
        messages = response.get("messages", [])

        forward_messages = []
        for msg in messages:
            # 检查消息是否包含嵌套转发
            if "[CQ:forward," in msg["raw_message"]:
                # 提取time戳
                timestamp = msg.get("time")
                # 拼接时间戳
                forward_messages.append(
                    f"has_Forward_message_with_timestamp_{timestamp}"
                )
            else:
                # 解码 HTML 实体，避免出现 &#91; 等编码
                raw_message = html.unescape(msg["raw_message"])  # 解码 HTML 实体
                if "file_unique" in str(msg):
                    # 提取 file_unique
                    file_unique = extract_file_unique(msg["raw_message"])
                    forward_messages.append(file_unique)
                else:
                    forward_messages.append(raw_message)
        return forward_messages
    except Exception as e:
        logger.error(f"Error fetching forward messages: {e}")
        return []


def get_time_diff_str(timestamp: datetime) -> str:
    now = utcnow()  # 获取当前时间
    time_diff = now - timestamp  # 获取时间差

    # 根据时间差的不同部分进行格式化
    if time_diff.days > 0:
        return f"{time_diff.days}天之前"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        return f"{hours}小时之前"
    elif time_diff.seconds >= 60:
        minutes = time_diff.seconds // 60
        return f"{minutes}分钟之前"
    elif time_diff.seconds > 0:
        return f"{time_diff.seconds}秒之前"
    # else:
    #     return "刚刚"


def is_valid_message(message: Message) -> bool:
    """判断消息是否为需要处理的视频或转发消息"""
    for segment in message:
        # 修改判断条件：通过消息类型判断
        if segment.type in ["forward", "video"]:  # 关键修改点1
            return True
    return False


def is_image_message(message: Message) -> bool:
    """判断消息是否包含图片"""
    return any(seg.type == "image" for seg in message)


def contains_bilibili_url(message_text: str, message: Message = None) -> bool:
    """判断消息是否包含B站视频链接"""
    # 如果消息包含图片或视频，跳过检查（因为图片/视频链接可能意外包含视频号）
    if message and any(seg.type in ["image", "video"] for seg in message):
        return False

    # 检查常见的B站链接格式
    bilibili_patterns = [
        r"https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+",  # 标准视频链接
        r"https?://b23\.tv/[A-Za-z0-9]+",  # 短链接
        r"BV[A-Za-z0-9]{10}",  # BV号
        r"av\d+",  # av号
        r"bilibili\.com",  # 包含bilibili.com的任何链接
        r"b23\.tv",  # 包含b23.tv的任何链接
    ]

    for pattern in bilibili_patterns:
        if re.search(pattern, message_text, re.IGNORECASE):
            return True
    return False


def extract_url_from_json(json_data: dict) -> str | None:
    """从JSON数据中提取URL"""

    # 递归搜索JSON中的URL
    def search_url(data, depth=0, max_depth=5):
        if depth > max_depth:
            return None

        if isinstance(data, dict):
            # 检查常见的URL字段名
            url_keys = ["url", "jumpUrl", "qqdocurl", "link", "href"]
            for key in url_keys:
                if (
                    key in data
                    and isinstance(data[key], str)
                    and ("bilibili.com" in data[key] or "b23.tv" in data[key])
                ):
                    return data[key]

            # 递归搜索所有值
            for value in data.values():
                result = search_url(value, depth + 1, max_depth)
                if result:
                    return result

        elif isinstance(data, list):
            # 递归搜索列表中的所有元素
            for item in data:
                result = search_url(item, depth + 1, max_depth)
                if result:
                    return result

        elif isinstance(data, str):
            # 检查字符串是否包含B站链接
            if "bilibili.com/video" in data or "b23.tv" in data:
                url = extract_bilibili_url(data)
                if url:
                    return url

        return None

    return search_url(json_data)


def extract_bilibili_url(message_text: str) -> str:
    """从消息文本中提取B站视频链接"""
    # 尝试匹配不同格式的B站链接
    # 标准视频链接
    match = re.search(
        r"https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+", message_text
    )
    if match:
        return match.group(0)

    # 短链接
    match = re.search(r"https?://b23\.tv/[A-Za-z0-9]+", message_text)
    if match:
        return match.group(0)

    # BV号
    match = re.search(r"BV[A-Za-z0-9]{10}", message_text)
    if match:
        bv_id = match.group(0)
        return f"https://www.bilibili.com/video/{bv_id}"

    # av号
    match = re.search(r"av(\d+)", message_text)
    if match:
        av_id = match.group(1)
        return f"https://www.bilibili.com/video/av{av_id}"

    return None


async def extract_bilibili_card_info(message: Message) -> dict[str, Any] | None:
    """从消息卡片中提取B站视频信息"""
    for segment in message:
        # 检查是否是JSON消息段
        if segment.type == "json":
            try:
                # 解析JSON数据
                data = json.loads(segment.data.get("data", "{}"))
                logger.info(f"解析JSON数据: {data}")

                # 检查是否是B站视频卡片 - 标准格式
                if data.get("desc") == "哔哩哔哩" or "哔哩哔哩" in data.get(
                    "prompt", ""
                ):
                    # 获取视频链接
                    if (
                        "meta" in data
                        and "detail_1" in data["meta"]
                        and "qqdocurl" in data["meta"]["detail_1"]
                    ):
                        url = data["meta"]["detail_1"]["qqdocurl"]
                        logger.info(f"找到B站视频链接: {url}")

                        # 处理链接
                        async with aiohttp.ClientSession(
                            headers=get_user_agent()
                        ) as session:
                            async with session.get(url, timeout=7) as response:
                                real_url = str(response.url).split("?")[0]
                                if real_url.endswith("/"):
                                    real_url = real_url[:-1]

                                logger.info(f"重定向后的链接: {real_url}")

                                # 创建信息容器
                                information_container = InformationContainer()
                                await parse_bili_url(real_url, information_container)

                                if information_container.vd_info:
                                    return {
                                        "video_id": information_container.vd_info.get(
                                            "bvid"
                                        )
                                        or f"av{information_container.vd_info.get('aid')}",
                                        "title": information_container.vd_info.get(
                                            "title", "未知视频"
                                        ),
                                        "url": real_url,
                                    }

                # 检查是否是QQ小程序格式的B站视频卡片
                if "小程序" in data.get("prompt", ""):
                    logger.info("检测到QQ小程序格式")

                    # 使用辅助函数从JSON中提取URL
                    url = extract_url_from_json(data)

                    if not url:
                        # 尝试从JSON字符串中直接搜索URL
                        json_str = json.dumps(data)
                        url_match = re.search(
                            r"(https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+|https?://b23\.tv/[A-Za-z0-9]+)",
                            json_str,
                        )
                        if url_match:
                            url = url_match.group(0)

                    if url:
                        logger.info(f"从QQ小程序中找到B站链接: {url}")

                        # 处理链接
                        async with aiohttp.ClientSession(
                            headers=get_user_agent()
                        ) as session:
                            async with session.get(url, timeout=7) as response:
                                real_url = str(response.url).split("?")[0]
                                if real_url.endswith("/"):
                                    real_url = real_url[:-1]

                                logger.info(f"重定向后的链接: {real_url}")

                                # 创建信息容器
                                information_container = InformationContainer()
                                await parse_bili_url(real_url, information_container)

                                if information_container.vd_info:
                                    return {
                                        "video_id": information_container.vd_info.get(
                                            "bvid"
                                        )
                                        or f"av{information_container.vd_info.get('aid')}",
                                        "title": information_container.vd_info.get(
                                            "title", "未知视频"
                                        ),
                                        "url": real_url,
                                    }

                # 尝试直接从JSON中搜索B站链接
                json_str = json.dumps(data)
                bili_url = extract_bilibili_url(json_str)
                if bili_url:
                    logger.info(f"从JSON字符串中提取到B站链接: {bili_url}")

                    # 处理链接
                    async with aiohttp.ClientSession(
                        headers=get_user_agent()
                    ) as session:
                        async with session.get(bili_url, timeout=7) as response:
                            real_url = str(response.url).split("?")[0]
                            if real_url.endswith("/"):
                                real_url = real_url[:-1]

                            logger.info(f"重定向后的链接: {real_url}")

                            # 创建信息容器
                            information_container = InformationContainer()
                            await parse_bili_url(real_url, information_container)

                            if information_container.vd_info:
                                return {
                                    "video_id": information_container.vd_info.get(
                                        "bvid"
                                    )
                                    or f"av{information_container.vd_info.get('aid')}",
                                    "title": information_container.vd_info.get(
                                        "title", "未知视频"
                                    ),
                                    "url": real_url,
                                }
            except Exception as e:
                logger.error(f"解析B站视频卡片失败: {e}")
                import traceback

                logger.error(traceback.format_exc())

    return None


def int_to_datetime(timestamp: int) -> datetime.datetime:
    # 创建 UTC+8 时区的对象
    utc_plus_8 = datetime.timezone(datetime.timedelta(hours=8))

    # 将时间戳转换为 UTC+8 时区的 datetime 对象
    dt_utc_plus_8 = datetime.datetime.fromtimestamp(timestamp, tz=utc_plus_8)

    # 将 UTC+8 转换为 UTC 时区
    dt_utc = dt_utc_plus_8.astimezone(datetime.timezone.utc)

    return dt_utc


_matcher = on_message(priority=1, block=False, rule=_rule)


@_matcher.handle()
async def handle_message(event: MessageEvent, session: Uninfo, bot: Bot):
    group_id = str(session.group.id)  # 获取群组ID
    message_id = str(event.message_id)  # 从 event 获取 message_id
    message_content = event.raw_message
    message = event.message  # 关键修改点2：直接使用message对象

    # 判断是否是转发消息
    # if "[CQ:forward," in message_content:
    if any(seg.type == "forward" for seg in message):
        forward_message_id = message[0].data.get("id")
        forward_messages = await get_forward_messages(forward_message_id, bot)
        # 拼接所有的raw_message或file_unique
        concatenated_content = "+".join(forward_messages)
        logger.info(
            f"聊天记录 拼接后的消息: {concatenated_content}",
            "message_sent_check",
            session=session,
        )
        # 计算拼接后的内容的sha256
        sha256 = compute_sha256(concatenated_content)
        async with AsyncSessionLocal() as db_session:
            # 检查数据库中是否已有相同sha256的消息，并且相同的群ID
            existing_message = await find_existing_message(db_session, sha256, group_id)
            if existing_message:
                time_diff_str = get_time_diff_str(existing_message.timestamp)

                # 如果找到相同的消息，构造CQ码进行回复
                reply_message = Message(
                    MessageSegment.reply(existing_message.message_id)
                    + MessageSegment.at(event.user_id)
                    + MessageSegment.text(f"在{time_diff_str}就有人发过了喵")
                    + MessageSegment.image(
                        file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                    )
                )
                try:
                    await _matcher.finish(reply_message)
                except FinishedException:
                    pass
                except Exception as e:
                    logger.error(f"Error while sending reply: {e}")
                logger.info(
                    f"Repeated message detected: {message_id} with sha256 {sha256} in group {group_id}"
                )
            else:
                # 否则存储该消息
                await store_message(db_session, message_id, sha256, group_id)
                logger.info(
                    f"Stored forward message {message_id} with sha256 {sha256} to database in group {group_id}."
                )
        return

    # 检查是否是B站视频卡片
    bili_card_info = await extract_bilibili_card_info(message)
    if bili_card_info:
        # 获取视频信息
        video_id = bili_card_info["video_id"]
        video_title = bili_card_info["title"]
        # 直接使用视频ID作为唯一标识
        video_sha256 = f"bilibili_video_{video_id}"

        async with AsyncSessionLocal() as db_session:
            # 检查数据库中是否已有相同视频
            existing_message = await find_existing_message(
                db_session, video_sha256, group_id
            )
            if existing_message:
                # 如果找到相同的视频，构造回复消息
                time_diff_str = get_time_diff_str(existing_message.timestamp)

                reply_message = Message(
                    MessageSegment.reply(existing_message.message_id)
                    + MessageSegment.at(event.user_id)
                    + MessageSegment.text(
                        f"视频《{video_title}》在{time_diff_str}就有人发过了喵"
                    )
                    + MessageSegment.image(
                        file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                    )
                )
                try:
                    await _matcher.finish(reply_message)
                except FinishedException:
                    pass
                except Exception as e:
                    logger.error(f"Error while sending reply: {e}")
                logger.info(
                    f"Repeated video card detected: {message_id} with video_id {video_id} in group {group_id}"
                )
            else:
                # 否则存储该视频信息
                await store_message(db_session, message_id, video_sha256, group_id)
                logger.info(
                    f"Stored video card {message_id} with video_id {video_id} to database in group {group_id}."
                )
        return

    # 检查是否包含B站视频链接
    if contains_bilibili_url(message_content, message):
        # 提取B站视频链接
        bili_url = extract_bilibili_url(message_content)
        if bili_url:
            # 使用parse_bilibili插件解析视频信息
            information_container = InformationContainer()
            try:
                # 解析B站视频链接
                await parse_bili_url(bili_url, information_container)

                # 如果成功获取到视频信息
                if information_container.vd_info:
                    # 使用视频的BV号或AV号作为唯一标识
                    video_id = (
                        information_container.vd_info.get("bvid")
                        or f"av{information_container.vd_info.get('aid')}"
                    )
                    # 直接使用视频ID作为唯一标识，不需要计算sha256
                    video_sha256 = f"bilibili_video_{video_id}"

                    async with AsyncSessionLocal() as db_session:
                        # 检查数据库中是否已有相同视频
                        existing_message = await find_existing_message(
                            db_session, video_sha256, group_id
                        )
                        if existing_message:
                            # 如果找到相同的视频，构造回复消息
                            time_diff_str = get_time_diff_str(
                                existing_message.timestamp
                            )
                            video_title = information_container.vd_info.get(
                                "title", "未知视频"
                            )

                            reply_message = Message(
                                MessageSegment.reply(existing_message.message_id)
                                + MessageSegment.at(event.user_id)
                                + MessageSegment.text(
                                    f"视频《{video_title}》在{time_diff_str}就有人发过了喵"
                                )
                                + MessageSegment.image(
                                    file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                                )
                            )
                            try:
                                await _matcher.finish(reply_message)
                            except FinishedException:
                                pass
                            except Exception as e:
                                logger.error(f"Error while sending reply: {e}")
                            logger.info(
                                f"Repeated video detected: {message_id} with video_id {video_id} in group {group_id}"
                            )
                        else:
                            # 否则存储该视频信息
                            await store_message(
                                db_session, message_id, video_sha256, group_id
                            )
                            logger.info(
                                f"Stored video {message_id} with video_id {video_id} to database in group {group_id}."
                            )
                    return
            except Exception as e:
                logger.error(f"Error parsing Bilibili URL: {e}")

    # 如果不是B站视频链接，继续执行原有逻辑
    if is_valid_message(message):
        if file_unique := extract_file_unique(message_content):
            sha256 = file_unique
        else:
            sha256 = compute_sha256(message_content)

        async with AsyncSessionLocal() as db_session:
            # 检查数据库中是否已有相同sha256的消息，并且相同的群ID
            existing_message = await find_existing_message(db_session, sha256, group_id)
            if existing_message:
                # 如果找到相同的消息，构造CQ码进行回复
                time_diff_str = get_time_diff_str(existing_message.timestamp)

                # 如果找到相同的消息，构造CQ码进行回复
                reply_message = Message(
                    MessageSegment.reply(existing_message.message_id)
                    + MessageSegment.text(f"在{time_diff_str}就有人发过了喵")
                    + MessageSegment.image(
                        file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                    )
                )
                try:
                    await _matcher.finish(Message(reply_message))
                except FinishedException:
                    pass
                except Exception as e:
                    logger.error(f"Error while sending reply: {e}")
                logger.info(
                    f"Repeated message detected: {message_id} with sha256 {sha256} in group {group_id}"
                )
            else:
                # 否则存储该消息
                await store_message(db_session, message_id, sha256, group_id)
                logger.info(
                    f"Stored message {message_id} with sha256 {sha256} to database in group {group_id}."
                )
        return
    # 图片
    # if is_image_message(message):
    #     if session.group:
    #         if session.group.id == "696707598":
    #             _matcher.finish()
    #             return
    #     async with AsyncSessionLocal() as db_session:
    #         # 遍历所有图片段

    #         # event.reply.time
    #         concatenated_content = []
    #         for segment in message:
    #             # if seg.type == "image" and (file_unique := seg.data.get("file_unique")):
    #             if segment.type == "image":
    #                 file_unique = segment.data.get("file_unique")
    #                 concatenated_content.append(file_unique)
    #             # file_unique = seg.data.get("file_unique")
    #                 # 仅检测不存储
    #                 # if
    #         concatenated_content = "+".join(concatenated_content)
    #         sha256 = compute_sha256(concatenated_content)
    #         logger.info(f"拼接后的消息: {concatenated_content}", "message_sent_check",session=session)
    #         existing = await find_existing_message(db_session, sha256, group_id)
    #         if existing:
    #             time_diff_str = get_time_diff_str(existing.timestamp)
    #             reply = Message(
    #                 MessageSegment.reply(int(existing.message_id)) +
    #                 # Message("[CQ:reply,id=" + existing.message_id + "]") +
    #                 MessageSegment.text(f"在{time_diff_str}就有人发过了喵") +
    #                 MessageSegment.image(file=f"file:///{Path(__file__).parent}/saiboliequan.jpg")
    #             )
    #             await _matcher.finish(reply)
    #         # if not existing and
    #         original_message = event.message

    #         concatenated_content = []
    #         for segment in original_message:
    #             if segment.data.get("summary"):
    #                 _matcher.finish()
    #             if segment.type == "image":
    #                 file_unique = segment.data.get("file_unique")
    #                 file_size = segment.data.get("file_size")
    #                 file_type = segment.data.get("file").split('.')[-1]

    #                 if int(file_size) > 50_0000 and file_type != "gif":
    #                     concatenated_content.append(file_unique)
    #                 # return
    #         if concatenated_content != []:

    #             concatenated_content = "+".join(concatenated_content)
    #             sha256 = compute_sha256(concatenated_content)
    #             logger.info(f"拼接后的消息: {concatenated_content}", "message_sent_check",session=session)
    #             await store_message(db_session, message_id, sha256, group_id)
    #             logger.info(f"已自动记录 size >500000 图片(type:{file_type})消息 {message_id} with sha256 {sha256} in group {group_id}.","message_sent_check" ,session=session)

    #     return


# 新增的标记图片命令
mark_image = on_command("#标记", priority=5, block=True)


@mark_image.handle()
async def handle_mark_image(event: MessageEvent, bot: Bot, session: Uninfo):
    group_id = str(session.group.id)  # 获取群组ID

    concatenated_content = []
    # 判断是否为回复消息
    if event.reply:
        # 获取被回复消息的ID
        replied_message_id = str(event.reply.message_id)
        # 获取被回复消息的内容
        original_message: Message = event.reply.message
        original_message_content = event.reply.raw_message

        # 检查是否是B站视频卡片
        bili_card_info = await extract_bilibili_card_info(original_message)
        if bili_card_info:
            # 获取视频信息
            video_id = bili_card_info["video_id"]
            video_title = bili_card_info["title"]
            # 直接使用视频ID作为唯一标识
            video_sha256 = f"bilibili_video_{video_id}"

            async with AsyncSessionLocal() as db_session:
                # 查询数据库中是否已存在相同的视频
                existing_message = await find_existing_message(
                    db_session, video_sha256, group_id
                )
                if existing_message:
                    # 如果找到相同的视频，构造回复消息
                    time_diff_str = get_time_diff_str(existing_message.timestamp)
                    reply_message = Message(
                        MessageSegment.reply(existing_message.message_id)
                        + MessageSegment.text(
                            f"视频《{video_title}》在{time_diff_str}就有人标记过了，还标记，杂鱼~"
                        )
                        + MessageSegment.image(
                            file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                        )
                    )
                    await mark_image.finish(reply_message)
                else:
                    # 如果视频不在数据库中，手动存储
                    await store_message(
                        db_session,
                        replied_message_id,
                        video_sha256,
                        group_id,
                        timestamp=int_to_datetime(event.reply.time),
                    )
                    result_message = await mark_image.send(
                        f"视频《{video_title}》标记成功，五秒后撤回本消息~"
                    )
                    if isinstance(result_message, dict):
                        message_id = result_message.get("message_id")
                    else:
                        message_id = (
                            result_message.message_id
                        )  # 如果是 Message 对象，直接访问属性

                    if message_id:
                        await asyncio.sleep(5)
                        await bot.delete_msg(message_id=message_id)
                    else:
                        await mark_image.finish("cannot delete message")
                    await mark_image.finish()
            return

        # 检查是否包含B站视频链接
        if contains_bilibili_url(original_message_content, original_message):
            # 提取B站视频链接
            bili_url = extract_bilibili_url(original_message_content)
            if bili_url:
                # 使用parse_bilibili插件解析视频信息
                information_container = InformationContainer()
                try:
                    # 解析B站视频链接
                    await parse_bili_url(bili_url, information_container)

                    # 如果成功获取到视频信息
                    if information_container.vd_info:
                        # 使用视频的BV号或AV号作为唯一标识
                        video_id = (
                            information_container.vd_info.get("bvid")
                            or f"av{information_container.vd_info.get('aid')}"
                        )
                        video_title = information_container.vd_info.get(
                            "title", "未知视频"
                        )
                        # 直接使用视频ID作为唯一标识，不需要计算sha256
                        video_sha256 = f"bilibili_video_{video_id}"

                        async with AsyncSessionLocal() as db_session:
                            # 查询数据库中是否已存在相同的视频
                            existing_message = await find_existing_message(
                                db_session, video_sha256, group_id
                            )
                            if existing_message:
                                # 如果找到相同的视频，构造回复消息
                                time_diff_str = get_time_diff_str(
                                    existing_message.timestamp
                                )
                                reply_message = Message(
                                    MessageSegment.reply(existing_message.message_id)
                                    + MessageSegment.text(
                                        f"视频《{video_title}》在{time_diff_str}就有人标记过了，还标记，杂鱼~"
                                    )
                                    + MessageSegment.image(
                                        file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                                    )
                                )
                                await mark_image.finish(reply_message)
                            else:
                                # 如果视频不在数据库中，手动存储
                                await store_message(
                                    db_session,
                                    replied_message_id,
                                    video_sha256,
                                    group_id,
                                    timestamp=int_to_datetime(event.reply.time),
                                )
                                result_message = await mark_image.send(
                                    f"视频《{video_title}》标记成功，五秒后撤回本消息~"
                                )
                                if isinstance(result_message, dict):
                                    message_id = result_message.get("message_id")
                                else:
                                    message_id = (
                                        result_message.message_id
                                    )  # 如果是 Message 对象，直接访问属性

                                if message_id:
                                    await asyncio.sleep(5)
                                    await bot.delete_msg(message_id=message_id)
                                else:
                                    await mark_image.finish("cannot delete message")
                                await mark_image.finish()
                        return
                except Exception as e:
                    logger.error(f"Error parsing Bilibili URL: {e}")

        # 处理被回复的消息中的图片
        for segment in original_message:
            if segment.type == "image":
                file_unique = segment.data.get("file_unique")
                concatenated_content.append(file_unique)
            if segment.data.get("summary"):
                await mark_image.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("哪来的神人给表情包打标记...")
                    )
                )
                return
            # if file_unique:
            #     sha256 = file_unique  # 使用file_unique作为图片的标识符
        concatenated_content = "+".join(concatenated_content)
        # 如果没有图片，返回提示
        if concatenated_content == "":
            await mark_image.finish("没有检测到图片或视频消息，杂鱼♥")
        sha256 = compute_sha256(concatenated_content)
        logger.info(
            f"拼接后的消息: {concatenated_content}",
            "message_sent_check",
            session=session,
        )
        async with AsyncSessionLocal() as db_session:
            # 查询数据库中是否已存在相同的图片
            existing_message = await find_existing_message(db_session, sha256, group_id)
            if existing_message:
                # 如果找到相同的图片，构造回复消息
                time_diff_str = get_time_diff_str(existing_message.timestamp)
                reply_message = Message(
                    MessageSegment.reply(existing_message.message_id)
                    + MessageSegment.text(
                        f"该图片在{time_diff_str}就有人标记过了，还标记，杂鱼~"
                    )
                    + MessageSegment.image(
                        file=f"file:///{Path(__file__).parent}/saiboliequan.jpg"
                    )
                )
                await mark_image.finish(reply_message)
            else:
                # 如果图片不在数据库中，手动存储
                await store_message(
                    db_session,
                    replied_message_id,
                    sha256,
                    group_id,
                    timestamp=int_to_datetime(event.reply.time),
                )
                # await mark_image.send("图片已手动标记！")
                result_message = await mark_image.send("标记成功，五秒后撤回本消息~")
                if isinstance(result_message, dict):
                    message_id = result_message.get("message_id")
                else:
                    message_id = (
                        result_message.message_id
                    )  # 如果是 Message 对象，直接访问属性

                if message_id:
                    await asyncio.sleep(5)
                    await bot.delete_msg(message_id=message_id)
                # await bot.delete_msg(message_id=result_message.message_id)
                else:
                    await mark_image.finish("cannot delete message")
                await mark_image.finish()
            # else:
            #     await mark_image.finish("未能提取到图片的唯一标识符（file_unique）。")
            return
    else:
        await mark_image.finish(f"该命令需要回复一条消息,杂鱼{session.user.nickname}！")


# 删除标记的命令
delete_mark = on_command("#删除标记", priority=5, block=True, permission=SUPERUSER)


@delete_mark.handle()
async def handle_delete_mark(event: MessageEvent, bot: Bot):
    # 判断是否为回复消息
    if event.reply:
        # 获取被回复消息的ID
        replied_message_id = str(event.reply.message_id)
        async with AsyncSessionLocal() as db_session:
            # 查询数据库中是否已存在相同的消息
            existing_message = await find_message_by_id(db_session, replied_message_id)
            if existing_message:
                # 删除数据库中的记录
                await delete_message(db_session, existing_message.message_id)
                result_message = await delete_mark.send("消息标记已删除！")
                if isinstance(result_message, dict):
                    message_id = result_message.get("message_id")
                else:
                    message_id = (
                        result_message.message_id
                    )  # 如果是 Message 对象，直接访问属性

                if message_id:
                    await asyncio.sleep(5)
                    await bot.delete_msg(message_id=message_id)
            else:
                await delete_mark.finish("未找到该消息的标记记录。")
    else:
        await delete_mark.finish("该命令需要回复一条消息。")


# 插件加载时初始化数据库
async def on_start():
    await init_db()


# 插件卸载时关闭数据库连接
async def on_shutdown():
    await engine.dispose()


# 注册插件启动和关闭钩子
driver = get_driver()
driver.on_startup(on_start)
driver.on_shutdown(on_shutdown)
