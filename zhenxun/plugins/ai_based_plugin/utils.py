from openai import OpenAI

from .config import API_BASE, API_KEY

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE,
)
def get_data(input_str:str) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": input_str,  
            }
        ],
        model="grok-3",
        temperature=1.1,
        
    )
    
    rst = chat_completion.choices[0].message.content
    # print(rst)
    return rst



rst_list = []

for i in range(3):
    # rst = get_data("""
    # 请根据参考以下模板生成一个名为 edab 的二次元女角色的详细描述，包含角色的外貌、性格、背景等信息。请使用中文，并确保描述生动有趣，富有创意。
    # 参考以下写法
    
    # 二次元的{姓名}，长着{脸型}，身高{身高}，{发色}{发型}，{胸部大小}，瞳色{瞳色}，{二次元属性(可多个)}属性，是{人设/背景}。

    # 确保结果在50字左右（+-10），不要输出任何其他的内容
    # """)
    rst = get_data("""按照顺序，用json格式随机生成一组二次元女生的属性给我，不要输出多余的内容:{脸型},{身高},{发色},{发型},{胸部大小},{瞳色},{二次元属性(可多个)},{人设/背景}""")
    rst_list.append(rst)

# print(rst_list)
