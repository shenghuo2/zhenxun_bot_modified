from typing import List, Optional, Set

from tortoise import fields

from configs.config import Config
from services.db_context import Model


class GroupInfoUser(Model):

    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    """自增id"""
    user_qq = fields.BigIntField()
    """用户id"""
    user_name = fields.CharField(255)
    """用户昵称"""
    group_id = fields.BigIntField()
    """群聊id"""
    user_join_time = fields.DatetimeField()
    """用户入群时间"""
    nickname = fields.CharField(255)
    """群聊昵称"""
    uid = fields.BigIntField()
    """用户uid"""

    class Meta:
        table = "group_info_users"
        table_description = "群员信息数据表"
        unique_together = ("user_qq", "group_id")

    @classmethod
    async def get_group_member_id_list(cls, group_id: int) -> Set[int]:
        """
        说明:
            获取该群所有用户qq
        参数:
            :param group_id: 群号
        """
        return set(
            await cls.filter(group_id=group_id).values_list("user_qq", flat=True)
        )

    @classmethod
    async def set_user_nickname(
        cls, user_qq: int, group_id: int, nickname: str
    ) -> bool:
        """
        说明:
            设置群员在该群内的昵称
        参数:
            :param user_qq: qq号
            :param group_id: 群号
            :param nickname: 昵称
        """
        if user := await cls.get_or_none(user_qq=user_qq, group_id=group_id):
            user.nickname = nickname
            await user.save(update_fields=["nickname"])
            return True
        return False

    @classmethod
    async def get_user_all_group(cls, user_qq: int) -> List[int]:
        """
        说明:
            获取该用户所在的所有群聊
        参数:
            :param user_qq: 用户qq
        """
        return list(
            await cls.filter(user_qq=user_qq).values_list("group_id", flat=True)
        )

    @classmethod
    async def get_user_nickname(cls, user_qq: int, group_id: int) -> str:
        """
        说明:
            获取用户在该群的昵称
        参数:
            :param user_qq: qq号
            :param group_id: 群号
        """
        if user := await cls.get_or_none(user_qq=user_qq, group_id=group_id):
            if user.nickname:
                nickname = ""
                if black_word := Config.get_config("nickname", "BLACK_WORD"):
                    for x in user.nickname:
                        nickname += "*" if x in black_word else x
                    return nickname
                return user.nickname
        return ""

    @classmethod
    async def get_group_member_uid(cls, user_qq: int, group_id: int) -> Optional[str]:
        pass
        # query = cls.query.where((cls.user_qq == user_qq) & (cls.group_id == group_id))
        # user = await query.gino.first()
        # _max_uid = cls.query.where(
        #     (cls.user_qq == 114514) & (cls.group_id == 114514)
        # ).with_for_update()
        # _max_uid_user = await _max_uid.gino.first()
        # _max_uid = _max_uid_user.uid
        # if not user or not user.uid:
        #     all_user = await cls.query.where(cls.user_qq == user_qq).gino.all()
        #     for x in all_user:
        #         if x.uid:
        #             return x.uid
        #     else:
        #         if not user:
        #             await GroupInfoUser.add_member_info(
        #                 user_qq, group_id, "", datetime.min
        #             )
        #             user = await cls.query.where(
        #                 (cls.user_qq == user_qq) & (cls.group_id == group_id)
        #             ).gino.first()
        #         await user.update(
        #             uid=_max_uid + 1,
        #         ).apply()
        #         await _max_uid_user.update(
        #             uid=_max_uid + 1,
        #         ).apply()

        # return user.uid if user and user.uid else None
