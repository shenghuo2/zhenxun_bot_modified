#!/usr/bin/python3
from nonebot import on_command ,on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent,Message,Event,MessageSegment
from nonebot.params import ArgStr, CommandArg
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from utils.utils import get_message_text
from services.log import logger
from utils.message_builder import image
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.adapters.onebot.v11 import GroupMessageEvent,PrivateMessageEvent
from .tools import gen_flag, CET4, GaoKao, DuanWu


__zx_plugin_name__ = "生活小工具合集"
__plugin_usage__ = """
QQ机器人工具集
    --shenghuo2
usage：
    使用注意这个命令有没有空格
    
    #四级考试
        显示最近的四级考试倒计时日期
""".strip()
__plugin_des__ = "工具汇总"
__plugin_cmd__ = ["#四级考试"]
__plugin_version__ = 0.01
__plugin_author__ = "shenghuo2"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["#四级考试"],
}
__plugin_type__ = ('工具',)
__plugin_cd_limit__ = {
    "cd": 2,
    "rst": "冷静点，要坏掉惹！"
}
# 命令注册
ip_query_command = on_command("#IP", priority=5, block=True)
gen_flag_command = on_command("#flag", priority=5, block=True)




# 四级考试时间计算
CET4_command = on_command("#四级考试", priority=5, block=True)

@CET4_command.handle()
async def handle_CET4_command(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#四级考试"] = args


@CET4_command.got("#四级考试", prompt="输入#四级考试")
async def got_CET4_command(bot: Bot, event: Event, state: T_State):
    msg = CET4()
    await CET4_command.finish(message = msg)

# flag生成
@gen_flag_command.handle()
async def handle_gen_flag(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#flag"] = args


@gen_flag_command.got("#flag", prompt="输入#flag")
async def got_gen_flag(bot: Bot, event: Event, state: T_State):
    msg = gen_flag()
    await gen_flag_command.finish(message = msg)


# 高考倒计时
GaoKao_countdown = on_command("#高考倒计时", priority=5, block=True)

@GaoKao_countdown.handle()
async def handle_GaoKao_countdown(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#高考倒计时"] = args


@GaoKao_countdown.got("#高考倒计时", prompt="输入#高考倒计时")
async def got_GaoKao_countdown(bot: Bot, event: Event, state: T_State):
    msg = GaoKao()
    await GaoKao_countdown.finish(message = msg)

# 端午
Duanwu_countdown = on_command("#端午", priority=5, block=True)

@Duanwu_countdown.handle()
async def handle_Duanwu_countdown(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#端午"] = args


@Duanwu_countdown.got("#端午", prompt="输入#端午")
async def got_Duanwu_countdown(bot: Bot, event: Event, state: T_State):
    # msg = GaoKao()
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id  # 获取群聊号
        # msg = f"群聊号：{group_id}\n"
        if group_id == "963496818":
            msg = DuanWu()+"\n亲爱的艾草精灵[CQ:at,qq=2293808331],你准备好艾草了吗"
        elif group_id == "787599185":
            msg = DuanWu()+"\n亲爱的艾草精灵[CQ:at,qq=1184474159],你准备好艾草了吗"
        else:
            msg = DuanWu()
        await Duanwu_countdown.finish(message = msg)

    elif isinstance(event, PrivateMessageEvent):
        # user_id = event.user_id  # 获取私聊用户qq号
        # msg = f"私聊用户号：{user_id}\n"
        await Duanwu_countdown.finish(message = DuanWu())

    