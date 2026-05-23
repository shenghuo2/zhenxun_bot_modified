"""Example config for OpenAI image generation.

Copy to config_local.py locally and fill in private values.
"""

import os

API_BASE: str = os.getenv("OPENAI_IMAGE_GEN_API_BASE", "https://api.openai.com")
API_KEY: str = os.getenv("OPENAI_IMAGE_GEN_API_KEY", "")
MODEL: str = os.getenv("OPENAI_IMAGE_GEN_MODEL", "gpt-image-1")
