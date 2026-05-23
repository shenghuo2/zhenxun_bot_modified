"""Example config for web-search-tool.

Copy to config_local.py locally and fill in private values.
"""

import os

ARK_API_KEY: str = os.getenv("WEB_SEARCH_ARK_API_KEY", "")
KIMI_API_KEY: str = os.getenv("WEB_SEARCH_KIMI_API_KEY", "")
