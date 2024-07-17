#!/usr/bin/python3
from email import message
from pyexpat.errors import messages
from re import T
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent,Message,Event,MessageSegment
from nonebot.params import ArgStr, CommandArg
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from utils.utils import get_message_text
from services.log import logger
from utils.message_builder import image
from .from_pixiv_setu import tagToImage, getCount, getSetuList

__zx_plugin_name__ = "新色图获取"
__plugin_usage__ = """
usage：
    搜张[keyword]
        实时搜索色图
    搜几张[keyword]
        返回5个结果
""".strip()
__plugin_des__ = "从Pixiv获取色图 但不是从老旧的数据库"
__plugin_cmd__ = ["搜张","搜几张",]
__plugin_version__ = 0.21
__plugin_author__ = "shenghuo2"
__plugin_settings__ = {
    "level": 9,
    "default_status": False,
    "limit_superuser": False,
    "cmd": ["搜张","搜几张",],
}
__plugin_type__ = ('工具',)
__plugin_cd_limit__ = {
    "cd": 3,
    "rst": "冲慢一点，要出来了！"
}
__plugin_count_limit__ = {
    "max_count": 30,
    "rst": "[at]你今天没得冲了！"
}

# 命令注册
setu_tag_get = on_command("搜张", priority=9, block=True)
setu_list_tag_get = on_command("搜几张", priority=9, block=True)
# 状态查询
@setu_tag_get.handle()
async def handle_setu_tag_get(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["搜张"] = args


@setu_tag_get.got("搜张", prompt="搜张[keyword]")
async def got_setu_tag_get(bot: Bot, event: Event, state: T_State):
    tag = str(state["搜张"])[2::]
    # 判断是不是数字pid
    if (tag.isnumeric()&(len(tag)==8))|(tag.isnumeric()&(len(tag)==9)):
        # 通过pid得到作品信息和图集
        setuInfoList,imageDict = tagToImage(tag)
        
        if setuInfoList['error'] == True:
            await setu_tag_get.finish(message='搜索不到该pid对应的图片')
            # 列出tags
        else:
            tagList = ""
            for tags in setuInfoList['body']['tags']['tags']:
                tagList += tags['tag'] + ","
            tagList = tagList[:-1]
            

            img = Message([
                    MessageSegment.text(
                                        f"作品名：{setuInfoList['body']['illustTitle']}\n"\
                                        f"画师名：{setuInfoList['body']['userName']}\n"\
                                        f"画师id：{setuInfoList['body']['userId']}\n"
                                        ),
                    MessageSegment.text(
                                        f"分辨率：{setuInfoList['body']['height']}x{setuInfoList['body']['width']}\n"\
                                        f"标签：{tagList}\n"\
                                        f"总页数：{setuInfoList['body']['pageCount']}页"
                                        )
            ])
            
            if "R-18" not in tagList:
                for picUrlNum in range(len(imageDict)):
                    img += MessageSegment.image(f'{imageDict[picUrlNum]}')
                    logger.info(f"{imageDict[picUrlNum]}已成功发出")
                    if picUrlNum == 4:
                        img += MessageSegment.text('超过五张的部分不再发出')
                        break

            if "R-18" in tagList:
                # img += MessageSegment.text(f'\n为了账号安全，含有r18标签的图片只发送第一张\n如果图寄了\n这是直链：\n{imageDict[0]}')
                img += MessageSegment.text(f'\nR18被拦截可能性高  这是图片直链：')
                for i in range(len(imageDict)):
                    img += MessageSegment.text(f'\n{imageDict[i]}')
                    logger.info(f"{imageDict[i]}已成功发出")
            try:
                # img += MessageSegment.text(f"共有{len(imageDict)}张")
                await setu_tag_get.finish(img)
            except Exception as e:
                error = ('错误明细是' + str(e.__class__.__name__) + str(e))
                if "Finished" in str(e.__class__.__name__):
                    await setu_tag_get.finish()
                await setu_tag_get.finish(message = error)
    else:
        tag = tag + "%2000users入り"
        # search_Count = getCount(tag)
        # await setu_tag_get.send(message = f"\"{tag[:-12]} 00users入り\"的搜索结果有{search_Count}条")
        search_result = tagToImage(tag)
        if len(search_result) == 1:
            msg = Message([
                MessageSegment.text("没有找到收藏较多的图  正在重新搜索"),
            ])
            await setu_tag_get.send(msg)
            tag = tag[:-12]
            # search_Count = getCount(tag)
            # await setu_tag_get.send(message = f"{tag}的搜索结果有{search_Count}条")
            search_result = tagToImage(tag)
            if len(search_result) == 1:
                msg = Message([
                MessageSegment.text("你的xp太奇怪辣 完全搜不到呢 建议去看看医生"),
                MessageSegment.image(f'https://c2cpicdw.qpic.cn/offpic_new/1308357113//1308357113-3516185286-3B858004C05950D3C21FAC772F0C5AC8/0'),
            ])
                await setu_tag_get.finish(msg)
        imageDict = search_result[1]
        setuDict = search_result[0]
    # if image == "1":
    #     msg = "没有找到质量较好的图  正在重新寻找"
    #     await setu_tag_get.send(message = msg)
    #     tag = tag[:-12]
    # elif image == "2":
    #     await setu_tag_get.send(message = "这张图太瑟 已经被lsp私藏了 没了/(ㄒoㄒ)/~~\n正在为你寻找新的")
    # elif image == "3":
    #     await setu_tag_get.finish(message = "这个pid的图被时间缝隙吞噬掉了\n  搜索不到 可能存在未来desu")
    # else:
        search_Count = getCount(tag)
        tag = tag.replace("%20",' ')
        img = Message([
                        
                        MessageSegment.text(
                                            f"pid：{setuDict['id']}\n"\
                                            f"作品名：{setuDict['title']}\n"
                                            ), 
                        MessageSegment.text(
                                            f"标签：{','.join(setuDict['tags'])}"\
                                            f"\n分辨率：{setuDict['height']}x{setuDict['width']}\n"\
                                            f"总页数：{setuDict['pageCount']}页\n"
                                            ), 
                        MessageSegment.text(
                                            f"作者名：{setuDict['userName']}\n"\
                                            f"作者uid：{setuDict['userId']}\n"\
                                            f"\"{tag}\"的搜索结果有{search_Count}条\n"
                                    ),
                    ])
        for picUrlNum in range(len(imageDict)):
            img += MessageSegment.image(f'{imageDict[picUrlNum]}')
            if picUrlNum == 4:
                img += MessageSegment.text('第5张之后的不展示了')
                logger.info(f"{imageDict[picUrlNum]}已成功发出")
                break
        try:
            await setu_tag_get.finish(img)
        except Exception as e:
            error = ('错误明细是' + str(e.__class__.__name__) + str(e))
            if "Finished" in str(e.__class__.__name__):
                await setu_tag_get.finish()
            await setu_tag_get.finish(message = error)
            
        # except "FinishedException":
        #     pass
        # except Exception as e:
        #     error = ('错误明细是' + str(e.__class__.__name__) + str(e))
        #     await setu_tag_get.finish(message = error)
    search_result = tagToImage(tag)
    if len(search_result) == 1:
        await setu_tag_get.finish(message = "你的xp太奇怪辣 完全搜不到呢 建议去看看医生")
    image = search_result[1]
    setuDict = search_result[0]
    try:
    #     if   image == "1":
    #         await setu_tag_get.finish(message = "你的xp太奇怪辣 完全搜不到呢 建议去看看医生")
    #     elif image == "2":
    #         await setu_tag_get.finish(message = "这张图太怪 已经被k蝠截获了 没了/(ㄒoㄒ)/~~")
    #     else:
        img = Message([
                        MessageSegment.text(f"pid：{setuDict['id']}\n作品名：{setuDict['title']}\n"), 
                        MessageSegment.text(f"标签：{','.join(setuDict['tags'])}\n分辨率：{setuDict['height']}x{setuDict['width']}"), 
                        MessageSegment.image(f'base64://{image}')
                    ])
        await setu_tag_get.send(img)
    except Exception as e:
        error = ('错误明细是' + str(e.__class__.__name__) + str(e))
        await setu_tag_get.finish(message = error)

# 状态查询
@setu_list_tag_get.handle()
async def handle_setu_tag_get(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["搜几张"] = args


@setu_list_tag_get.got("搜几张", prompt="搜几张[keyword]")
async def got_setu_tag_get(bot: Bot, event: Event, state: T_State):
    tag = str(state["搜几张"])[3::]
    try:
        tag = tag + "%2000users入り"
        
        msg = Message()
        setuList = getSetuList(tag)
        if setuList == "None":
            msg = Message([
                MessageSegment.text("没有找到超过5张收藏较多的图  正在重新搜索"),
            ])
            await setu_tag_get.send(msg)
            tag = tag[:-12]
            setuList = getSetuList(tag)

        for index in setuList:
            msg += MessageSegment.text(f"pid：{index[0]}\n")
            msg += MessageSegment.image(f'{index[1]}')
        await setu_list_tag_get.finish(msg)
    except Exception as e:
        error = ('错误明细是' + str(e.__class__.__name__) + str(e))
        if "Finished" in str(e.__class__.__name__):
            await setu_tag_get.finish()
        await setu_tag_get.finish(message = error)
