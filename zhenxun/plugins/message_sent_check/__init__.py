import hashlib
import re
from nonebot import on_message
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Bot, Message
from zhenxun.services.log import logger
import datetime
from pathlib import Path
from zhenxun.configs.config import Config
from nonebot import get_driver
from nonebot.exception import FinishedException
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

# 初始化 SQLAlchemy 部分
DATABASE_PATH = Path(__file__).parent / "messages.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
Base = declarative_base()

# 定义数据库模型
class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False, unique=True)
    message_sha256 = Column(String, nullable=False)
    group_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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
    description="记录所有非纯文字的消息的sha256和消息id，检测重复消息并自动回复",
    usage="自动记录消息的 sha256 和消息ID，存储到SQLite数据库中。若检测到重复消息，自动回复提示",
    extra={
        "author": "shenghuo2",
        "version": "0.2",
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
    }
)

# 计算sha256的函数
def compute_sha256(message: str) -> str:
    return hashlib.sha256(message.encode('utf-8')).hexdigest()

# 存储消息记录到数据库的异步函数
async def store_message(session: AsyncSession, message_id: str, sha256: str, group_id: str):
    message_record = MessageRecord(
        message_id=message_id,
        message_sha256=sha256,
        group_id=group_id
    )
    session.add(message_record)
    await session.commit()

# 查询数据库中是否已有相同的sha256和群ID
async def find_existing_message(session: AsyncSession, sha256: str, group_id: str) -> MessageRecord:
    result = await session.execute(
        select(MessageRecord).filter_by(
            message_sha256=sha256,
            group_id=group_id
        )
    )
    return result.scalars().first()

# 判断是否为纯文本消息
def is_pure_text(message: MessageEvent):
    return all(segment.type == "text" for segment in message)

# 插件的消息处理逻辑
async def _rule(session: Uninfo) -> bool:
    # 从配置中获取群号白名单
    group_whitelist = Config.get_config("message_sent_check", "GROUP_WHITELIST")
    
    if group_whitelist and session.group.id not in group_whitelist:
        return False  # 如果群不在白名单中，忽略该消息
    return True  # 如果群在白名单中，处理消息

def is_valid_message(message_content: str) -> bool:
    """
    判断消息是否为需要处理的图片、视频或转发消息， 
    同时忽略包含表情包的消息。
    """
    # 检查消息是否是图片、视频或转发消息
    if  message_content.startswith("[CQ:video,") or message_content.startswith("[CQ:forward,"):
        return True
    return False

# 用正则提取图片的 file_unique 字段
def extract_file_unique(message_content: str) -> str:
    match = re.search(r'file_unique=([a-fA-F0-9]+)', message_content)
    if match:
        return match.group(1)
    return None  # 如果没有匹配到，返回 None

# 获取转发消息的内容
async def get_forward_messages(forward_message_id: str,bot: Bot) -> list:
    try:
        response: dict = await bot.call_api("get_forward_msg", message_id=forward_message_id)
        messages = response.get("messages", [])
        # 提取 raw_message 或 file_unique（用于图片）
        return [msg["raw_message"] if not "file_unique" in msg else extract_file_unique(msg["raw_message"]) for msg in messages]
    except Exception as e:
        logger.error(f"Error fetching forward messages: {e}")
        return []
import html  # 导入html模块来解码HTML实体

# 获取转发消息的内容
async def get_forward_messages(forward_message_id: str, bot: Bot) -> list:
    try:
        response: dict = await bot.call_api("get_forward_msg", message_id=forward_message_id)
        messages = response.get("messages", [])
        # 提取 raw_message 或 file_unique（用于图片）
        forward_messages = []
        for msg in messages:
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
    now = datetime.datetime.utcnow()
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

_matcher = on_message(priority=1, block=False, rule=_rule)

@_matcher.handle()
async def handle_message(event: MessageEvent, session: Uninfo, bot: Bot):
    group_id = str(session.group.id)  # 获取群组ID
    message_id = str(event.message_id)  # 从 event 获取 message_id
    message_content = event.raw_message
    
    # 判断是否是转发消息
    if "[CQ:forward," in message_content:
        forward_message_id = re.search(r"id=(\d+)", message_content)
        if forward_message_id:
            forward_message_id = forward_message_id.group(1)
            # 获取转发消息内容
            forward_messages = await get_forward_messages(forward_message_id, bot)
            # 拼接所有的raw_message或file_unique
            concatenated_content = "+".join(forward_messages)
            logger.info(f"拼接后的消息: {concatenated_content}", "message_sent_check",session=session)
            # 计算拼接后的内容的sha256
            sha256 = compute_sha256(concatenated_content)
            async with AsyncSessionLocal() as db_session:
                # 检查数据库中是否已有相同sha256的消息，并且相同的群ID
                existing_message = await find_existing_message(db_session, sha256, group_id)
                if existing_message:
                    time_diff_str = get_time_diff_str(existing_message.timestamp)
                    
                    # 如果找到相同的消息，构造CQ码进行回复
                    reply_message = Message(
                        MessageSegment.reply(existing_message.message_id) + 
                        MessageSegment.text(f"在{time_diff_str}就有人发过了喵") + 
                        MessageSegment.image(file=f"file:///{Path(__file__).parent}/saiboliequan.jpg")
                    )
                    try:
                        await _matcher.finish(reply_message)
                    except FinishedException:
                        pass
                    except Exception as e:
                        logger.error(f"Error while sending reply: {e}")
                    logger.info(f"Repeated message detected: {message_id} with sha256 {sha256} in group {group_id}")
                else:
                    # 否则存储该消息
                    await store_message(db_session, message_id, sha256, group_id)
                    logger.info(f"Stored forward message {message_id} with sha256 {sha256} to database in group {group_id}.")
    else:
        # 如果不是转发消息，继续执行原有逻辑
        if is_valid_message(message_content):
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
                        MessageSegment.reply(existing_message.message_id) + 
                        MessageSegment.text(f"在{time_diff_str}就有人发过了喵") + 
                        MessageSegment.image(file=f"file:///{Path(__file__).parent}/saiboliequan.jpg")
                    )                    
                    try:
                        await _matcher.finish(Message(reply_message))
                    except FinishedException:
                        pass
                    except Exception as e:
                        logger.error(f"Error while sending reply: {e}")
                    logger.info(f"Repeated message detected: {message_id} with sha256 {sha256} in group {group_id}")
                else:
                    # 否则存储该消息
                    await store_message(db_session, message_id, sha256, group_id)
                    logger.info(f"Stored message {message_id} with sha256 {sha256} to database in group {group_id}.")
        else:
            # logger.info(f"Ignoring non-valid CQ message: {message_content}")
            pass

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
