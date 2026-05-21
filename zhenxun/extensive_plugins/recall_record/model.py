from __future__ import annotations

from datetime import datetime

from tortoise import fields

from zhenxun.services.db_context import Model


class RecallRecord(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    """自增id"""
    group_id = fields.CharField(255, description="群号")
    """群号"""
    user_id = fields.CharField(255, description="原消息发送者QQ")
    """原消息发送者QQ"""
    user_name = fields.CharField(255, null=True, description="发送者群昵称")
    """发送者群昵称"""
    message_id = fields.CharField(255, description="消息ID")
    """消息ID"""
    raw_message = fields.TextField(null=True, description="原始消息内容")
    """原始消息内容"""
    plain_text = fields.TextField(null=True, description="纯文本消息内容")
    """纯文本消息内容"""
    operator_id = fields.CharField(255, null=True, description="执行撤回者QQ")
    """执行撤回者QQ"""
    is_recalled = fields.BooleanField(default=False, description="是否已撤回")
    """是否已撤回"""
    message_time = fields.DatetimeField(description="原消息时间")
    """原消息时间"""
    recall_time = fields.DatetimeField(null=True, description="撤回时间")
    """撤回时间"""
    bot_id = fields.CharField(255, null=True, description="bot id")
    """bot id"""
    platform = fields.CharField(255, null=True, description="平台")
    """平台"""
    create_time = fields.DatetimeField(auto_now_add=True)
    """记录创建时间"""

    class Meta:  # pyright: ignore [reportIncompatibleVariableOverride]
        table = "recall_record"
        table_description = "群消息撤回记录表"
        unique_together = ("group_id", "message_id")
        indexes = (
            ("group_id", "is_recalled"),
            ("group_id", "recall_time"),
        )

    @classmethod
    async def upsert_message(
        cls,
        *,
        group_id: str,
        user_id: str,
        user_name: str,
        message_id: str,
        raw_message: str | None,
        plain_text: str | None,
        message_time: datetime,
        bot_id: str | None = None,
        platform: str | None = None,
    ) -> tuple["RecallRecord", bool]:
        return await cls.update_or_create(
            group_id=group_id,
            message_id=message_id,
            defaults={
                "user_id": user_id,
                "user_name": user_name,
                "raw_message": raw_message,
                "plain_text": plain_text,
                "message_time": message_time,
                "bot_id": bot_id,
                "platform": platform,
            },
        )

    @classmethod
    async def mark_recalled(
        cls,
        *,
        group_id: str,
        user_id: str,
        user_name: str,
        message_id: str,
        operator_id: str | None,
        recall_time: datetime,
        bot_id: str | None = None,
        platform: str | None = None,
    ) -> tuple["RecallRecord", bool]:
        if record := await cls.get_or_none(group_id=group_id, message_id=message_id):
            record.user_id = user_id
            record.user_name = user_name
            record.operator_id = operator_id
            record.is_recalled = True
            record.recall_time = recall_time
            record.bot_id = bot_id or record.bot_id
            record.platform = platform or record.platform
            await record.save(
                update_fields=[
                    "user_id",
                    "user_name",
                    "operator_id",
                    "is_recalled",
                    "recall_time",
                    "bot_id",
                    "platform",
                ]
            )
            return record, False

        record = await cls.create(
            group_id=group_id,
            user_id=user_id,
            user_name=user_name,
            message_id=message_id,
            operator_id=operator_id,
            is_recalled=True,
            message_time=recall_time,
            recall_time=recall_time,
            bot_id=bot_id,
            platform=platform,
        )
        return record, True

    @classmethod
    async def get_recent_recalled(
        cls,
        *,
        group_id: str | None = None,
        limit: int = 10,
    ) -> list["RecallRecord"]:
        query = cls.filter(is_recalled=True)
        if group_id:
            query = query.filter(group_id=group_id)
        return await query.order_by("-recall_time", "-message_time").limit(limit)

    @classmethod
    async def get_recalled_by_date(
        cls,
        *,
        start_time: datetime,
        end_time: datetime,
        group_id: str | None = None,
    ) -> list["RecallRecord"]:
        query = cls.filter(
            is_recalled=True,
            recall_time__gte=start_time,
            recall_time__lt=end_time,
        )
        if group_id:
            query = query.filter(group_id=group_id)
        return await query.order_by("-recall_time", "-message_time")

    @classmethod
    async def get_recalled_by_message_id(
        cls,
        *,
        message_id: str,
        group_id: str | None = None,
    ) -> list["RecallRecord"]:
        query = cls.filter(is_recalled=True, message_id=message_id)
        if group_id:
            query = query.filter(group_id=group_id)
        return await query.order_by("-recall_time", "-message_time")
