import html
import json
from typing import Any, Tuple

import aiohttp
from pydantic import BaseModel

from zhenxun.services.log import logger

from .config import DEEPSEEK_API_KEY

# 已知的广告 JSON 卡片 app 标识
AD_APP_IDS = {
    "com.tencent.tuwen.lua",
    "com.tencent.troopsharecard",
}

# 已知的广告关键词（出现在 JSON 卡片 title / desc / prompt 中即判定为广告）
AD_KEYWORDS = [
    "福利导航",
    "进入-截图-扫码",
    "推荐群聊",
    "加群",
    "进群",
    "群聊推荐",
    "扫码进群",
    "点击加群",
    "微信裙",
    "必进",
]

# 文本/图文引流常见特征
AD_TEXT_KEYWORDS = [
    "第一群",
    "稳定更新",
    "风雨无阻",
    "长线更新",
    "更多奇奇怪怪",
    "微信裙",
    "必进",
]

# 引流文字末尾标记（纯文本消息以这些符号结尾则视为广告）
AD_TRAILING_MARKERS = [
    "🔚",
]

AD_DIRECTION_MARKERS = [
    "👇",
    "⬇",
    "⏩",
    "传送",
]


AD_URL_PATTERNS = [
    "qm.qq.com/q/",
    "qm.qq.com/cgi-bin/qm/qr",
    "groupwpa",
    "show_pslcard",
    "card_type=group",
]


GROUP_SHARE_HINTS = [
    "推荐群聊",
    "群聊推荐",
    "群聊",
    "群资料",
    "加群",
    "进群",
    "群号",
    "群二维码",
]


def _walk_strings(obj: Any) -> list[str]:
    """递归提取 JSON 卡片中的所有字符串字段，便于做通用文本特征匹配。"""
    texts: list[str] = []
    if isinstance(obj, str):
        stripped = obj.strip()
        if stripped:
            texts.append(stripped)
        return texts

    if isinstance(obj, dict):
        for value in obj.values():
            texts.extend(_walk_strings(value))
        return texts

    if isinstance(obj, list):
        for item in obj:
            texts.extend(_walk_strings(item))

    return texts


def _contains_any(texts: list[str], patterns: list[str]) -> bool:
    return any(pattern in text for text in texts for pattern in patterns)


def _looks_like_text_ad(full_text: str, has_image: bool) -> bool:
    stripped = full_text.strip()
    if not stripped:
        return False

    if any(stripped.endswith(marker) for marker in AD_TRAILING_MARKERS):
        return True

    if any(pattern in stripped for pattern in AD_URL_PATTERNS):
        return True

    keyword_hits = sum(1 for keyword in AD_TEXT_KEYWORDS if keyword in stripped)
    direction_hits = sum(stripped.count(marker) for marker in AD_DIRECTION_MARKERS)

    if keyword_hits >= 2:
        return True

    if has_image and keyword_hits >= 1 and direction_hits >= 2:
        return True

    return has_image and direction_hits >= 4


def _is_group_share_card(card: dict, texts: list[str]) -> bool:
    """识别群聊分享卡片。命中后直接按广告处理。"""
    app_id = card.get("app", "")
    meta = card.get("meta", {})
    contact = meta.get("contact", {}) if isinstance(meta, dict) else {}

    if app_id not in {"com.tencent.contact.lua", "com.tencent.troopsharecard"}:
        return False

    # troopsharecard 本身就是群分享卡片。
    if app_id == "com.tencent.troopsharecard":
        return True

    if _contains_any(texts, AD_URL_PATTERNS):
        return True

    tag = str(contact.get("tag", ""))
    prompt = str(card.get("prompt", ""))
    nickname = str(contact.get("nickname", ""))
    view = str(card.get("view", ""))
    bizsrc = str(card.get("bizsrc", ""))
    if view == "contact" and bizsrc == "qun.share":
        return True

    return any(hint in value for value in (tag, prompt, nickname) for hint in GROUP_SHARE_HINTS)


def is_ad_message(msg: dict) -> bool:
    """判断转发消息中的某条子消息是否为广告。

    检测规则：
    1. 文本或图文消息命中引流文案、群邀请链接、下箭头导流样式
    2. type=json 且 app 在 AD_APP_IDS 中（已知广告/引流卡片）
    3. type=json 且任意字段包含 AD_KEYWORDS 或 AD_URL_PATTERNS
    4. type=json 且识别为群聊卡片时，直接视为广告
    """
    message_list = msg.get("message")
    if not message_list or not isinstance(message_list, list):
        return False

    text_parts: list[str] = []
    has_json = False
    has_image = False

    for seg in message_list:
        seg_type = seg.get("type", "")
        if seg_type == "text":
            text_parts.append(seg.get("data", {}).get("text", ""))
        elif seg_type == "json":
            has_json = True
        elif seg_type == "image":
            has_image = True

    full_text = "".join(text_parts)
    if _looks_like_text_ad(full_text, has_image):
        return True

    if not has_json:
        return False

    for seg in message_list:
        if seg.get("type") != "json":
            continue
        raw_data = seg.get("data", {}).get("data", "")
        if not raw_data:
            continue
        try:
            card = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            continue

        texts = _walk_strings(card)

        app_id = card.get("app", "")
        if app_id in AD_APP_IDS:
            return True

        if _contains_any(texts, AD_KEYWORDS):
            return True

        if _contains_any(texts, AD_URL_PATTERNS):
            return True

        if _is_group_share_card(card, texts):
            return True

    return False


class BalanceInfo(BaseModel):
    currency: str
    total_balance: str
    granted_balance: str
    topped_up_balance: str



async def get_deepseek_balance() -> Tuple[str, int]:
    """获取DeepSeek账户余额"""
    api_url = "https://api.deepseek.com/user/balance"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status != 200:
                    return f"❌ 接口请求失败，状态码：{response.status}", 500
                
                data = await response.json()
                if not data.get("is_available", False):
                    return str(response.json()), 200

                if not data.get("balance_infos"):
                    return "⚠️ 未找到余额信息", 404

                for info in data["balance_infos"]:
                    if info["currency"] == "CNY":
                        balance = BalanceInfo(**info)
                        return (
                            "📊 DeepSeek账户余额\n"
                            f"• 总余额：¥{balance.total_balance}\n"
                            f"• 赠送余额：¥{balance.granted_balance}\n"
                            f"• 充值余额：¥{balance.topped_up_balance}"
                        ), 200
                return "⚠️ 未找到CNY余额信息", 404

    except aiohttp.ClientError as e:
        return f"❌ 网络请求失败：{str(e)}", 500
    except Exception as e:
        logger.error(f"DeepSeek余额查询异常：{str(e)}")
        return "❌ 服务暂时不可用，请稍后再试", 500
