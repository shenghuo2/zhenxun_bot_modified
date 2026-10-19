import asyncio
import json
from pathlib import Path
import re
from typing import Any

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.message import event_preprocessor
from nonebot.params import CommandArg

from ..config import pconfig
from ..download import downloader
from ..exception import DownloadException, ParseException, handle_exception
from ..parsers.base import BaseParser
from ..parsers.bilibili_video import BilibiliVideoParser
from ..utils import encode_video_to_h264, keep_zh_en_num, merge_av
from .filter import is_enabled
from .obhelper import obhelper
from .rule import Searched, SearchResult, on_keyword_regex

parser = BilibiliVideoParser()

VIDEO_DOWNLOAD_COMMAND_RE = re.compile(r"^(?:#视频下载|#下载)(?:\s+(?P<arg>.+))?$")

_URL_KEY_MAPPING = {
    "detail_1": "qqdocurl",
    "news": "jumpUrl",
    "music": "jumpUrl",
}


def _extract_json_url(json_seg: MessageSegment) -> str | None:
    """处理 OneBot JSON 类型的消息段，提取 URL"""
    data_str: str | None = json_seg.data.get("data")
    if not data_str:
        return None

    data_str = data_str.replace("&#44;", ",")

    try:
        data: dict[str, Any] = json.loads(data_str)
    except json.JSONDecodeError:
        logger.exception("json 卡片解析失败")
        return None

    meta: dict[str, Any] | None = data.get("meta")
    if not meta:
        return None

    for key1, key2 in _URL_KEY_MAPPING.items():
        if item := meta.get(key1):
            if url := item.get(key2):
                return url.replace("&amp;", "&")
    return None


@event_preprocessor
async def _normalize_reply_download_command(event: MessageEvent):
    if not event.reply or not VIDEO_DOWNLOAD_COMMAND_RE.match(event.message.extract_plain_text().strip()):
        return

    text_segments = [seg for seg in event.message if seg.is_text()]
    non_text_segments = [seg for seg in event.message if not seg.is_text()]
    if not text_segments:
        return
    event.message = Message(text_segments + non_text_segments)
    event.raw_message = str(event.message)


video_download = on_command("#视频下载", aliases={"#下载"}, priority=5, block=True, rule=is_enabled)

_bilibili_patterns: list[tuple[str, str]] = [
    ("bilibili", r"https?://(?:space|www|live|m|t)?\.?bilibili\.com/[A-Za-z\d\._?%&+\-=/#]+()()"),
    ("bili2233", r"https?://bili2233\.cn/[A-Za-z\d\._?%&+\-=/#]+()()"),
    ("b23", r"https?://b23\.tv/[A-Za-z\d\._?%&+\-=/#]+()()"),
]
if pconfig.bili_video_parse_enabled:
    _bilibili_patterns.extend(
        [
            ("BV", r"(BV[1-9a-zA-Z]{10})(?:\s)?(\d{1,3})?"),
            ("av", r"av(\d{6,})(?:\s)?(\d{1,3})?"),
        ]
    )

bilibili = on_keyword_regex(*_bilibili_patterns)


def _reply_to_command(event: MessageEvent, content: MessageSegment | str) -> Message:
    if isinstance(content, str):
        content = MessageSegment.text(content)
    return Message(MessageSegment.reply(event.message_id) + content)


def _get_reply_message_id(event: MessageEvent) -> int | str | None:
    for seg in event.message:
        if seg.type != "reply":
            continue
        reply_id = seg.data.get("id")
        if isinstance(reply_id, str) and reply_id.isdigit():
            return int(reply_id)
        return reply_id
    return None


def _normalize_onebot_message(raw_message: Any) -> Message:
    if isinstance(raw_message, Message):
        return raw_message
    if isinstance(raw_message, list):
        message = Message()
        for item in raw_message:
            if isinstance(item, MessageSegment):
                message += item
                continue
            if not isinstance(item, dict):
                continue
            seg_type = item.get("type")
            seg_data = item.get("data", {})
            if isinstance(seg_type, str) and isinstance(seg_data, dict):
                message += MessageSegment(type=seg_type, data=seg_data)
        return message
    return Message(str(raw_message))


async def _fetch_reply_message(bot: Bot, event: MessageEvent) -> Message | None:
    if event.reply:
        return event.reply.message

    reply_id = _get_reply_message_id(event)
    if reply_id is None:
        return None

    try:
        msg_info = await bot.get_msg(message_id=reply_id)
    except Exception as e:
        logger.warning(f"获取回复消息失败 message_id={reply_id}: {e}")
        return None

    raw_message = msg_info.get("message") or msg_info.get("raw_message", "")
    return _normalize_onebot_message(raw_message)


def _extract_text_and_json_urls(message: Message) -> str:
    texts: list[str] = []
    if text := message.extract_plain_text().strip():
        texts.append(text)
    for seg in message:
        if seg.type == "json" and (url := _extract_json_url(seg)):
            texts.append(url)
    return "\n".join(texts)


def _extract_video_download_arg(event: MessageEvent) -> str:
    text = event.message.extract_plain_text().strip()
    matched = VIDEO_DOWNLOAD_COMMAND_RE.match(text)
    if not matched:
        return ""
    return (matched.group("arg") or "").strip()


def _extract_page_num(source: str, fallback: str | None = None) -> int:
    if matched := re.search(r"(?:&|\?)p=(\d{1,3})", source):
        return int(matched.group(1))
    return int(fallback) if fallback else 1


def _format_duration(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    if seconds:
        return f"{minutes} 分 {seconds} 秒"
    return f"{minutes} 分钟"


async def _extract_bilibili_video_target(source: str) -> tuple[dict[str, int | str], str, int] | None:
    url_pattern = re.compile(
        r"https?://(?:(?:space|www|live|m|t)\.)?bilibili\.com/[A-Za-z\d\._?%&+\-=/#]+"
        r"|https?://(?:bili2233\.cn|b23\.tv)/[A-Za-z\d\._?%&+\-=/#]+",
        re.IGNORECASE,
    )
    if matched_url := url_pattern.search(source):
        url = matched_url.group(0)
        if "b23.tv" in url or "bili2233.cn" in url:
            redirected = await BaseParser.get_redirect_url(url, parser.headers)
            if redirected != url:
                url = redirected
        source = url

    if matched := re.search(r"(BV[1-9a-zA-Z]{10})(?:\s)?(\d{1,3})?", source):
        bvid = matched.group(1)
        return {"bvid": bvid}, bvid, _extract_page_num(source, matched.group(2))

    if matched := re.search(r"(?:^|(?<![A-Za-z0-9]))av(\d{6,})(?:\s)?(\d{1,3})?", source, re.IGNORECASE):
        avid = int(matched.group(1))
        return {"avid": avid}, f"av{avid}", _extract_page_num(source, matched.group(2))

    return None


async def _download_first_available(urls: list[str], *, file_name: str) -> Path:
    last_error: DownloadException | None = None
    for index, url in enumerate(urls, start=1):
        try:
            return await downloader.download_video(url, video_name=file_name, ext_headers=parser.headers)
        except DownloadException as e:
            last_error = e
            logger.warning(f"B站媒体候选地址下载失败 {index}/{len(urls)}: {url}")
    raise last_error or DownloadException("媒体下载失败")


async def _download_bilibili_video(id_arg: dict[str, int | str], video_id: str, page_num: int):
    video_info = await parser.parse_video_info(**id_arg, page_num=page_num)
    if video_info.video_duration > pconfig.duration_maximum:
        raise ParseException(
            f"当前视频时长 {_format_duration(video_info.video_duration)}，"
            f"超过管理员设置的最长时间 {_format_duration(pconfig.duration_maximum)}"
        )

    file_name = f"{video_id}-{page_num}"
    video_path = pconfig.cache_dir / f"{file_name}.mp4"
    if video_path.exists():
        return video_info, video_path

    video_urls = video_info.video_urls or [video_info.video_url]
    audio_urls = video_info.audio_urls or ([video_info.audio_url] if video_info.audio_url else [])
    if audio_urls:
        v_path = await _download_first_available(video_urls, file_name=f"{file_name}-video.m4s")
        a_path = await _download_first_available(audio_urls, file_name=f"{file_name}-audio.m4s")
        await merge_av(v_path=v_path, a_path=a_path, output_path=video_path)
    else:
        video_path = await _download_first_available(video_urls, file_name=f"{file_name}.mp4")
    return video_info, video_path


async def _send_video(matcher, video_path: Path) -> None:
    try:
        await matcher.send(obhelper.video_seg(video_path))
    except ActionFailed as e:
        message: str = e.info.get("message", "")
        if not message.endswith(".png'"):
            raise
        logger.warning("视频上传出现无缩略图错误，将重新编码为 h264 进行上传")
        h264_video_path = await encode_video_to_h264(video_path)
        await matcher.send(obhelper.video_seg(h264_video_path))


async def _try_set_msg_emoji_like(bot: Bot, event: MessageEvent) -> None:
    try:
        await bot.call_api("set_msg_emoji_like", message_id=event.message_id, emoji_id="282")
    except Exception:
        pass


async def _download_imgs_without_raise(urls: list[str]) -> list[Path]:
    results = await asyncio.gather(
        *(downloader.download_img(url, ext_headers=parser.headers) for url in urls),
        return_exceptions=True,
    )
    return [r for r in results if isinstance(r, Path)]


@bilibili.handle()
@handle_exception()
async def _(event: MessageEvent, sr: SearchResult = Searched()):
    pub_prefix = f"{pconfig.nickname}解析 | 哔哩哔哩 - "
    keyword = sr.keyword
    url, video_id, page_num = str(sr.searched.group(0)), sr.searched.group(1), sr.searched.group(2)
    # 是否附加链接
    need_join_link = keyword != "bilibili"
    # 短链重定向地址
    if keyword in ("b23", "bili2233"):
        b23url = url
        url = await BaseParser.get_redirect_url(url, parser.headers)
        if url == b23url:
            logger.warning(f"链接 {url} 无效，忽略")
            return

    # 链接中是否包含BV，av号
    if id_type := next((i for i in ("/BV", "/av") if i in url), None):
        patterns = {
            "/BV": re.compile(r"/(BV[1-9a-zA-Z]{10})()"),
            "/av": re.compile(r"/av(\d{6,})()"),
        }
        if matched := patterns[id_type].search(url):
            keyword = id_type
            video_id = str(matched.group(1))

    # B站自动解析开关: 关闭时全部交给 parse_bilibili 插件处理(默认关闭)
    if not pconfig.bili_video_parse_enabled:
        logger.debug(f"B站视频解析已关闭，忽略链接: {url}")
        bilibili.skip()

    # 处理非视频链接
    if not video_id:
        await handle_others(url)
        await bilibili.finish()

    join_link = ""
    if need_join_link:
        url_id = f"av{video_id}" if keyword in ("av", "/av") else video_id
        join_link = f" https://www.bilibili.com/video/{url_id}"
    await bilibili.send(f"{pub_prefix}视频{join_link}")
    # 获取分集数
    page_num = int(page_num) if page_num else 1
    if url and (matched := re.search(r"(?:&|\?)p=(\d{1,3})", url)):
        page_num = int(matched.group(1))
    # 视频
    id_arg: dict[str, int | str] = {}
    if keyword in ("av", "/av"):
        id_arg["avid"] = int(video_id)
    else:
        id_arg["bvid"] = video_id
    video_info = await parser.parse_video_info(**id_arg, page_num=page_num)

    segs: list[MessageSegment | str] = [
        video_info.title,
        obhelper.img_seg(await downloader.download_img(video_info.cover_url, ext_headers=parser.headers)),
        video_info.display_info,
        video_info.ai_summary,
    ]
    if video_info.video_duration > pconfig.duration_maximum:
        segs.append(
            f"⚠️ 当前视频时长 {_format_duration(video_info.video_duration)}, "
            f"超过管理员设置的最长时间 {_format_duration(pconfig.duration_maximum)}!"
        )
    await obhelper.send_segments(segs)

    if video_info.video_duration > pconfig.duration_maximum:
        logger.warning(f"video duration > {pconfig.duration_maximum}, ignore download")
        return
    _, video_path = await _download_bilibili_video(id_arg, video_id, page_num)
    await _send_video(bilibili, video_path)


# 处理 非视频
async def handle_others(url: str):
    pub_prefix = f"{pconfig.nickname}解析 | 哔哩哔哩 - "
    segs: list[MessageSegment | Message | str] = []
    # 动态
    if "t.bilibili.com" in url or "/opus" in url:
        matched = re.search(r"/(\d+)", url)
        if not matched:
            logger.warning(f"链接 {url} 无效 - 没有获取到动态 id, 忽略")
            return
        opus_id = int(matched.group(1))
        img_lst, text = await parser.parse_opus(opus_id)
        await bilibili.send(f"{pub_prefix}动态")
        segs.append(text)
        if img_lst:
            paths = await _download_imgs_without_raise(img_lst)
            segs.extend(obhelper.img_seg(path) for path in paths)
        await obhelper.send_segments(segs)
    # 直播间解析
    elif "/live" in url:
        # https://live.bilibili.com/30528999?hotRank=0
        matched = re.search(r"/(\d+)", url)
        if not matched:
            logger.warning(f"链接 {url} 无效 - 没有获取到直播间 id, 忽略")
            return
        room_id = int(matched.group(1))
        title, cover, keyframe = await parser.parse_live(room_id)
        if not title:
            await bilibili.finish(f"{pub_prefix}直播 - 未找到直播间信息")
        res = f"{pub_prefix}直播 {title}"
        res += obhelper.img_seg(await downloader.download_img(cover, ext_headers=parser.headers)) if cover else ""
        res += obhelper.img_seg(await downloader.download_img(keyframe, ext_headers=parser.headers)) if keyframe else ""
    # 专栏解析
    elif "/read" in url:
        matched = re.search(r"read/cv(\d+)", url)
        if not matched:
            logger.warning(f"链接 {url} 无效 - 没有获取到专栏 id, 忽略")
            return
        read_id = int(matched.group(1))
        texts, urls = await parser.parse_read(read_id)
        await bilibili.send(f"{pub_prefix}专栏")
        # 并发下载
        paths = await _download_imgs_without_raise(urls)
        # 反转路径列表，pop 时，则为原始顺序
        paths.reverse()
        for text in texts:
            if text:
                segs.append(text)
            else:
                segs.append(obhelper.img_seg(paths.pop()))
        if segs:
            await obhelper.send_segments(segs)
    # 收藏夹解析
    elif "/favlist" in url:
        # https://space.bilibili.com/22990202/favlist?fid=2344812202
        matched = re.search(r"favlist\?fid=(\d+)", url)
        if not matched:
            logger.warning(f"链接 {url} 无效 - 没有获取到收藏夹 id, 忽略")
            return
        fav_id = int(matched.group(1))
        # 获取收藏夹内容，并下载封面
        texts, urls = await parser.parse_favlist(fav_id)
        await bilibili.send(f"{pub_prefix}收藏夹\n正在为你找出相关链接请稍等...")
        paths: list[Path] = await _download_imgs_without_raise(urls)
        # 组合 text 和 image
        for path, text in zip(paths, texts):
            segs.append(obhelper.img_seg(path) + text)
        assert len(segs) > 0
        await obhelper.send_segments(segs)
    else:
        logger.warning(f"不支持的链接: {url}")


@video_download.handle()
@handle_exception()
async def _(bot: Bot, event: MessageEvent):
    source = _extract_video_download_arg(event)
    if not source:
        reply_message = await _fetch_reply_message(bot, event)
        if reply_message is None:
            await video_download.finish(_reply_to_command(event, "请回复一条 B 站视频消息，或在命令后直接附上视频链接"))
        source = _extract_text_and_json_urls(reply_message)

    target = await _extract_bilibili_video_target(source)
    if target is None:
        await video_download.finish(_reply_to_command(event, "没有找到可下载的 B 站视频链接"))

    id_arg, video_id, page_num = target
    await _try_set_msg_emoji_like(bot, event)
    video_info, video_path = await _download_bilibili_video(id_arg, video_id, page_num)
    logger.info(f"手动下载 B 站视频: {video_info.title} {video_id} p={page_num}")
    await _send_video(video_download, video_path)


bili_music = on_command(cmd="bm", block=True, rule=is_enabled)


@bili_music.handle()
@handle_exception()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    matched = re.match(r"^(BV[1-9a-zA-Z]{10})(?:\s)?(\d{1,3})?$", text)
    if not matched:
        await bili_music.finish("命令格式: bm BV1LpD3YsETa [集数](中括号表示可选)")

    # 回应用户
    await _try_set_msg_emoji_like(bot, event)
    bvid, p_num = str(matched.group(1)), matched.group(2)

    # 处理分 p
    p_num = int(p_num) if p_num else 1
    video_info = await parser.parse_video_info(bvid=bvid, page_num=p_num)
    if not video_info.audio_url:
        raise ParseException("没有可供下载的音频流")
    # 音频文件名
    video_title = keep_zh_en_num(video_info.title)
    audio_name = f"{video_title}.mp3"
    audio_path = pconfig.cache_dir / audio_name
    # 下载
    if not audio_path.exists():
        await downloader.download_audio(video_info.audio_url, audio_name=audio_name, ext_headers=parser.headers)

    # 发送音频
    await bili_music.send(obhelper.record_seg(audio_path))
    # 上传音频
    if pconfig.need_upload:
        await bili_music.send(obhelper.file_seg(audio_path))
