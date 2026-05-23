"""Example config for Gemini image editing.

Copy to config.py locally and fill in private values.
"""

import os

GEMINI_API_BASE: str = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image-preview")

GEMINI_COST_PER_CALL: float = 0.16
