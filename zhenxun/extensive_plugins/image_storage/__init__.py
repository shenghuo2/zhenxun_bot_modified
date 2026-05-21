"""
图片存储插件
命令:
- #存图 nai - 存储NAI图片（需要有Description字段）
- #存图 灵感 / #灵感 - 存储灵感图片
- #存图 默认 / #改图 - 默认存储
- #查ver / #读ver / 查询图片version - 查看图片的Source信息
- #解析 - 查看图片的prompt信息
- #存图数量 / 存图统计 - 查看各类别已存数量
- #存图 查重 - 检查图片是否已存储（MD5查重）

注意: 存图功能仅限superuser使用
"""

import hashlib
import io
import json
from pathlib import Path

import httpx
import numpy as np
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from PIL import Image

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.utils.enum import PluginType

from .nai_extractor import extract_image_metadata

__plugin_meta__ = PluginMetadata(
    name="图片存储",
    description="存储图片到不同分类文件夹，支持NAI元数据检测",
    usage="#存图 nai/灵感/默认，#改图，#灵感，#查ver，#解析，#存图数量，#存图 查重（存图仅superuser）",
    extra=PluginExtraData(
        author="",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        commands=[
            Command(command="#存图 nai"),
            Command(command="#存图 灵感"),
            Command(command="#灵感"),
            Command(command="#存图 默认"),
            Command(command="#改图"),
            Command(command="#查ver"),
            Command(command="#读ver"),
            Command(command="查询图片version"),
            Command(command="#解析"),
            Command(command="#存图数量"),
            Command(command="存图统计"),
            Command(command="#存图 查重"),
        ],
    ).to_dict(),
)

# 存储根目录
STORAGE_ROOT = Path(__file__).parent / "saved_images"
STORAGE_DIRS = {
    "nai": STORAGE_ROOT / "nai",
    "灵感": STORAGE_ROOT / "inspiration",
    "默认": STORAGE_ROOT / "default",
}

# MD5哈希索引文件
HASH_INDEX_FILE = STORAGE_ROOT / "hash_index.json"

# 确保目录存在
for dir_path in STORAGE_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)


_save_image = on_command("#存图", priority=5, block=True)
_save_image_alias = on_command("#改图", priority=5, block=True)
_save_inspiration = on_command("#灵感", priority=5, block=True)
_view_tag = on_command(
    "#查ver", aliases={"#读ver", "查询图片version"}, priority=5, block=True
)
_parse_prompt = on_command("#解析", priority=5, block=True)
_image_count = on_command("#存图数量", aliases={"存图统计"}, priority=5, block=True)


async def is_superuser(event: MessageEvent) -> bool:
    """检查是否为 superuser"""
    from nonebot import get_driver

    return str(event.user_id) in get_driver().config.superusers


async def download_image(url: str) -> bytes | None:
    """下载图片"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.error(f"下载图片失败: {e}")
    return None


async def extract_images_from_event(event: MessageEvent) -> list[str]:
    """从消息事件中提取图片URL"""
    image_urls = []

    # 从回复消息中提取
    if event.reply:
        for seg in event.reply.message:
            if seg.type == "image":
                url = seg.data.get("url")
                if url:
                    image_urls.append(url)

    # 从当前消息中提取
    for seg in event.message:
        if seg.type == "image":
            url = seg.data.get("url")
            if url:
                image_urls.append(url)

    return image_urls


def get_image_hash(data: bytes) -> str:
    """计算图片MD5哈希"""
    return hashlib.md5(data).hexdigest()


def load_hash_index() -> dict:
    """加载MD5哈希索引"""
    if HASH_INDEX_FILE.exists():
        try:
            with open(HASH_INDEX_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载哈希索引失败: {e}")
    return {}


def save_hash_index(index: dict):
    """保存MD5哈希索引"""
    try:
        with open(HASH_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存哈希索引失败: {e}")


def add_hash_to_index(img_hash: str, category: str, filename: str):
    """添加哈希到索引"""
    index = load_hash_index()
    if img_hash not in index:
        index[img_hash] = []

    entry = {"category": category, "filename": filename}
    if entry not in index[img_hash]:
        index[img_hash].append(entry)

    save_hash_index(index)


def check_hash_in_index(img_hash: str) -> list:
    """检查哈希是否在索引中，返回所在分类列表"""
    index = load_hash_index()
    if img_hash in index:
        return [entry["category"] for entry in index[img_hash]]
    return []


def count_images_in_dir(dir_path: Path) -> int:
    """统计目录中的图片数量"""
    if not dir_path.exists():
        return 0
    extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    return sum(1 for f in dir_path.iterdir() if f.suffix.lower() in extensions)


async def _do_save_image(bot: Bot, event: MessageEvent, category: str):
    """存储图片核心逻辑"""
    # 检查superuser权限
    if not await is_superuser(event):
        return Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("存图功能仅限管理员使用")
        )

    # 处理查重命令
    if category == "查重":
        return await _handle_check_duplicate_logic(event)

    if category not in STORAGE_DIRS:
        return Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text(f"未知分类: {category}\n支持的分类: nai, 灵感, 默认")
        )

    image_urls = await extract_images_from_event(event)

    if not image_urls:
        return Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("请回复或发送图片")
        )

    save_dir = STORAGE_DIRS[category]
    saved_count = 0
    skipped_count = 0
    duplicate_count = 0
    nai_skipped = False

    for url in image_urls:
        try:
            image_data = await download_image(url)
            if not image_data:
                skipped_count += 1
                continue

            # NAI模式需要检查Description字段
            if category == "nai":
                try:
                    img = Image.open(io.BytesIO(image_data))
                    img_array = np.array(img.convert("RGBA"))
                    metadata = extract_image_metadata(img_array)

                    if "Description" not in metadata:
                        logger.info("图片无Description字段，跳过")
                        nai_skipped = True
                        continue
                except Exception as e:
                    logger.warning(f"无法提取NAI元数据: {e}")
                    nai_skipped = True
                    continue

            # 计算哈希避免重复
            img_hash = get_image_hash(image_data)

            # 使用JSON索引检查是否已存在
            existing_categories = check_hash_in_index(img_hash)
            if existing_categories:
                duplicate_count += 1
                logger.info(f"图片已存在于: {existing_categories}")
                continue

            # 确定文件扩展名
            try:
                img = Image.open(io.BytesIO(image_data))
                fmt = img.format.lower() if img.format else "png"
            except Exception:
                fmt = "png"

            # 保存文件
            save_path = save_dir / f"{img_hash}.{fmt}"
            save_path.write_bytes(image_data)

            # 添加到哈希索引
            add_hash_to_index(img_hash, category, f"{img_hash}.{fmt}")

            saved_count += 1
            logger.info(f"图片已保存: {save_path}")

        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            skipped_count += 1

    # 统计当前目录图片数量
    total_count = count_images_in_dir(save_dir)

    # NAI模式特殊处理
    if category == "nai" and nai_skipped and saved_count == 0:
        return Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("未读取到prompt，已跳过。")
        )

    result_parts = []
    if saved_count > 0:
        result_parts.append(f"成功保存 {saved_count} 张")
    if duplicate_count > 0:
        result_parts.append(f"重复 {duplicate_count} 张")
    if skipped_count > 0:
        result_parts.append(f"跳过 {skipped_count} 张")

    result_text = "，".join(result_parts) if result_parts else "无图片保存"
    result_text += f"\n[{category}] 当前共 {total_count} 张"

    return Message(
        MessageSegment.reply(event.message_id) + MessageSegment.text(result_text)
    )


@_save_image.handle()
async def handle_save_image(bot: Bot, event: MessageEvent):
    """存储图片"""
    raw_text = event.get_message().extract_plain_text().strip()
    category = raw_text.replace("#存图", "").strip()

    # 如果没有指定分类，默认存储到"默认"分类
    if not category:
        category = "默认"

    result = await _do_save_image(bot, event, category)
    await _save_image.finish(result)


@_save_image_alias.handle()
async def handle_save_image_alias(bot: Bot, event: MessageEvent):
    """#改图 -> #存图 默认"""
    result = await _do_save_image(bot, event, "默认")
    await _save_image_alias.finish(result)


@_save_inspiration.handle()
async def handle_save_inspiration(bot: Bot, event: MessageEvent):
    """#灵感 -> #存图 灵感"""
    result = await _do_save_image(bot, event, "灵感")
    await _save_inspiration.finish(result)


@_view_tag.handle()
async def handle_view_tag(bot: Bot, event: MessageEvent):
    """查看图片的Source信息（版本信息）"""
    image_urls = await extract_images_from_event(event)

    if not image_urls:
        await _view_tag.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请回复或发送图片")
            )
        )
        return

    results = []
    for i, url in enumerate(image_urls):
        try:
            image_data = await download_image(url)
            if not image_data:
                results.append(f"图片{i + 1}: 下载失败")
                continue

            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img.convert("RGBA"))
            metadata = extract_image_metadata(img_array)

            source = metadata.get("Source", "无Source信息")
            if len(image_urls) > 1:
                results.append(f"图片{i + 1} Source:\n{source}")
            else:
                results.append(f"Source:\n{source}")

        except AssertionError:
            results.append(f"图片{i + 1}: 非NAI图片或无法解析元数据")
        except Exception as e:
            results.append(f"图片{i + 1}: 解析失败 - {e}")

    await _view_tag.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("\n\n".join(results))
        )
    )


@_parse_prompt.handle()
async def handle_parse_prompt(bot: Bot, event: MessageEvent):
    """解析图片的prompt信息"""
    image_urls = await extract_images_from_event(event)

    if not image_urls:
        await _parse_prompt.finish(
            Message(
                MessageSegment.reply(event.message_id)
                + MessageSegment.text("请回复或发送图片")
            )
        )
        return

    results = []
    for i, url in enumerate(image_urls):
        try:
            image_data = await download_image(url)
            if not image_data:
                results.append(f"图片{i + 1}: 下载失败")
                continue

            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img.convert("RGBA"))
            metadata = extract_image_metadata(img_array)

            prompt = metadata.get("Description", "无prompt信息")
            if len(image_urls) > 1:
                results.append(f"图片{i + 1} Prompt:\n{prompt}")
            else:
                results.append(f"Prompt:\n{prompt}")

        except AssertionError:
            results.append(f"图片{i + 1}: 非NAI图片或无法解析元数据")
        except Exception as e:
            results.append(f"图片{i + 1}: 解析失败 - {e}")

    await _parse_prompt.finish(
        Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("\n\n".join(results))
        )
    )


@_image_count.handle()
async def handle_image_count(bot: Bot, event: MessageEvent):
    """查看各分类图片数量"""
    counts = []
    total = 0

    for name, dir_path in STORAGE_DIRS.items():
        count = count_images_in_dir(dir_path)
        counts.append(f"[{name}] {count} 张")
        total += count

    result_text = "📊 图片存储统计\n" + "\n".join(counts) + f"\n---\n总计: {total} 张"

    await _image_count.finish(
        Message(
            MessageSegment.reply(event.message_id) + MessageSegment.text(result_text)
        )
    )


async def _handle_check_duplicate_logic(event: MessageEvent) -> Message:
    """查重逻辑核心函数"""
    image_urls = await extract_images_from_event(event)

    if not image_urls:
        return Message(
            MessageSegment.reply(event.message_id)
            + MessageSegment.text("请回复或发送图片")
        )

    results = []
    for i, url in enumerate(image_urls):
        try:
            image_data = await download_image(url)
            if not image_data:
                results.append(f"图片{i + 1}: 下载失败")
                continue

            img_hash = get_image_hash(image_data)

            # 使用JSON索引查找
            found_in = check_hash_in_index(img_hash)

            if found_in:
                categories = "、".join(found_in)
                if len(image_urls) > 1:
                    results.append(f"图片{i + 1}: 已存在于 [{categories}]")
                else:
                    results.append(f"已存在于 [{categories}]")
            else:
                if len(image_urls) > 1:
                    results.append(f"图片{i + 1}: 未存储")
                else:
                    results.append("未存储")

        except Exception as e:
            logger.error(f"查重失败: {e}")
            results.append(f"图片{i + 1}: 查重失败 - {e}")

    return Message(
        MessageSegment.reply(event.message_id) + MessageSegment.text("\n".join(results))
    )
