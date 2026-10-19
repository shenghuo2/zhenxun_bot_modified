from typing import TypeVar

from nonebot import get_driver, logger, on_command
from nonebot.adapters import Message
from nonebot.exception import ActionFailed
from nonebot.params import CommandArg

from ..config import pconfig
from ..exception import DownloadException, IgnoreException, ParseException
from ..helper import UniHelper, UniMessage, Voice
from ..parsers import BaseParser, BilibiliParser, ParseResult
from ..renders import get_renderer
from ..utils import LimitedSizeDict
from .rule import SUPER_PRIVATE, Searched, SearchResult, on_keyword_regex

# bilibili 由本地定制的 matchers/bilibili.py 处理(含 #视频下载 等增强功能),
# 因此从统一解析 matcher 中排除, 避免重复匹配
_EXCLUDED_PLATFORMS = {"bilibili"}


def _get_enabled_parser_classes() -> list[type[BaseParser]]:
    disabled_platforms = set(pconfig.disabled_platforms) | _EXCLUDED_PLATFORMS
    all_subclass = BaseParser.get_all_subclass()
    return [_cls for _cls in all_subclass if _cls.platform.name not in disabled_platforms]


# 关键词 -> Parser 映射
KEYWORD_PARSER_MAP: dict[str, BaseParser] = {}
T = TypeVar("T", bound=BaseParser)


def get_parser(keyword: str) -> BaseParser:
    return KEYWORD_PARSER_MAP[keyword]


def get_parser_by_type(parser_type: type[T]) -> T:
    for parser in KEYWORD_PARSER_MAP.values():
        if isinstance(parser, parser_type):
            return parser
    raise ValueError(f"未找到类型为 {parser_type} 的 parser 实例")


@get_driver().on_startup
def register_parser_matcher():
    enabled_classes = _get_enabled_parser_classes()

    enabled_platforms = []
    for _cls in enabled_classes:
        parser = _cls()
        enabled_platforms.append(parser.platform.display_name)
        for keyword, _ in _cls._key_patterns:
            KEYWORD_PARSER_MAP[keyword] = parser
    logger.info(f"启用平台: {', '.join(sorted(enabled_platforms))}")

    patterns = [p for _cls in enabled_classes for p in _cls._key_patterns]
    matcher = on_keyword_regex(*patterns)
    matcher.append_handler(parser_handler)


# 缓存结果
_RESULT_CACHE = LimitedSizeDict[str, ParseResult](max_size=50)


def clear_result_cache():
    _RESULT_CACHE.clear()


@UniHelper.with_reaction
async def parser_handler(
    sr: SearchResult = Searched(),
):
    """统一的解析处理器"""
    try:
        # 1. 获取缓存结果
        cache_key = sr.searched.group(0)
        result = _RESULT_CACHE.get(cache_key)

        if result is None:
            # 2. 获取对应平台 parser
            parser = get_parser(sr.keyword)
            result = await parser.parse(sr.keyword, sr.searched)
            logger.debug(f"解析结果: {result}")
        else:
            logger.debug(f"命中缓存: {cache_key}, 结果: {result}")

        # 3. 渲染内容消息并发送
        renderer = get_renderer(result.platform.name)(result)
        voice_failed = False
        async for message in renderer.render_messages():
            try:
                await message.send()
            except ActionFailed as e:
                if not any(isinstance(segment, Voice) for segment in message):
                    raise
                voice_failed = True
                logger.warning(
                    f"{result.platform.display_name}语音发送失败，继续发送其余内容: {e}"
                )

        if voice_failed:
            await UniMessage("语音发送失败，已跳过").send()

        # 4. 缓存解析结果
        _RESULT_CACHE[cache_key] = result
    except IgnoreException:
        # 可忽略异常(如超过大小/时长限制), 静默处理
        return
    except (ParseException, DownloadException) as e:
        # 解析失败, 优雅提示, 避免输出完整 ERROR traceback
        await UniMessage(e.message).send()


from ..download import yt_dlp_downloader

if yt_dlp_downloader is not None:
    from ..parsers import YouTubeParser

    @on_command("ym", priority=3, block=True).handle()
    @UniHelper.with_reaction
    async def _(message: Message = CommandArg()):
        text = message.extract_plain_text()
        parser = get_parser_by_type(YouTubeParser)
        _, matched = parser.search_url(text)
        if not matched:
            await UniMessage("请发送正确的油管链接").finish()

        url = matched.group(0)

        audio_path = await yt_dlp_downloader.download_audio(url)
        await UniMessage(UniHelper.record_seg(audio_path)).send()

        if pconfig.need_upload:
            await UniMessage(UniHelper.file_seg(audio_path)).send()


@on_command("blogin", block=True, permission=SUPER_PRIVATE).handle()
async def _():
    parser = get_parser_by_type(BilibiliParser)
    qrcode = await parser.login_with_qrcode()
    await UniMessage(UniHelper.img_seg(qrcode)).send()
    async for msg in parser.check_qr_state():
        await UniMessage(msg).send()


# 注册本地定制 B 站 matcher(含 #视频下载 / bm 命令)
from .bilibili import bilibili as _bilibili_matcher  # noqa: F401
