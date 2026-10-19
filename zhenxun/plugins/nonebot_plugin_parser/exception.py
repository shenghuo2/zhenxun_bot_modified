from collections.abc import Callable
from functools import wraps

from nonebot.internal.matcher import current_matcher


class ResolverException(Exception):
    """插件异常 base class"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ParseException(ResolverException):
    def __init__(self, message: str):
        super().__init__(message)


class DownloadException(ParseException):
    """下载异常"""

    def __init__(self, message: str | None = None):
        super().__init__(message or "媒体下载失败")


class IgnoreException(ParseException):
    """可忽略异常"""

    def __init__(self, message: str | None = None):
        super().__init__(message or "可忽略异常")


class TipException(ParseException):
    """提示异常"""


def handle_exception(error_message: str | None = None):
    """处理 matcher 中的异常, 并回复错误消息"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ResolverException as e:
                matcher = current_matcher.get()
                await matcher.finish(error_message or e.message)

        return wrapper

    return decorator
