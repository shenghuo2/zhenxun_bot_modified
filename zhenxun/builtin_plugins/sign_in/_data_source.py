from datetime import datetime
from pathlib import Path
import random
import secrets

from nonebot_plugin_uninfo import Uninfo
import pytz

from zhenxun.configs.path_config import IMAGE_PATH
from zhenxun.models.friend_user import FriendUser
from zhenxun.models.group_member_info import GroupInfoUser
from zhenxun.models.sign_log import SignLog
from zhenxun.models.sign_user import SignUser
from zhenxun.models.user_gold_log import UserGoldLog
from zhenxun.models.user_console import UserConsole
from zhenxun.services.log import logger
from zhenxun.utils.image_utils import BuildImage, ImageTemplate
from zhenxun.utils.platform import PlatformUtils

from ._random_event import random_event
from .utils import get_card

ICON_PATH = IMAGE_PATH / "_icon"

PLATFORM_PATH = {
    "dodo": ICON_PATH / "dodo.png",
    "discord": ICON_PATH / "discord.png",
    "kaiheila": ICON_PATH / "kook.png",
    "qq": ICON_PATH / "qq.png",
}

BOT_PVE_LOG_PREFIX = "__bot_sign_pve__"
BOT_PVE_BONUS_PREFIX = "pve_bonus:"


class SignManage:
    @classmethod
    def _get_bot_pve_log_user_id(cls, session: Uninfo) -> str:
        platform = PlatformUtils.get_platform(session)
        return f"{BOT_PVE_LOG_PREFIX}:{platform}:{session.self_id}"

    @classmethod
    def _get_bot_pve_bonus(cls, log: SignLog) -> float:
        if not log.bot_id or not log.bot_id.startswith(BOT_PVE_BONUS_PREFIX):
            return 0.0
        try:
            return float(log.bot_id.removeprefix(BOT_PVE_BONUS_PREFIX))
        except ValueError:
            return 0.0

    @classmethod
    async def _get_today_bot_pve(cls, session: Uninfo) -> tuple[float, float, float]:
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        platform = PlatformUtils.get_platform(session)
        user_id = cls._get_bot_pve_log_user_id(session)
        pve_log = await SignLog.filter(user_id=user_id, platform=platform).order_by(
            "-create_time"
        ).first()
        if pve_log and pve_log.create_time.astimezone(
            pytz.timezone("Asia/Shanghai")
        ).date() == now.date():
            base_score = float(pve_log.impression)
            extra_score = cls._get_bot_pve_bonus(pve_log)
            return base_score, extra_score, base_score + extra_score

        base_score = (secrets.randbelow(99) + 1) / 100
        extra_score = round(random.uniform(0, 0.25), 3)
        await SignLog.create(
            user_id=user_id,
            impression=base_score,
            bot_id=f"{BOT_PVE_BONUS_PREFIX}{extra_score:.3f}",
            platform=platform,
        )
        logger.info(
            f"生成 bot 本日签到 PVE 值. base: {base_score:.2f}, extra: {extra_score:.2f}",
            "签到",
            session=session,
        )
        return base_score, extra_score, base_score + extra_score

    @classmethod
    async def _get_today_sign_result(
        cls, user: SignUser, session: Uninfo
    ) -> tuple[float | None, float, bool | None, float | None, int | None]:
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        today_log = await SignLog.filter(user_id=user.user_id).order_by("-create_time").first()
        if not today_log:
            return None, 0.0, None, None, None
        if (
            today_log.create_time.astimezone(pytz.timezone("Asia/Shanghai")).date()
            != now.date()
        ):
            return None, 0.0, None, None, None

        today_gold_log = await UserGoldLog.filter(
            user_id=user.user_id, source="sign_in"
        ).order_by("-create_time").first()
        today_gold = None
        if today_gold_log and (
            today_gold_log.create_time.astimezone(pytz.timezone("Asia/Shanghai")).date()
            == now.date()
        ):
            today_gold = today_gold_log.gold

        bot_base_score, bot_extra_score, bot_total_score = await cls._get_today_bot_pve(
            session
        )
        return (
            bot_base_score,
            bot_extra_score,
            float(today_log.impression) > bot_total_score,
            float(today_log.impression),
            today_gold,
        )

    @classmethod
    async def rank(
        cls, session: Uninfo, num: int, group_id: str | None = None
    ) -> BuildImage | str:  # sourcery skip: avoid-builtin-shadow
        """好感度排行

        参数:
            session: Uninfo
            num: 排行榜数量
            group_id: 群组id

        返回:
            BuildImage: 构造图片
        """
        query = SignUser
        if group_id:
            user_list = await GroupInfoUser.filter(group_id=group_id).values_list(
                "user_id", flat=True
            )
            if user_list:
                query = query.filter(user_id__in=user_list)
        user_list = (
            await query.annotate()
            .order_by("-impression")
            .values_list("user_id", "impression", "sign_count", "platform")
        )
        if not user_list:
            return "当前还没有人签到过哦..."
        user_id_list = [user[0] for user in user_list]
        if session.user.id in user_id_list:
            index = user_id_list.index(session.user.id) + 1
        else:
            index = "-1（未统计）"
        user_list = user_list[:num] if num < len(user_list) else user_list
        column_name = ["排名", "-", "名称", "好感度", "签到次数", "平台"]
        friend_list = await FriendUser.filter(user_id__in=user_id_list).values_list(
            "user_id", "user_name"
        )
        uid2name = {f[0]: f[1] for f in friend_list}
        if diff_id := set(user_id_list).difference(set(uid2name.keys())):
            group_user = await GroupInfoUser.filter(user_id__in=diff_id).values_list(
                "user_id", "user_name"
            )
            for g in group_user:
                uid2name[g[0]] = g[1]
        data_list = []
        platform = PlatformUtils.get_platform(session)
        for i, user in enumerate(user_list):
            bytes = await PlatformUtils.get_user_avatar(
                user[0], platform, session.self_id
            )
            data_list.append(
                [
                    f"{i+1}",
                    (bytes, 30, 30) if user[3] == "qq" else "",
                    uid2name.get(user[0]),
                    user[1],
                    user[2],
                    (PLATFORM_PATH.get(user[3]), 30, 30),
                ]
            )
        if group_id:
            title = "好感度群组内排行"
            tip = f"你的排名在本群第 {index} 位哦!"
        else:
            title = "好感度全局排行"
            tip = f"你的排名在全局第 {index} 位哦!"
        return await ImageTemplate.table_page(title, tip, column_name, data_list)

    @classmethod
    async def sign(
        cls, session: Uninfo, nickname: str, is_card_view: bool = False
    ) -> Path:
        """签到

        参数:
            session: Uninfo
            nickname: 用户昵称
            is_card_view: 是否展示卡片

        返回:
            Path: 卡片路径
        """
        platform = PlatformUtils.get_platform(session)
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        user_console = await UserConsole.get_user(session.user.id, platform)
        user, _ = await SignUser.get_or_create(
            user_id=session.user.id,
            defaults={"user_console": user_console, "platform": platform},
        )
        new_log = (
            await SignLog.filter(user_id=session.user.id)
            .order_by("-create_time")
            .first()
        )
        log_time = None
        if new_log:
            log_time = new_log.create_time.astimezone(
                pytz.timezone("Asia/Shanghai")
            ).date()
        if not is_card_view and (not new_log or (log_time and log_time != now.date())):
            return await cls._handle_sign_in(user, nickname, session)
        bot_base_score, bot_extra_score, pve_win, add_impression, gold = (
            await cls._get_today_sign_result(user, session)
        )
        return await get_card(
            user,
            session,
            nickname,
            add_impression or -1,
            gold,
            "",
            is_card_view=False,
            bot_base_score=bot_base_score,
            bot_extra_score=bot_extra_score,
            pve_win=pve_win,
        )

    @classmethod
    async def _handle_sign_in(
        cls,
        user: SignUser,
        nickname: str,
        session: Uninfo,
    ) -> Path:
        """签到处理

        参数:
            user: SignUser
            nickname: 用户昵称
            session: Uninfo

        返回:
            Path: 卡片路径
        """
        platform = PlatformUtils.get_platform(session)
        impression_added = (secrets.randbelow(99) + 1) / 100
        rand = random.random()
        add_probability = float(user.add_probability)
        specify_probability = user.specify_probability
        if rand + add_probability > 0.97 or rand < specify_probability:
            impression_added *= 2
        bot_base_score, bot_extra_score, bot_total_score = await cls._get_today_bot_pve(
            session
        )
        pve_win = impression_added > bot_total_score
        await SignUser.sign(user, impression_added, session.self_id, platform)
        gold = random.randint(1, 100)
        gift = random_event(float(user.impression))
        if isinstance(gift, int):
            gold += gift
            await UserConsole.add_gold(user.user_id, gold + gift, "sign_in", platform)
            gift = f"额外金币 +{gift}"
        else:
            await UserConsole.add_gold(user.user_id, gold, "sign_in", platform)
            await UserConsole.add_props_by_name(user.user_id, gift, 1, platform)
            gift += " + 1"
        logger.info(
            f"签到成功. score: {user.impression:.2f} "
            f"(+{impression_added:.2f}).获取金币/道具: {gold}. "
            f"对决结果: {'win' if pve_win else 'lose'} vs {bot_total_score:.2f} "
            f"(base {bot_base_score:.2f} + {bot_extra_score:.2f})",
            "签到",
            session=session,
        )
        return await get_card(
            user,
            session,
            nickname,
            impression_added,
            gold,
            gift,
            rand + add_probability > 0.97 or rand < specify_probability,
            bot_base_score=bot_base_score,
            bot_extra_score=bot_extra_score,
            pve_win=pve_win,
        )
