import datetime

from sqlalchemy import Column, DateTime, Integer, String
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
    timestamp = Column(DateTime, default=utcnow)


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()


async def store_message(
    session: AsyncSession,
    message_id: str,
    sha256: str,
    group_id: str,
    timestamp: datetime.datetime | None = None,
):
    record = MessageRecord(
        message_id=message_id,
        message_sha256=sha256,
        group_id=group_id,
        timestamp=timestamp or utcnow(),
    )
    session.add(record)
    await session.commit()


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
