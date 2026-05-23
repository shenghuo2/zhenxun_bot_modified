"""Example config for Windsurf stock monitor.

Copy to config.py locally and fill in private values.
"""

import os

SHOP_API_URL: str = os.getenv("WINDSURF_SHOP_API_URL", "https://example.com/shopApi/Shop/goodsList")
SHOP_TOKEN: str = os.getenv("WINDSURF_SHOP_TOKEN", "")
GOODS_TYPE: str = "card"
REQUEST_TIMEOUT: float = 20.0

REQUEST_HEADERS: dict[str, str] = {}
REQUEST_COOKIES: dict[str, str] = {}

TARGET_CATEGORY_NAME: str = "example-category"
TARGET_GOODS_NAMES: list[str] = ["example-product"]
QQ_GROUP_IDS: list[int] = [123456789]

CHECK_INTERVAL_MINUTES: int = 1
REPEAT_NOTIFY_WHEN_IN_STOCK: bool = False

SMTP_ENABLED: bool = False
SMTP_HOST: str = os.getenv("WINDSURF_SMTP_HOST", "")
SMTP_PORT: int = 465
SMTP_USE_SSL: bool = True
SMTP_USE_STARTTLS: bool = True
SMTP_USERNAME: str = os.getenv("WINDSURF_SMTP_USERNAME", "")
SMTP_PASSWORD: str = os.getenv("WINDSURF_SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("WINDSURF_SMTP_FROM", "")
SMTP_TO: list[str] = []
SMTP_SUBJECT: str = "[库存提醒] Windsurf 有货"
