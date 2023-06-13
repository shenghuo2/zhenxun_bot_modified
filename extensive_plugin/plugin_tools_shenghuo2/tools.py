import uuid
from datetime import datetime

def CET4():
    today = datetime.today()
    if today > datetime(today.year, 6, 17):

        future = datetime.strptime(f'{today.year}-12-10 09:00:00','%Y-%m-%d %H:%M:%S')
    else:
        future = datetime.strptime(f'{today.year}-06-17 09:00:00','%Y-%m-%d %H:%M:%S')
    #当前时间
    now=datetime.now()
    #时间差
    delta = future-now
    # 这些好像没用上吧，是chatgpt写的
    # hour = delta.seconds/60/60
    # minute = (delta.seconds - hour*60*60)/60
    # seconds = delta.seconds-hour*60*60 - minute*60
    print_now = now.strftime('%Y-%m-%d %H:%M:%S')

    return (f"现在是北京时间: ,{print_now}\n距离英语四级笔试考试还有：{delta.days}天")

def gen_flag():
    return "flag{" + str(uuid.uuid4()) + "}"