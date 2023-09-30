#!/usr/bin/python3
from typing import Type
from cgitb import handler 
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent,Message,Event,MessageSegment
from nonebot.params import ArgStr, CommandArg
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from utils.utils import get_message_text
from services.log import logger
from utils.message_builder import image
from .generate import generate_invitation

__zx_plugin_name__ = "SHCTF2023邀请函生成"
__plugin_usage__ = """
usage：
    SHCTF2023邀请函生成
        #邀请函 昵称 邀请函头像的QQ号(留空为发送者自身)

""".strip()
__plugin_des__ = "SHCTF2023邀请函生成 发送图片"
__plugin_cmd__ = ["#邀请函"]
__plugin_version__ = 0.11
__plugin_author__ = "Probius,shenghuo2"
__plugin_settings__ = {
    "level": 3,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["#邀请函",],
}
__plugin_type__ = ('工具',)
__plugin_cd_limit__ = {
    "cd": 1,
    "rst": "冷静点，要坏掉惹！" 
}
# 命令注册
SHCTF2023_invitation_gen = on_command("#邀请函", priority=3, block=True)

@SHCTF2023_invitation_gen.handle()
async def handle_invitation_args(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#邀请函"] = args


@SHCTF2023_invitation_gen.got("#邀请函", prompt="#邀请函 昵称 邀请函头像的QQ号(留空为发送者自身)")
async def got_invitation(bot: Bot, event: Event, state: T_State):
    args = str(state["#邀请函"]).split()
    if len(args)==1:
        await SHCTF2023_invitation_gen.finish('请输入生成邀请函的参数:\n#邀请函 昵称 邀请函头像的QQ号(留空为发送者自身)')
    nickName = args[1][:15]
    if len(args) >2:
        QQid = args[2]
    else:
        QQid = event.get_user_id()
    img_base64 = generate_invitation(nickName,QQid)

    img = MessageSegment.image(f'base64://{img_base64}')
    try:
        await SHCTF2023_invitation_gen.send(img)
    except Exception as e:
        error = ('错误明细是' + str(e.__class__.__name__) + str(e))
        await SHCTF2023_invitation_gen.finish(message = error)
    # logger.info(args)
    # logger.info()
    # ip = str(state["ip"])[3::]
    # ip = get_srv(ip)
    # img_base64 = mc_status_get(ip)
    # img = MessageSegment.image(f'base64://{img_base64}')
    # try:
    #     await SHCTF2023_invitation_gen.send(img)
    # except Exception as e:
    #     error = ('错误明细是' + str(e.__class__.__name__) + str(e))
    #     await SHCTF2023_invitation_gen.finish(message = error)


# mc_player_list = on_command("mcplayer", priority=5, block=True)
# mc_srv = on_command("mcsrv", priority=5, block=True)