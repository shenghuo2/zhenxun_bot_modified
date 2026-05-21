import datetime

import sqlalchemy
from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL

Base = declarative_base()

utcnow = lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False, unique=True)
    message_sha256 = Column(String, nullable=False)
    group_id = Column(String, nullable=False)
    sender_id = Column(String, nullable=True)  # 逗号分隔的发送者列表
    timestamp = Column(DateTime, default=utcnow)
    hit_count = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_sha256_group", "message_sha256", "group_id"),
    )


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """创建表并自动迁移缺失的列（兼容旧数据库）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 对已有的旧表补充新列（SQLite ALTER TABLE）
        for col_name, col_def in [
            ("hit_count", "INTEGER DEFAULT 1"),
            ("sender_id", "TEXT"),
        ]:
            try:
                await conn.execute(
                    sqlalchemy.text(
                        f"ALTER TABLE messages ADD COLUMN {col_name} {col_def}"
                    )
                )
            except Exception:
                pass  # 列已存在，忽略


async def close_db():
    await engine.dispose()


async def store_message(
    session: AsyncSession,
    message_id: str,
    sha256: str,
    group_id: str,
    sender_id: str | None = None,
    timestamp: datetime.datetime | None = None,
):
    record = MessageRecord(
        message_id=message_id,
        message_sha256=sha256,
        group_id=group_id,
        sender_id=sender_id,
        timestamp=timestamp or utcnow(),
        hit_count=1,
    )
    session.add(record)
    await session.commit()


async def increment_hit_count(
    session: AsyncSession, record: MessageRecord, sender_id: str | None = None
) -> int:
    """将 hit_count +1，累加发送者，并返回新的计数"""
    record.hit_count = (record.hit_count or 1) + 1
    if sender_id:
        if record.sender_id:
            # 累加，用逗号分隔
            record.sender_id = f"{record.sender_id},{sender_id}"
        else:
            record.sender_id = sender_id
    session.add(record)
    await session.commit()
    return record.hit_count


async def find_existing_message(
    session: AsyncSession, sha256: str, group_id: str
) -> MessageRecord | None:
    result = await session.execute(
        select(MessageRecord).filter_by(message_sha256=sha256, group_id=group_id)
    )
    return result.scalars().first()


async def find_message_by_id(
    session: AsyncSession, message_id: str
) -> MessageRecord | None:
    result = await session.execute(
        select(MessageRecord).filter_by(message_id=message_id)
    )
    return result.scalars().first()


async def delete_message_record(session: AsyncSession, message_id: str) -> bool:
    result = await session.execute(
        select(MessageRecord).filter_by(message_id=message_id)
    )
    record = result.scalars().first()
    if record:
        await session.delete(record)
        await session.commit()
        return True
    return False
