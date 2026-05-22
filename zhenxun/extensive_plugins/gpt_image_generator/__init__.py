"""
GPT-Image-2 图片生成插件
命令: #gpt改图 / #GPT改图 / 大gpt / 大GPT
支持文生图和图生图, 多供应商重试链, 撤回取消
"""

import asyncio
import io
import math
import re
import time

from nonebot import get_driver, on_command, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType
from zhenxun.utils.rules import notice_rule

from .api import (
    GPTImageClient,
    ImageGenerationResult,
    download_image_bytes,
    find_provider,
)
from .config import (
    COOLDOWN_EXTRA_SECONDS,
    COOLDOWN_FAIL_SECONDS,
    DEFAULT_COUNT,
    DEFAULT_QUALITY,
    MAX_COUNT_REGULAR,
    MAX_PIXELS,
    MAX_RATIO,
    MAX_SIDE,
    MIN_PIXELS,
    PIXEL_ALIGNMENT,
    PRESET_RATIOS,
    PROVIDERS,
    QUALITY_VALUES,
    REGULAR_RETRY_CHAIN,
    SIZE_PRESETS,
    SUPERUSER_RETRY_CHAIN,
)
from .usage_tracker import add_credits, check_user_limit, record_usage

__plugin_meta__ = PluginMetadata(
    name="GPT改图",
    description="使用 GPT-Image-2 模型进行图片生成/编辑，支持多供应商自动重试",
    usage=(
        "#gpt改图 [提示词] [--size=1k|2k] [--ratio=16:9]\n"
        "#GPT改图 / 大gpt / 大GPT"
    ),
    extra=PluginExtraData(
        author="",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#gpt改图 [提示词]"),
        ],
    ).to_dict(),
)

_gpt_image = on_command(
    "#gpt改图", aliases={"#GPT改图", "大gpt", "大GPT"}, priority=5, block=True
)

# 撤回检测
_recall_listener = on_notice(
    priority=1, block=False, rule=notice_rule(GroupRecallNoticeEvent)
)

_active_requests: dict[str, asyncio.Event] = {}
_user_cooldowns: dict[str, float] = {}     # user_id -> cooldown_end_timestamp
_user_generating: dict[str, bool] = {}     # user_id -> 是否正在生成中


# ============ 工具函数 ============

def is_superuser(event: MessageEvent) -> bool:
    try:
        return str(event.user_id) in get_driver().config.superusers
    except Exception:
        return False


def check_cooldown(user_id: str) -> tuple[int, int]:
    """返回 (是否在冷却中, 剩余秒数), 同时检查生成中标志"""
    if _user_generating.get(user_id):
        return 9999, 0  # 生成中, 用大值表示
    if user_id not in _user_cooldowns:
        return 0, 0
    remaining = int(_user_cooldowns[user_id] - time.time())
    if remaining > 0:
        return remaining, remaining
    return 0, 0


def set_cooldown(user_id: str, duration: float) -> None:
    """设置冷却结束时间 (从现在起 duration 秒)"""
    _user_cooldowns[user_id] = time.time() + duration


def strip_command(text: str) -> str:
    """去除命令前缀, 返回剩余文本"""
    for prefix in ("#gpt改图", "#GPT改图", "大gpt", "大GPT"):
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    # 兜底: 尝试用正则匹配
    text = re.sub(r"^(#[gG][pP][tT]改图|大[gG][pP][tT])", "", text)
    return text.strip()


def parse_command_args(text: str) -> dict:
    """
    解析命令参数, 从前面截断, 防止从提示词中误匹配.
    支持:
      --size=1k|2k  --ratio=16:9  --count=2  --quality=high
      --provider=yunwu  -p=clawnode
      简写: 1k 2k  16:9  2 3  low medium high max
    返回 {"prompt", "size_key", "ratio_key", "count", "quality_key", "provider"}
    """
    size_key = None
    ratio_key = None
    count = None
    quality_key = None
    provider = None

    # 匹配所有 --flag=value 和 -p=value 模式 (不会误匹配提示词)
    # --provider= 或 -p= (大小写不敏感匹配 PROVIDERS)
    for pattern in [r"--provider=(\S+)", r"-p=(\S+)"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).lower()
            for p_cfg in PROVIDERS:
                if p_cfg["name"].lower() == val:
                    provider = p_cfg["name"]
                    break
            text = text.replace(m.group(0), "")

    for pattern, target_var, valid_set in [
        (r"--size=(\S+)", "size", SIZE_PRESETS),
        (r"--ratio=(\S+)", "ratio", PRESET_RATIOS),
        (r"--count=(\d+)", "count", None),
        (r"--quality=(\S+)", "quality", QUALITY_VALUES),
    ]:
        m = re.search(pattern, text)
        if m:
            val = m.group(1)
            if target_var == "size" and val in SIZE_PRESETS:
                size_key = val
            elif target_var == "ratio" and val in PRESET_RATIOS:
                ratio_key = val
            elif target_var == "count" and val.isdigit():
                count = int(val)
            elif target_var == "quality" and val in QUALITY_VALUES:
                quality_key = val
            text = text.replace(m.group(0), "")

    # 从前面逐 token 匹配简写, 第一个不匹配的 token 起全部是提示词
    tokens = text.strip().split()
    prompt_start = 0
    for i, tok in enumerate(tokens):
        if size_key is None and tok in SIZE_PRESETS:
            size_key = tok
        elif ratio_key is None and tok in PRESET_RATIOS:
            ratio_key = tok
        elif count is None and tok.isdigit():
            count = int(tok)
        elif quality_key is None and tok in QUALITY_VALUES:
            quality_key = tok
        else:
            prompt_start = i
            break
    else:
        prompt_start = len(tokens)

    prompt = " ".join(tokens[prompt_start:]).strip()
    return {
        "prompt": prompt,
        "size_key": size_key,
        "ratio_key": ratio_key,
        "count": count,
        "quality_key": quality_key,
        "provider": provider,
    }


def extract_images(event: MessageEvent) -> list[str]:
    """提取图片 URL: 回复消息中的图片在前, 当前消息中的图片在后"""
    urls = []

    if event.reply:
        for seg in event.reply.message:
            if seg.type == "image":
                url = seg.data.get("url")
                if url:
                    urls.append(url)

    for seg in event.message:
        if seg.type == "image":
            url = seg.data.get("url")
            if url:
                urls.append(url)

    return urls


def calculate_dimensions(size_key: str, ratio_key: str) -> tuple[int, int]:
    """
    根据目标分辨率和比例尺计算精确像素尺寸, 对齐到 16px.

    约束:
    - 宽高均为 16 的倍数
    - 比例 ≤ 3:1 (任意方向)
    - 总像素: 655,360 ~ 8,294,400
    - 最大边长 < 3,840px

    Raises:
        ValueError: 无法在约束内计算合法尺寸
    """
    target_pixels = SIZE_PRESETS[size_key]
    w_ratio, h_ratio = PRESET_RATIOS[ratio_key]
    ratio_float = w_ratio / h_ratio

    # width = sqrt(target * ratio), height = width / ratio
    w_raw = math.sqrt(target_pixels * ratio_float)
    h_raw = w_raw / ratio_float

    width = round(w_raw / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
    height = round(h_raw / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT

    width = max(PIXEL_ALIGNMENT, width)
    height = max(PIXEL_ALIGNMENT, height)

    # 验证约束, 不满足则微调
    for _ in range(200):
        valid = True

        if width < PIXEL_ALIGNMENT or height < PIXEL_ALIGNMENT:
            valid = False

        pixels = width * height
        if pixels < MIN_PIXELS or pixels > MAX_PIXELS:
            valid = False

        if max(width, height) >= MAX_SIDE + PIXEL_ALIGNMENT:
            valid = False

        ratio = max(width / height, height / width)
        if ratio > MAX_RATIO + 0.01:
            valid = False

        if valid:
            return width, height

        # 超出像素上限则等比例缩小, 低于下限则放大
        if pixels > MAX_PIXELS:
            scale = math.sqrt(MAX_PIXELS / pixels)
            width = round(width * scale / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
            height = round(height * scale / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
        elif pixels < MIN_PIXELS:
            scale = math.sqrt(MIN_PIXELS / pixels)
            width = round(width * scale / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
            height = round(height * scale / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
        else:
            width = round(width / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT
            height = round(height / PIXEL_ALIGNMENT) * PIXEL_ALIGNMENT

    raise ValueError(f"无法计算合法尺寸: {size_key}, {ratio_key}")


async def get_image_dimensions(url: str) -> tuple[int, int] | None:
    """下载图片并返回 (width, height)"""
    try:
        from PIL import Image

        data = await download_image_bytes(url)
        if data:
            img_bytes, _ = data
            img = Image.open(io.BytesIO(img_bytes))
            return img.size
    except Exception:
        pass
    return None


def find_closest_preset_ratio(w: int, h: int) -> str:
    """找到最接近的预设比例尺名称"""
    if w <= 0 or h <= 0:
        return "1:1"
    target = w / h
    best = "1:1"
    best_diff = float("inf")
    for key, (rw, rh) in PRESET_RATIOS.items():
        candidate = rw / rh
        diff = abs(target - candidate)
        if diff < best_diff:
            best_diff = diff
            best = key
    return best


def truncate_error(msg: str, max_len: int = 100) -> str:
    """截断过长错误消息"""
    if len(msg) > max_len:
        return msg[:max_len] + "..."
    return msg


def calculate_cost(provider: dict, result: ImageGenerationResult) -> float:
    """计算本次调用费用 (RMB), 支持按次/按token/按输入输出分离计费"""
    in_per_m = provider.get("cost_per_million_input_tokens")
    out_per_m = provider.get("cost_per_million_output_tokens")
    if in_per_m and out_per_m:
        if result.prompt_tokens > 0 or result.completion_tokens > 0:
            return (
                result.prompt_tokens / 1_000_000 * in_per_m
                + result.completion_tokens / 1_000_000 * out_per_m
            )
        # API 未返回拆分, 用 total_tokens 按输出费率计
        if result.total_tokens > 0:
            return result.total_tokens / 1_000_000 * out_per_m
        return provider.get("cost_per_call", 0.03)
    per_m = provider.get("cost_per_million_tokens")
    if per_m:
        return result.total_tokens / 1_000_000 * per_m
    return provider.get("cost_per_call", 0.03)


# ============ 撤回检测 ============

@_recall_listener.handle()
async def handle_recall(event: GroupRecallNoticeEvent):
    msg_id = str(event.message_id)
    cancel_event = _active_requests.get(msg_id)
    if cancel_event:
        cancel_event.set()
        logger.info(f"命令消息被撤回, 取消请求: {msg_id}")


# ============ 重试链执行 ============

async def execute_retry_chain(
    cancel_event: asyncio.Event,
    retry_chain: list[str],
    has_images: bool,
    image_datas: list[tuple[bytes, str]] | None,
    prompt: str,
    size_str: str,
    count: int = 1,
    quality: str = "medium",
    needs_custom_size: bool = False,
) -> tuple[ImageGenerationResult, str, list[str]]:
    """
    遍历重试链调用提供商, 循环 count 次 (API 固定 n=1)。
    needs_custom_size 时自动跳过 size_faithful=False 的供应商。
    成功时返回 (result, provider_name, fallback_errors)。
    失败抛 RuntimeError。
    被取消抛 asyncio.CancelledError。
    """
    all_images = []
    all_tokens = 0
    all_prompt_tokens = 0
    all_completion_tokens = 0
    final_provider = ""
    fallback_errors = []

    for _ in range(count):
        if cancel_event.is_set():
            raise asyncio.CancelledError()

        async def run_chain():
            errors = []
            for provider_name in retry_chain:
                if cancel_event.is_set():
                    raise asyncio.CancelledError()
                provider_cfg = find_provider(provider_name)
                if not provider_cfg:
                    errors.append(f"{provider_name}: 未找到配置")
                    continue
                # 需要自定义尺寸但不忠实的供应商自动跳过
                if needs_custom_size and not provider_cfg.get("size_faithful", True):
                    errors.append(f"{provider_name}: 不支持自定义分辨率, 已自动切换")
                    logger.info(f"跳过 {provider_name}: 不支持自定义分辨率")
                    continue
                client = GPTImageClient(provider_cfg)
                p_start = time.time()
                try:
                    if has_images and image_datas:
                        result = await client.img2img(
                            prompt=prompt, image_datas=image_datas,
                            size=size_str, quality=quality, n=1,
                        )
                    else:
                        result = await client.txt2img(
                            prompt=prompt, size=size_str,
                            quality=quality, n=1,
                        )
                    return result, provider_name, errors
                except Exception as e:
                    p_dur = time.time() - p_start
                    err_str = truncate_error(str(e), 100)
                    errors.append(f"{provider_name}({p_dur:.0f}s): {err_str}")
                    logger.warning(
                        f"供应商 {provider_name} 失败(耗时{p_dur:.0f}s): {err_str}"
                    )
            raise RuntimeError("所有供应商均失败: " + "; ".join(errors))

        chain_task = asyncio.ensure_future(run_chain())
        cancel_task = asyncio.ensure_future(cancel_event.wait())

        done, pending = await asyncio.wait(
            [chain_task, cancel_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if cancel_task in done:
            if chain_task.done() and not chain_task.cancelled():
                exc = chain_task.exception()
                if exc is None:
                    cancel_task.cancel()
                    result, provider_name, errors = chain_task.result()
                    all_images.extend(result.images)
                    all_tokens += result.total_tokens
                    all_prompt_tokens += result.prompt_tokens
                    all_completion_tokens += result.completion_tokens
                    final_provider = provider_name
                    fallback_errors = errors
                    continue
            if not chain_task.done():
                chain_task.cancel()
            raise asyncio.CancelledError()

        cancel_task.cancel()
        exc = chain_task.exception()
        if exc is not None:
            raise exc
        result, provider_name, errors = chain_task.result()
        all_images.extend(result.images)
        all_tokens += result.total_tokens
        all_prompt_tokens += result.prompt_tokens
        all_completion_tokens += result.completion_tokens
        final_provider = provider_name
        if errors:
            fallback_errors = errors

    return (
        ImageGenerationResult(
            images=all_images,
            total_tokens=all_tokens,
            prompt_tokens=all_prompt_tokens,
            completion_tokens=all_completion_tokens,
        ),
        final_provider,
        fallback_errors,
    )


# ============ 主处理器 ============

@_gpt_image.handle()
async def handle_gpt_image(bot: Bot, event: MessageEvent):
    user_id = str(event.user_id)
    group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None
    is_su = is_superuser(event)

    # Step 0: 管理员添加次数命令
    raw_text = event.get_message().extract_plain_text().strip()
    remaining_text = strip_command(raw_text)
    credits_match = re.match(r"^添加次数\s+(\d{5,})\s*$", remaining_text)
    if credits_match:
        target_qq = credits_match.group(1)
        if is_su:
            new_balance = add_credits(target_qq, 1)
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(
                        f"已为 {target_qq} 添加 1 次，当前永久次数余额 {new_balance}"
                    )
                )
            )
        else:
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text("权限不足")
                )
            )
        return

    # Step 1: 回应表情
    try:
        await bot.call_api(
            "set_msg_emoji_like", message_id=event.message_id, emoji_id="282"
        )
    except Exception:
        pass

    # Step 2: 检查冷却/生成中状态 (普通用户)
    if not is_su:
        on_cd, remaining = check_cooldown(user_id)
        if _user_generating.get(user_id):
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(
                        "你的上一张图还在生成中，请等待完成后再次使用~"
                    )
                )
            )
            return
        if on_cd:
            minutes = remaining // 60
            seconds = remaining % 60
            if minutes > 0:
                cd_msg = f"冷却中，请等待 {minutes}分{seconds}秒 后再试"
            else:
                cd_msg = f"冷却中，请等待 {seconds}秒 后再试"
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(cd_msg)
                )
            )
            return

    # Step 3: 解析命令参数
    parsed = parse_command_args(remaining_text)
    prompt = parsed["prompt"]
    size_key = parsed["size_key"] or "1k"
    ratio_key = parsed["ratio_key"]
    count = parsed["count"] or DEFAULT_COUNT
    quality = parsed["quality_key"] or DEFAULT_QUALITY

    # Step 4: 普通用户校验
    if not is_su:
        if count > MAX_COUNT_REGULAR:
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(f"单次最多生成 {MAX_COUNT_REGULAR} 张")
                )
            )
            return
        limit_info = check_user_limit(user_id, group_id)
        if limit_info["total_available"] < count:
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(
                        f"今日剩余免费 {limit_info['free_remaining']} 次 + "
                        f"永久次数 {limit_info['permanent_credits']} 次，"
                        f"共 {limit_info['total_available']} 次，无法生成 {count} 张"
                    )
                )
            )
            return
    # Step 6: 提取图片
    image_urls = extract_images(event)

    # Step 7: 确定比例尺
    if not ratio_key and image_urls:
        dims = await get_image_dimensions(image_urls[0])
        if dims:
            ratio_key = find_closest_preset_ratio(*dims)
    if not ratio_key:
        ratio_key = "1:1"

    # Step 8: 计算尺寸
    try:
        width, height = calculate_dimensions(size_key, ratio_key)
    except ValueError as e:
        await _gpt_image.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"参数错误: {e}")
            )
        )
        return
    size_str = f"{width}x{height}"

    # Step 9: 判断 endpoint / 下载图片
    has_images = bool(image_urls)
    image_datas = None
    if has_images:
        image_datas = []
        for url in image_urls[:5]:
            data = await download_image_bytes(url)
            if data:
                image_datas.append(data)
        if not image_datas:
            if not prompt:
                await _gpt_image.finish(
                    Message(
                        MessageSegment.reply(event.message_id)
                        + MessageSegment.text("无法下载图片，且未提供提示词")
                    )
                )
                return
            has_images = False

    # 无图无提示词
    if not has_images and not prompt:
        await _gpt_image.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请输入图片描述或回复/发送图片")
            )
        )
        return

    # 普通用户在真正开始生成前二次检查并加锁，避免并发调用生成 API。
    if not is_su:
        if _user_generating.get(user_id):
            await _gpt_image.finish(
                Message(
                    MessageSegment.reply(event.message_id)
                    + MessageSegment.text(
                        "你的上一张图还在生成中，请等待完成后再次使用~"
                    )
                )
            )
            return
        _user_generating[user_id] = True

    # Step 10: 注册撤回检测
    cancel_event = asyncio.Event()
    msg_id_str = str(event.message_id)
    _active_requests[msg_id_str] = cancel_event

    start_time = time.time()

    provider_override = parsed.get("provider")
    if provider_override:
        retry_chain = [provider_override]
    else:
        retry_chain = SUPERUSER_RETRY_CHAIN if is_su else REGULAR_RETRY_CHAIN

    # 需要自定义分辨率 (非默认尺寸 或 图生图)
    needs_custom_size = (size_key != "1k" or ratio_key != "1:1" or has_images)

    success = False
    try:
        result, provider_name, fallback_errors = await execute_retry_chain(
            cancel_event=cancel_event,
            retry_chain=retry_chain,
            has_images=has_images,
            image_datas=image_datas,
            prompt=prompt,
            size_str=size_str,
            count=count,
            quality=quality,
            needs_custom_size=needs_custom_size,
        )
        success = True
    except asyncio.CancelledError:
        await _gpt_image.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("生图被取消")
            )
        )
        return
    except RuntimeError as e:
        logger.exception(f"GPT改图失败: {e}")
        err_str = str(e)
        await _gpt_image.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text(f"生成失败: {truncate_error(err_str, 100)}")
            )
        )
        return
    finally:
        _active_requests.pop(msg_id_str, None)
        if not is_su:
            _user_generating.pop(user_id, None)
            if success:
                set_cooldown(user_id, COOLDOWN_EXTRA_SECONDS)
            else:
                set_cooldown(user_id, COOLDOWN_FAIL_SECONDS)

    # Step 11: 记录用量和费用
    total_duration = time.time() - start_time
    provider_cfg = find_provider(provider_name) or {}
    cost = calculate_cost(provider_cfg, result)

    # 只有成功才计入次数 (count 张算 count 次)
    usage_stats = record_usage(
        user_id, group_id, cost * count, is_superuser=is_su, count=count
    )

    # Step 12: 构建回复
    msg = Message()
    msg += MessageSegment.reply(event.message_id)

    for img in result.images:
        msg += MessageSegment.image(img)

    # 统计信息
    stats = f"\n---\n{width}x{height} | {ratio_key} | {size_key} | {quality}"
    if count > 1:
        stats += f" | ×{count}"
    stats += f" | 耗时 {total_duration:.1f}s"
    if result.total_tokens > 0:
        stats += f" | {result.total_tokens} tokens"

    total_cost = cost * count
    stats += f"\n本次 {total_cost:.4f}￥ ({cost:.4f}×{count}, 供应商: {provider_name})"

    if is_su:
        stats += (
            f"\n[SU] 累计: {usage_stats['user_total_count']}次 / "
            f"{usage_stats['user_total_cost']:.2f}￥"
        )
    else:
        stats += (
            f"\n个人累计: {usage_stats['user_total_count']}次 / "
            f"{usage_stats['user_total_cost']:.2f}￥"
        )
        if group_id:
            stats += (
                f"\n群累计: {usage_stats['group_total_count']}次 / "
                f"{usage_stats['group_total_cost']:.2f}￥"
            )
        # 显示额度信息
        daily_limit = usage_stats["daily_limit"]
        free_used = usage_stats["user_daily_count"]
        perm_credits = usage_stats["permanent_credits"]
        stats += f"\n今日免费: {free_used}/{daily_limit} | 永久次数: {perm_credits}"
        if usage_stats["used_permanent"] > 0:
            stats += f" (本次使用 {usage_stats['used_permanent']} 次永久额度)"
        stats += f"\n冷却: {COOLDOWN_EXTRA_SECONDS}s"

    # 回退警告
    if fallback_errors:
        stats += "\n警告: 原供应商失败，已自动切换\n"
        stats += "\n".join(fallback_errors[:2])

    msg += MessageSegment.text(stats)
    await _gpt_image.finish(msg)
