from pathlib import Path

from zhenxun.configs.config import Config

PLUGIN_NAME = "message_dedup"
PLUGIN_DIR = Path(__file__).parent
ASSETS_DIR = PLUGIN_DIR / "assets"
REPLY_IMAGE = ASSETS_DIR / "saiboliequan.jpg"
DATABASE_PATH = PLUGIN_DIR / "messages.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# ── 配置键 ──────────────────────────────────────────────
MODULE = "message_dedup"

CONFIG_DEFS = [
    {
        "module": MODULE,
        "key": "GROUP_WHITELIST",
        "value": [],
        "default_value": [],
        "help": "启用该插件的群号列表，为空则全部启用",
        "type": list,
    },
    {
        "module": MODULE,
        "key": "ENABLE_FORWARD_CHECK",
        "value": True,
        "default_value": True,
        "help": "是否启用转发消息查重",
        "type": bool,
    },
    {
        "module": MODULE,
        "key": "ENABLE_BILIBILI_CHECK",
        "value": True,
        "default_value": True,
        "help": "是否启用B站视频查重（含卡片和文本链接）",
        "type": bool,
    },
    {
        "module": MODULE,
        "key": "ENABLE_VIDEO_CHECK",
        "value": True,
        "default_value": True,
        "help": "是否启用普通视频消息查重",
        "type": bool,
    },
    {
        "module": MODULE,
        "key": "ENABLE_MARK_COMMAND",
        "value": True,
        "default_value": True,
        "help": "是否启用 #标记 / #删除标记 命令",
        "type": bool,
    },
]


def get_cfg(key: str):
    return Config.get_config(MODULE, key)
