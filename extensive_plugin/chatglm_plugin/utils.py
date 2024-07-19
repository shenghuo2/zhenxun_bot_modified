from openai import OpenAI
import openai
from .key import api_key

client = OpenAI(
    api_key=api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
) 

def GLM_standard(text:str, model:str):
    response = client.chat.completions.create(
        model=model,  # 填写需要调用的模型名称
        messages=[
            {"role": "user", "content": text},
        ],
    )
    result = f"真寻思考完毕：\n{response.choices[0].message.content}" \
            f"\n💽 本段对话使用模型: {model}" \
            f"\n✅ 本段对话使用Token: {response.usage.total_tokens}"
    return result

def chatGLM_4_standard(text:str):
    
    return GLM_standard(text,"glm-4")
# print(GLM_standard("你好是什么意思","glm-4-flash"))
def chatGLM_4_flash(text:str):
    
    return GLM_standard(text,"glm-4-flash")


def cogView_image(prompt:str):
    try:
        response = client.images.generate(
        model="cogview-3", #填写需要调用的模型名称
        prompt=prompt,
        )   
        return response.data[0].url
    except openai.BadRequestError as e:
        return str(e)
    except Exception as e:
        return str(e)
    
# print(cogView_image("变形金刚"))

# print(chatGLM_4_flash("你好是什么意思"))
def identify_img_by_glm4v(image_url:str,
                          text:str = "图里有什么") -> str:
    response = client.chat.completions.create(
        model="glm-4v",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    },
                    {
                    "type":  "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
    )

    result = f"真寻思考完毕：\n{response.choices[0].message.content}" \
            f"\n✅ 本段对话使用Token: {response.usage.total_tokens}"
    return result


# print(identify_img_by_glm4v('https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png'))

from PIL import Image
from io import BytesIO
import base64
import requests

def convert_jfif_to_base64_jpg(url):
    # 从URL获取图像
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 打开 JFIF 图像
    with Image.open(BytesIO(response.content)) as img:
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        # 创建一个 BytesIO 对象来保存图像数据
        buffer = BytesIO()
        # 将图像保存为 JPEG 格式到 BytesIO 对象
        img.save(buffer, format='JPEG')
        # 获取字节数据
        byte_data = buffer.getvalue()
        # 将字节数据编码为 base64
        base64_str = base64.b64encode(byte_data).decode('utf-8')

    return base64_str
