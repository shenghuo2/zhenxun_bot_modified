import random
import asyncio
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.permission import SUPERUSER
from openai import OpenAI

from .config import DEEPSEEK_API_BASE, DEEPSEEK_API_KEY

# 初始化 DeepSeek API
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)

# 目标群聊
TARGET_GROUP = 787599185

# 记录开骂状态
roast_enabled = False
roast_target = "你"
roast_count = 5

# 生成阴阳怪气的 Prompt
def generate_prompt(target):
    prompts = [
        f"被骂目标是 {target}，请用阴阳怪气但不带脏话的方式讽刺他们。",
        f"请嘲讽 {target}，用讽刺但不骂人的语气，让他们感觉自己很蠢。",
        f"用阴阳怪气的方式讽刺 {target}，但不使用脏话，要有点幽默感。",
        f"针对 {target}，编写一句让人哭笑不得的阴阳怪气评价。",
        f"请用高情商但充满讽刺的语气评价 {target}，但不要使用脏话。",
        f"请用贱贱的语气损 {target}，让他们觉得自己很无语但挑不出毛病。",
        f"请用阴阳怪气的方式损 {target}，让他们感觉自己像个笨蛋，但不能用脏话。",
        f"请针对 {target}，用讽刺但有趣的方式进行调侃，语气要显得高人一等。",
        f"以 {target} 为对象，说一句让他们社死的阴阳怪气话，但不能包含脏话。",
        f"请嘲讽 {target}，让他们感觉自己被内涵了，但又无可反驳。"
    ]
    return random.choice(prompts)

# 监听 #开骂 指令
enable_roast = on_command("#开骂", permission=SUPERUSER)

@enable_roast.handle()
async def _(bot: Bot, event: Event):
    global roast_enabled, roast_target, roast_count
    args = event.get_message().extract_plain_text().strip().split()

    # 解析参数
    if len(args) >= 1:
        roast_target = args[1]  # 第一个参数是目标
    if len(args) >= 2 and args[2].isdigit():
        roast_count = int(args[2])  # 第二个参数是次数
    else:
        roast_count = 5  # 默认 5 次

    roast_enabled = True
    await bot.send(event, f"🤖 阴阳怪气模式已开启，目标：{roast_target}，次数：{roast_count}！")

    # 开始自动骂人
    for _ in range(roast_count):
        if not roast_enabled:
            break  # 如果途中关闭，则停止
        await asyncio.sleep(random.randint(1, 3))  # 1-5 秒随机延迟
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个擅长阴阳怪气的AI，每次回复都要带点嘲讽，阴阳怪气但不直接骂人。"},
                {"role": "user", "content": generate_prompt(roast_target)}
            ],
            stream=False
        )
        answer = response.choices[0].message.content
        await bot.send(event, Message(answer))

    roast_enabled = False
    await bot.send(event, "🤖 阴阳怪气模式结束，目标被怼得够惨了吧！")

# 监听 #闭嘴 指令
disable_roast = on_command("#闭嘴", permission=SUPERUSER)

@disable_roast.handle()
async def _(bot: Bot, event: Event):
    global roast_enabled
    roast_enabled = False
    await bot.send(event, "🤖 阴阳怪气模式已关闭，暂时放你们一马。")
