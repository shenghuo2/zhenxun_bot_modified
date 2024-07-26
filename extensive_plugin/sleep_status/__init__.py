import time
from typing import Any, Tuple
import requests

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import RegexGroup

from configs.config import Config
from configs.path_config import TEMP_PATH
from services.log import logger
from utils.http_utils import AsyncHttpx
from utils.manager import withdraw_message_manager
from utils.message_builder import image

__zx_plugin_name__ = "睡眠状态"
__plugin_usage__ = """
usage：
    查询生蚝似了吗
    指令：
        #查询生蚝状态
        #生蚝状态
        
""".strip()
__plugin_des__ = "查询睡眠状态"
__plugin_cmd__ = ["#查询生蚝状态"]
__plugin_version__ = 0.1
__plugin_author__ = "HibiKier"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["#查询生蚝状态", "#生蚝状态"],
}


query_status = on_command('#查询生蚝状态',aliases={'#生蚝状态'} , priority=5, block=True)


url = "http://3.113.17.244:8000/status"


def get_sleep_status_json()-> dict:
    return requests.get(url).json()
    
def get_sleep_status():
    # requests.get(url).json()
    try:
        return requests.get(url,timeout=5).json()['sleep']
    except Exception as e:
        return str(e)


@query_status.handle()
async def _():
    result = get_sleep_status()
    if type(result) == bool:
        if result:
            await query_status.finish("似了😴")
            
        await query_status.finish("活着🧐")
    else:
        await query_status.finish("连查询状态的服务器都似了🤣:"+result)
