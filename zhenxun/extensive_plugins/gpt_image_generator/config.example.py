"""Example config for GPT image generation.

Copy to config_local.py locally and fill in private provider values.
"""

import os

PROVIDERS = [
    {
        "name": "OpenAI",
        "base_url": os.getenv("GPT_IMAGE_PROVIDER_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("GPT_IMAGE_PROVIDER_API_KEY", ""),
        "model": os.getenv("GPT_IMAGE_PROVIDER_MODEL", "gpt-image-1"),
        "returns_b64": True,
        "size_faithful": True,
        "cost_per_call": None,
        "cost_per_million_input_tokens": 40.0,
        "cost_per_million_output_tokens": 240.0,
    },
]

SUPERUSER_RETRY_CHAIN = ["OpenAI"]
REGULAR_RETRY_CHAIN = ["OpenAI"]

COOLDOWN_EXTRA_SECONDS = 10
COOLDOWN_FAIL_SECONDS = 30
DAILY_LIMIT = 3
MAX_COUNT_REGULAR = 3
GROUP_DAILY_LIMITS: dict[str, int] = {}

REQUEST_TIMEOUT = 600

DEFAULT_QUALITY = "medium"
DEFAULT_COUNT = 1
QUALITY_VALUES = {"low", "medium", "high", "max"}

PRESET_RATIOS = {
    "1:1": (1, 1),
    "1:2": (1, 2),
    "1:3": (1, 3),
    "2:1": (2, 1),
    "3:1": (3, 1),
    "2:3": (2, 3),
    "3:2": (3, 2),
    "3:4": (3, 4),
    "4:3": (4, 3),
    "16:9": (16, 9),
    "9:16": (9, 16),
}

SIZE_PRESETS = {
    "1k": 1024 * 1024,
    "2k": 2048 * 2048,
}

MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_SIDE = 3840 - 16
PIXEL_ALIGNMENT = 16
MAX_RATIO = 3.0

SHORTCUT_PRESETS: dict[str, dict] = {}
