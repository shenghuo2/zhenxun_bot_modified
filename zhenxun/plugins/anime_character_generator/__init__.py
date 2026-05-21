import asyncio
import time
from pathlib import Path

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.permission import SUPERUSER, SuperUser
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import (
    Alconna,
    Args,
    Arparma,
    At,
    MultiVar,
    Query,
    on_alconna,
)
from nonebot_plugin_uninfo import Uninfo

from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

from .config import is_configured, update_config
from .image_generator import generate_image, test_generate
from .utils import format_character_with_prompts, generate_smart_character

# 冷却时间配置（秒）
GLOBAL_COOLDOWN_SECONDS = 20  # 全局冷却时间
USER_COOLDOWN_SECONDS = 180  # 用户冷却时间（5分钟）

# 全局冷却时间，存储插件最后使用时间
global_cooldown_time = 0
# 用户冷却时间字典，存储用户ID和上次使用时间
user_cooldown = {}

__plugin_meta__ = PluginMetadata(
    name="二次元的我",
    description="生成专属于你的二次元角色，支持 NovelAI 图像生成",
    usage="""
    指令：
        #二次元的我 / #二次元转生 - 生成专属于你的二次元角色
        #生成角色图像 <提示词> - 根据提示词生成角色图像
        
    管理员指令：
        #novelai配置 <用户名> <密码> - 配置 NovelAI 账户（仅超级用户）
        #测试novelai - 测试 NovelAI 连接（仅超级用户）
    """.strip(),
    extra=PluginExtraData(
        author="Assistant",
        version="0.1",
        menu_type="娱乐",
    ).dict(),
)

_my_character_matcher = on_alconna(
    Alconna("#二次元的我"),
    aliases={"#二次元转生"},
    priority=5,
    block=True,
)


@_my_character_matcher.handle()
async def _(session: Uninfo):
    """生成专属二次元角色"""
    global global_cooldown_time
    try:
        user_id = session.user.id
        current_time = time.time()
        global_cooldown_message = ""  # 初始化全局冷却消息

        # 检查是否为超级用户，超级用户无视冷却
        bot = get_bot()
        is_superuser = user_id in bot.config.superusers

        if not is_superuser:
            # 检查全局冷却时间
            if global_cooldown_time > 0:
                global_time_passed = current_time - global_cooldown_time
                if global_time_passed < GLOBAL_COOLDOWN_SECONDS:
                    # 等待全局冷却结束
                    sleep_time = GLOBAL_COOLDOWN_SECONDS - global_time_passed
                    await asyncio.sleep(sleep_time)
                    current_time = time.time()  # 更新当前时间
                    # 将冷却提示添加到后续消息中
                    global_cooldown_message = f"⏳ 刚才冷却了 {sleep_time:.1f}秒\n\n"

            # 检查用户冷却时间
            if user_id in user_cooldown:
                time_passed = current_time - user_cooldown[user_id]
                if time_passed < USER_COOLDOWN_SECONDS:
                    remaining_time = int(USER_COOLDOWN_SECONDS - time_passed)
                    minutes = remaining_time // 60
                    seconds = remaining_time % 60
                    await MessageUtils.build_message(
                        [
                            "⏰ ",
                            At(flag="user", target=str(user_id)),
                            f" 冷却中，请等待 {minutes}分{seconds}秒 后再试",
                        ]
                    ).send()
                    return

        # 获取用户名（优先使用群昵称）
        username = session.user.nick or session.user.name or f"用户{user_id}"

        # 生成智能角色属性
        character_data = generate_smart_character()

        # 格式化为中文描述，传入用户名
        prompts, description = format_character_with_prompts(
            character_data, username=username
        )

        # 构建完整消息
        message = f"{global_cooldown_message}✨{description}"
        message += f"\n💡 提示：个人冷却时间{USER_COOLDOWN_SECONDS // 60}分钟，全局冷却时间{GLOBAL_COOLDOWN_SECONDS}秒"

        # 发送角色描述
        await MessageUtils.build_message(message).send(reply_to=True)

        # 如果 NovelAI 已配置，自动生成角色图像
        if is_configured():
            try:
                # await MessageUtils.build_message(
                #     "🎨 正在为你生成专属角色图像，请稍候..."
                # ).send()

                # 构建图像生成的 prompt
                # 基础 prompt + 角色属性
                base_prompt = "1 girl, solo, official art, simple background, full body, standing, best quality"
                full_prompt = f"{base_prompt}, {prompts}"

                # 生成图像
                image_path = await generate_image(prompt=full_prompt)

                if image_path:
                    # 发送图像
                    # await MessageUtils.build_message(
                    #     f"🖼️ {username} 的专属二次元角色图像生成完成！"
                    # ).send()
                    await MessageUtils.build_message(Path(image_path)).send(
                        reply_to=True
                    )
                    logger.info(f"用户 {user_id}({username}) 自动生成了专属角色图像")
                else:
                    await MessageUtils.build_message(
                        "⚠️ 角色图像生成失败，但角色描述已生成"
                    ).send(reply_to=True)

            except Exception as img_error:
                logger.error(f"自动生成角色图像失败: {img_error}")
                await MessageUtils.build_message(
                    "⚠️ 角色图像生成失败，但角色描述已生成"
                ).send(reply_to=True)

        # 更新冷却时间（superuser也需要更新以维护全局冷却）
        global_cooldown_time = current_time
        if not is_superuser:
            user_cooldown[user_id] = current_time

        logger.info(f"用户 {user_id}({username}) 生成了专属二次元角色")
    except Exception as e:
        logger.error(f"生成专属角色失败: {e}")
        await MessageUtils.build_message("角色生成失败，请稍后再试").send(reply_to=True)


# NovelAI 图像生成相关命令
_novelai_config_matcher = on_alconna(
    Alconna("#novelai配置", "api_token:str"),
    priority=5,
    block=True,
)


@_novelai_config_matcher.handle()
async def _(session: Uninfo, api_token: str):
    """配置 NovelAI API Token（仅超级用户）"""
    user_id = session.user.id

    # 检查是否为超级用户
    try:
        bot = get_bot()
        is_superuser = str(user_id) in bot.config.superusers
    except Exception:
        is_superuser = False

    if not is_superuser:
        await MessageUtils.build_message(
            "❌ 只有超级用户才能配置 NovelAI API Token"
        ).send(reply_to=True)
        return

    try:
        # 更新配置
        update_config(api_token=api_token, enable=True)

        await MessageUtils.build_message(
            "✅ NovelAI 配置成功，图像生成功能已启用"
        ).send(reply_to=True)
        logger.info(f"超级用户 {user_id} 配置了 NovelAI API Token")

    except Exception as e:
        logger.error(f"配置 NovelAI 失败: {e}")
        await MessageUtils.build_message("❌ 配置失败，请稍后再试").send(reply_to=True)


_generate_image_matcher = on_alconna(
    Alconna("#生成角色图像", Args["prompt", MultiVar(str)]),
    priority=5,
    block=True,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@_generate_image_matcher.handle()
async def _(
    bot: Bot,
    event: MessageEvent,
    session: Uninfo,
    arparma: Arparma,
    prompt: Query[tuple[str, ...]] = Query("prompt", ()),
):
    """根据提示词生成角色图像"""
    user_id = session.user.id

    # 检查功能是否启用
    if not is_configured():
        await MessageUtils.build_message(
            "❌ 图像生成功能未启用\n请超级用户使用 #novelai配置 <api_token> 来配置"
        ).send(reply_to=True)
        return

    try:
        # 获取用户名
        username = session.user.nick or session.user.name or f"用户{user_id}"

        # 将prompt元组转换为字符串
        prompt_str = " ".join(prompt.result) if prompt.result else ""

        if not prompt_str.strip():
            await MessageUtils.build_message("❌ 请提供有效的提示词").send(
                reply_to=True
            )
            return

        # await MessageUtils.build_message("🎨 正在生成图像，请稍候...").send(
        #     reply_to=True
        # )
        await bot.call_api(
            "set_msg_emoji_like", message_id=event.message_id, emoji_id="282"
        )

        # 生成图像（自动保存到 image_cache 文件夹，使用 seed 和 prompt 命名）
        image_path = await generate_image(prompt=prompt_str)

        if image_path:
            # 发送图像
            # await MessageUtils.build_message(
            #     [f"✨ {username} 的角色图像生成完成！\n", f"提示词: {prompt_str}"]
            # ).send(reply_to=True)

            # 发送图像文件
            await MessageUtils.build_message(Path(image_path)).send(reply_to=True)

            logger.info(f"用户 {user_id}({username}) 生成了角色图像")
        else:
            await MessageUtils.build_message("❌ 图像生成失败，请稍后再试").send(
                reply_to=True
            )

    except Exception as e:
        logger.error(f"生成角色图像失败: {e}")
        await MessageUtils.build_message("❌ 图像生成失败，请稍后再试").send(
            reply_to=True
        )


_test_novelai_matcher = on_alconna(
    Alconna("#测试novelai"),
    priority=5,
    block=True,
)


@_test_novelai_matcher.handle()
async def _(session: Uninfo):
    """测试 NovelAI 连接（仅超级用户）"""
    user_id = session.user.id

    # 检查是否为超级用户
    try:
        bot = get_bot()
        is_superuser = str(user_id) in bot.config.superusers
    except Exception:
        is_superuser = False

    if not is_superuser:
        await MessageUtils.build_message("❌ 只有超级用户才能测试 NovelAI 连接").send()
        return

    try:
        if not is_configured():
            await MessageUtils.build_message(
                "❌ 请先使用 #novelai配置 <api_token> 来配置 API Token"
            ).send()
            return

        await MessageUtils.build_message("🧪 正在测试 NovelAI 连接...").send()

        # 测试生成一个简单的图像
        test_prompt = "1girl, anime style, simple, test image"
        try:
            image_path = await test_generate()
            if image_path:
                await MessageUtils.build_message("✅ NovelAI 连接测试成功！").send()
            else:
                await MessageUtils.build_message("❌ NovelAI 连接测试失败").send()
        except Exception as test_error:
            await MessageUtils.build_message(f"❌ 测试失败: {test_error!s}").send()

    except Exception as e:
        logger.error(f"测试 NovelAI 连接失败: {e}")
        await MessageUtils.build_message(f"❌ 测试失败: {e!s}").send()
