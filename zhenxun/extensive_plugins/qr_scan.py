import tempfile
from pathlib import Path

import cv2
import httpx
import pyzbar.pyzbar as pyzbar
import zxing
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.plugin import PluginMetadata

from zhenxun.services.log import logger

__plugin_meta__ = PluginMetadata(
    name="二维码扫描",
    description="回复图片或发送 scan+图片 自动解码二维码/条形码",
    usage="scan [图片] 或 回复图片消息并发送 scan",
    type="application",
    supported_adapters={"~onebot.v11"},
)

scan_cmd = on_command("scan", priority=5, block=True)


def _extract_image_url(message: Message) -> str | None:
    """从消息中提取第一张图片的 URL。"""
    for seg in message:
        if seg.type == "image":
            url = seg.data.get("url") or seg.data.get("file")
            if url and url.startswith("http"):
                return url
    return None


async def _download_image(url: str) -> bytes:
    """异步下载图片。"""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _decode_wechat(image_path: str) -> str | None:
    """使用 OpenCV WeChatQRCode 解码。"""
    try:
        detector = cv2.wechat_qrcode_WeChatQRCode()
        image = cv2.imread(image_path)
        if image is None:
            return None
        results, _ = detector.detectAndDecode(image)
        if results:
            return results[0]
    except Exception as e:
        logger.debug(f"wechat_qrcode 解码失败: {e}", "qr_scan")
    return None


def _decode_pyzbar(image_path: str) -> tuple[str, str] | None:
    """使用 pyzbar 解码，返回 (类型, 内容)。"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None
        barcodes = pyzbar.decode(image)
        if barcodes:
            return barcodes[0].type, barcodes[0].data.decode()
    except Exception as e:
        logger.debug(f"pyzbar 解码失败: {e}", "qr_scan")
    return None


def _decode_zxing(image_path: str) -> tuple[str, str] | None:
    """使用 zxing 解码，返回 (类型, 内容)。"""
    try:
        reader = zxing.BarCodeReader()
        result = reader.decode(image_path)
        if result and result.format is not None:
            return result.format, result.raw
    except Exception as e:
        logger.debug(f"zxing 解码失败: {e}", "qr_scan")
    return None


@scan_cmd.handle()
async def handle_scan(bot: Bot, event: MessageEvent):
    # 1. 提取图片 URL：优先当前消息，其次回复消息
    image_url = _extract_image_url(event.message)
    if not image_url and event.reply:
        image_url = _extract_image_url(event.reply.message)

    if not image_url:
        await scan_cmd.finish("请发送图片或回复一条包含图片的消息再使用 scan 命令")
        return

    # 2. 下载图片到临时文件
    try:
        image_data = await _download_image(image_url)
    except Exception as e:
        logger.warning(f"下载图片失败: {e}", "qr_scan")
        await scan_cmd.finish("图片下载失败，请稍后再试")
        return

    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
        tmp.write(image_data)
        tmp.flush()
        tmp_path = tmp.name

        # 3. 依次尝试三引擎解码
        # ── WeChatQRCode ──
        result = _decode_wechat(tmp_path)
        if result:
            await scan_cmd.finish(f"[+] 检测到二维码\n[+] {result}\n(wechat_qrcode)")
            return

        # ── pyzbar ──
        pyzbar_result = _decode_pyzbar(tmp_path)
        if pyzbar_result:
            code_type, content = pyzbar_result
            await scan_cmd.finish(f"[+] 检测到{code_type}码\n[+] {content}\n(pyzbar)")
            return

        # ── zxing ──
        zxing_result = _decode_zxing(tmp_path)
        if zxing_result:
            code_type, content = zxing_result
            await scan_cmd.finish(f"[+] 检测到{code_type}码\n[+] {content}\n(zxing)")
            return

    await scan_cmd.finish("未检测到二维码或条形码")
