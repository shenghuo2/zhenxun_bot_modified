#!/usr/bin/python3
import json
from typing import Type
from cgitb import handler 
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent,Message,Event,MessageSegment
from nonebot.params import Arg, ArgStr, CommandArg
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from utils.utils import get_message_img, get_message_text
from services.log import logger
from utils.message_builder import image

from time import time
from .utils import *
__zx_plugin_name__ = "ChatGLM api接入"
__plugin_usage__ = """
usage：
    #AI 问题
        使用GLM4的模型进行对话，可以联网搜索
    #画图
        使用CogView3进行画图
    #识图
        使用glm4v进行图像内容识别
""".strip()
__plugin_des__ = "ChatGLM api接入"
__plugin_cmd__ = ["#AI",'#画图',"#识图"]
__plugin_version__ = 0.04
__plugin_author__ = "shenghuo2"
__plugin_settings__ = {
    "level": 5,
    "default_status": False,
    "limit_superuser": False,
    "cmd": ["#AI",
            '#画图',
            "#识图",
            ],
}
__plugin_type__ = ('工具',)
__plugin_cd_limit__ = {
    "cd": 5,
    "rst": "冷静点，要坏掉惹！" 
}
# 命令注册
ai_question_and_answer = on_command("#AI",aliases={'#ai'}, priority=5, block=True)
@ai_question_and_answer.handle()
async def handle_QA_args(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#AI"] = args


@ai_question_and_answer.got("#AI", prompt="请输入你的问题")
async def got_QA(bot: Bot, event: Event, state: T_State):

    args = str(state["#AI"]).strip()
    logger.info(f"args: {args}")
    if len(args)==3:
        await ai_question_and_answer.finish("请输入问题再提问")
    question = args[3:]
    start_time = time()
    wait = "您的消息正在处理，请稍后"
    if isinstance(event, GroupMessageEvent):
        wait += Message(f"[CQ:at,qq={event.get_user_id()}]")
        
    await ai_question_and_answer.send(message=Message(f"[CQ:reply,id={event.message_id}]")+wait)
        
    # answer = chatGLM_4_flash(question)
    answer = GLM_standard(question,'glm-4-0520')
    total_time = round(time() - start_time,2)
    answer = f"总共用时：{total_time}s\n"+ answer
    await ai_question_and_answer.finish(Message(f"[CQ:reply,id={event.message_id}]")+answer)
    
ai_draw = on_command("#画图", priority=5, block=True)
@ai_draw.handle()
async def handle_ai_draw_args(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["#画图"] = args


@ai_draw.got("#画图", prompt="请输入你要画的图像描述")
async def got_ai_draw(bot: Bot, event: Event, state: T_State):

    args = str(state["#画图"]).strip()
    logger.info(f"args: {args}")
    if len(args)==3:
        await ai_question_and_answer.finish("请输入你要画的图像描述")
    question = args[3:]
    start_time = time()
    wait = "您的图片正在“画”，请稍后"
    if isinstance(event, GroupMessageEvent):
        wait += Message(f"[CQ:at,qq={event.get_user_id()}]")
    await ai_question_and_answer.send(message=Message(f"[CQ:reply,id={event.message_id}]")+wait)
    
    image_url = cogView_image(question) 
    
    total_time = round(time() - start_time,2)
    if image_url.startswith('http') == False:
        await ai_question_and_answer.finish(f"【🥺】 绘画“{question.strip()}”出错，错误详情：{image_url}")
    answer = Message(f"总共用时：{total_time}s\n"+ MessageSegment.image(image_url))
    await ai_question_and_answer.finish(Message(f"[CQ:reply,id={event.message_id}]")+answer)
    

identify_image = on_command("#识图", priority=5, block=True)

@identify_image.handle()
async def handle_identify_image(bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()):
    img_url = get_message_img(event.json())
    if img_url:
        state["img_url"] = args
    # event.reply
    reply_type = event.reply
    if reply_type:
        logger.info(f"event.json(): {event.json()}")
        reply_message = await bot.get_msg(message_id= json.loads(event.json())['reply']['message_id'] )
        reply_message_segments = reply_message['message']
        state["img_url"] = Message(reply_message_segments)
        

@identify_image.got("img_url", prompt="虚空识图？来图来图GKD")
async def got_identify_image(bot: Bot, event: MessageEvent, state: T_State, img_url: Message = Arg("img_url")):
    img_url = get_message_img(img_url)
    if not img_url:
        await identify_image.reject_arg("img_url", "识别的必须是图片！")
    img_url = img_url[0]
    logger.info(f'img_url:{img_url}')
    await identify_image.send(Message(f"[CQ:reply,id={event.message_id}]")+"开始识别.....")
    start_time = time() 

    image_data = convert_jfif_to_base64_jpg(img_url)
    answer = identify_img_by_glm4v(image_url=image_data)
    
    total_time = round(time() - start_time,2)
    answer = Message(f"总共用时：{total_time}s\n"+ answer)
    await identify_image.finish(Message(f"[CQ:reply,id={event.message_id}]")+answer)
    