from datetime import datetime

from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Alconna, Args, Arparma, At, on_alconna
from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_uninfo import Uninfo

from zhenxun.builtin_plugins.sign_in.config import (
    SIGN_TODAY_CARD_PATH,
    level2attitude,
    lik2level,
    lik2relation,
)
from zhenxun.builtin_plugins.sign_in.utils import (
    get_level_and_next_impression,
    generate_progress_bar_pic,
    MORNING_MESSAGE,
    LG_MESSAGE,
)
from zhenxun.configs.config import BotConfig
from zhenxun.configs.path_config import IMAGE_PATH, TEMPLATE_PATH
from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.models.friend_user import FriendUser
from zhenxun.models.group_member_info import GroupInfoUser
from zhenxun.models.sign_user import SignUser
from zhenxun.services.log import logger
from zhenxun.utils.depends import UserName
from zhenxun.utils.image_utils import BuildImage
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.platform import PlatformUtils

__plugin_meta__ = PluginMetadata(
    name="自欺欺人喵",
    description="生成一个假的签到卡片，自欺欺人用",
    usage="""
    生成假的签到卡片
    指令:
        #假签到 - 生成自己的假签到卡片
        #假签到 @用户 - 生成指定用户的假签到卡片
        #假签到 @用户 数字 - 生成指定用户的假签到卡片，并指定好感度增加值
        #假签到 数字 - 生成自己的假签到卡片，并指定好感度增加值
    """.strip(),
    extra=PluginExtraData(
        author="shenghuo2",
        version="0.1",
        commands=[
            Command(command="#假签到"),
        ],
    ).to_dict(),
)

_fake_sign_matcher = on_alconna(
    Alconna(
        "#假签到",
        Args["target?", At]["impression?", float],
    ),
    priority=5,
    block=True,
    permission=SUPERUSER,
)

_fake_sign_matcher.shortcut(
    "ssbk",
    command="#假签到",
    arguments=["1.99"],
    prefix=True,
)


@_fake_sign_matcher.handle()
async def _(
    session: Uninfo,
    arparma: Arparma,
    nickname: str = UserName(),
):
    target = arparma.query[At]("target")
    impression_value = arparma.query[float]("impression")

    # 确定目标用户
    if target:
        target_user_id = target.target
    else:
        target_user_id = session.user.id

    # 获取用户数据
    user = await SignUser.filter(user_id=target_user_id).first()

    if not user:
        await MessageUtils.build_message(
            "该用户还没有签到过哦，无法生成假签到卡片~"
        ).finish()

    # 确定好感度增加值
    if impression_value is not None:
        add_impression = impression_value
    else:
        add_impression = 0.50  # 默认值

    # 获取目标用户昵称和头像
    if target:
        target_nickname = await _get_user_nickname(target_user_id)
        platform = PlatformUtils.get_platform(session)
        target_avatar = PlatformUtils.get_user_avatar_url(
            target_user_id, platform, session.self_id
        )
    else:
        target_nickname = nickname
        target_avatar = session.user.avatar

    # 生成假签到卡片（不使用缓存，直接生成新图片）
    gift = "自欺欺人的礼物"
    gold = 50
    is_double = add_impression >= 1.0

    path = await _generate_fake_card(
        user,
        target_nickname,
        target_avatar,
        add_impression,
        gold,
        gift,
        is_double,
    )

    logger.info(
        f"生成假签到卡片. 目标: {target_user_id}, 好感度: +{add_impression}",
        "自欺欺人喵",
        session=session,
    )
    await MessageUtils.build_message(["喵~ 假签到卡片生成成功！\n", path]).finish()


async def _get_user_nickname(user_id: str) -> str:
    """获取用户昵称"""
    # 尝试从好友列表获取
    friend = await FriendUser.filter(user_id=user_id).first()
    if friend and friend.user_name:
        return friend.user_name

    # 尝试从群成员信息获取
    group_user = await GroupInfoUser.filter(user_id=user_id).first()
    if group_user and group_user.user_name:
        return group_user.user_name

    return f"用户{user_id}"


async def _generate_fake_card(
    user: SignUser,
    nickname: str,
    avatar_url: str | None,
    add_impression: float,
    gold: int,
    gift: str,
    is_double: bool = False,
):
    """生成假签到卡片（不使用缓存）"""
    await generate_progress_bar_pic()

    impression = float(user.impression)
    user_console = await user.user_console
    if user_console and user_console.uid is not None:
        uid = f"{user_console.uid}".rjust(12, "0")
        uid = f"{uid[:4]} {uid[4:8]} {uid[8:]}"
    else:
        uid = "XXXX XXXX XXXX"
    level, next_impression, previous_impression = get_level_and_next_impression(
        impression
    )
    interpolation = next_impression - impression
    message = f"{BotConfig.self_nickname}希望你开心！"
    hour = datetime.now().hour
    if hour > 6 and hour < 10:
        message = MORNING_MESSAGE[0]
    elif hour >= 0 and hour < 6:
        message = LG_MESSAGE[0]
    _impression = f"{add_impression}(×2)" if is_double else add_impression
    process = 1 - (next_impression - impression) / (
        next_impression - previous_impression
    )
    now = datetime.now()
    data = {
        "ava_url": avatar_url,
        "name": nickname,
        "uid": uid,
        "sign_count": f"{user.sign_count}",
        "message": f"{BotConfig.self_nickname}说: {message}",
        "cur_impression": f"{impression:.2f}",
        "impression": f"好感度+{_impression}",
        "gold": f"金币+{gold}",
        "gift": gift,
        "level": f"{level} [{lik2relation[level]}]",
        "attitude": f"对你的态度: {level2attitude[level]}",
        "interpolation": f"{interpolation:.2f}",
        "heart2": [1 for _ in range(int(level))],
        "heart1": [1 for _ in range(len(lik2level) - int(level) - 1)],
        "process": process * 100,
        "date": str(now.replace(microsecond=0)),
        "font_size": 45,
    }
    if len(nickname) > 6:
        data["font_size"] = 27

    pic = await template_to_pic(
        template_path=str((TEMPLATE_PATH / "sign").absolute()),
        template_name="main.html",
        templates={"data": data},
        pages={
            "viewport": {"width": 465, "height": 926},
            "base_url": f"file://{TEMPLATE_PATH}",
        },
        wait=2,
    )
    image = BuildImage.open(pic)
    # 使用 fake_ 前缀避免与真实签到卡片冲突
    date = now.date()
    timestamp = int(now.timestamp())
    file_name = f"fake_{user.user_id}_{date}_{timestamp}.png"
    await image.save(SIGN_TODAY_CARD_PATH / file_name)
    return IMAGE_PATH / "sign" / "today_card" / file_name
