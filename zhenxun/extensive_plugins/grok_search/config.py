"""Grok 插件配置与运行时状态持久化。"""

import json
import os
from pathlib import Path
from typing import Any

from nonebot.log import logger

from zhenxun.configs.path_config import DATA_PATH

PLUGIN_DIR = Path(__file__).parent
ENV_FILE = PLUGIN_DIR / ".env"


def _strip_env_value(value: str) -> str:
    """去掉 .env 值两侧空白和简单引号。"""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_local_env() -> dict[str, str]:
    """读取插件同目录 .env，避免把密钥写进源码。"""
    if not ENV_FILE.exists():
        return {}

    env_data: dict[str, str] = {}
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key:
                env_data[key] = _strip_env_value(value)
    except Exception as e:
        logger.warning(f"Grok 本地 .env 读取失败，将使用环境变量或默认值: {e}")
    return env_data


_LOCAL_ENV = _load_local_env()


def _get_env_value(key: str, default: str = "") -> str:
    """优先读取进程环境变量，其次读取插件同目录 .env。"""
    return os.getenv(key) or _LOCAL_ENV.get(key) or default

# Grok API 配置
GROK_API_BASE: str = _get_env_value("GROK_API_BASE", "http://localhost:8000")
GROK_API_KEY: str = _get_env_value("GROK_API_KEY")

# 模型配置（搜索和改图使用不同的模型）
GROK_SEARCH_MODEL: str = "grok-4.1-thinking"  # 搜索使用的模型
GROK_EDIT_MODEL: str = "grok-imagine-1.0"  # 改图使用的模型（图片生成专用）

# 向后兼容
GROK_MODEL: str = GROK_SEARCH_MODEL

GROK_DATA_DIR = DATA_PATH / "grok_search"
GROK_RUNTIME_CONFIG_FILE = GROK_DATA_DIR / "config.json"


def _normalize_model(value: Any, default: str) -> str:
    """读取持久化配置时保证模型名是非空字符串。"""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def load_runtime_config() -> dict[str, str]:
    """加载运行时模型配置，不存在或损坏时回退默认值。"""
    config = {
        "search_model": GROK_SEARCH_MODEL,
        "edit_model": GROK_EDIT_MODEL,
    }

    if not GROK_RUNTIME_CONFIG_FILE.exists():
        return config

    try:
        raw_data = json.loads(GROK_RUNTIME_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Grok 运行时配置读取失败，将使用默认配置: {e}")
        return config

    if not isinstance(raw_data, dict):
        logger.warning("Grok 运行时配置格式异常，将使用默认配置")
        return config

    config["search_model"] = _normalize_model(
        raw_data.get("search_model"), GROK_SEARCH_MODEL
    )
    config["edit_model"] = _normalize_model(raw_data.get("edit_model"), GROK_EDIT_MODEL)
    return config


def save_runtime_config(search_model: str, edit_model: str) -> None:
    """保存运行时模型配置。"""
    GROK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "search_model": search_model,
        "edit_model": edit_model,
    }
    GROK_RUNTIME_CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
