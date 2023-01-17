from typing import List

from gino import Gino
from tortoise import Tortoise, run_async
from tortoise.connection import connections
from tortoise.models import Model as Model_

from configs.config import address, bind, database, password, port, sql_name, user
from utils.text_utils import prompt2cn

from .log import logger

MODELS: List[str] = []


class Model(Model_):
    """自动添加模块

    Args:
        Model_ (_type_): _description_
    """

    def __init_subclass__(cls, **kwargs):
        MODELS.append(cls.__module__)


def add_model(model: str):
    """
    添加加载模型

    Args:
        model (str): 模型路径
    """
    if model not in MODELS:
        MODELS.append(model)


async def init():
    if not bind and not any([user, password, address, port, database]):
        raise ValueError("\n" + prompt2cn("数据库配置未填写", 28))
    i_bind = bind
    if not i_bind:
        i_bind = f"{sql_name}://{user}:{password}@{address}:{port}/{database}"
    try:
        await Tortoise.init(db_url=i_bind, modules={"models": MODELS})
        await Tortoise.generate_schemas()
        logger.info(f"Database loaded successfully!")
    except Exception as e:
        raise Exception(f"数据库连接错误.... {type(e)}: {e}")


async def disconnect():
    await connections.close_all()
