"""Example Kimi search test.

Copy to test_kimi.py locally and provide your own API key.
"""

import asyncio

from .config import KIMI_API_URL

KIMI_API_KEY = ""


async def main() -> None:
    print(f"Use {KIMI_API_URL} with a local-only API key")


if __name__ == "__main__":
    asyncio.run(main())
