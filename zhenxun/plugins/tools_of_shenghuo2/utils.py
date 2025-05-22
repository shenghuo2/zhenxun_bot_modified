from typing import Tuple
import aiohttp
from pydantic import BaseModel
from .config import DEEPSEEK_API_KEY
from zhenxun.services.log import logger


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
