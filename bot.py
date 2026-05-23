import os
from pathlib import Path

import nonebot
from dotenv import load_dotenv

# from nonebot.adapters.discord import Adapter as DiscordAdapter
# from nonebot.adapters.dodo import Adapter as DoDoAdapter
# from nonebot.adapters.kaiheila import Adapter as KaiheilaAdapter
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


def _load_process_env() -> None:
    """Load dotenv files into process env for libraries that read os.environ directly."""
    root = Path(__file__).resolve().parent
    base_env = root / ".env"
    playwright_browsers = root / "data" / "ms-playwright"

    if base_env.is_file():
        load_dotenv(base_env, override=False)

    environment = os.environ.get("ENVIRONMENT", "prod")
    env_file = root / f".env.{environment}"
    if env_file.is_file():
        load_dotenv(env_file, override=False)

    if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ and playwright_browsers.is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(playwright_browsers)

_load_process_env()
nonebot.init()


driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)
# driver.register_adapter(KaiheilaAdapter)
# driver.register_adapter(DoDoAdapter)
# driver.register_adapter(DiscordAdapter)

from zhenxun.services.db_context import disconnect, init

driver.on_startup(init)
driver.on_shutdown(disconnect)

# nonebot.load_builtin_plugins("echo")
nonebot.load_plugins("zhenxun/builtin_plugins")
nonebot.load_plugins("zhenxun/plugins")
nonebot.load_plugins("zhenxun/extensive_plugins")


if __name__ == "__main__":
    nonebot.run()
