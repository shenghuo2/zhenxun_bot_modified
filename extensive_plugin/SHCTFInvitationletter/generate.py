# -*- coding: utf-8 -*-

import requests
from PIL import ImageFont, ImageDraw, Image, ImageOps
from io import BytesIO
import base64

sourcePath = '.\\extensive_plugin\\SHCTFInvitationletter\\'
def crop_circle_avatar(img):
    img = img.resize((350, 350), Image.ANTIALIAS)  # 将头像调整为 320, 320 大小
    bigsize = (img.size[0] * 3, img.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(img.size, Image.ANTIALIAS)
    img.putalpha(mask)
    return img

def generate_invitation(name:str,qqID:str):

    imgurl = f'http://q.qlogo.cn/headimg_dl?dst_uin={str(qqID)}&spec=640&img_type=jpg'

    response = requests.get(imgurl)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
    avatar = crop_circle_avatar(avatar)

    img = Image.open(sourcePath +"source.jpg")

    def get_text_width(name, font):
        width = 0
        has_chinese = any(ord(char) >= 128 for char in name)
        
        for char in name:
            if ord(char) >= 128:  # 中文字符
                width += 90
            else:  # 英文字符
                if has_chinese:
                    width += 30
                else:
                    width += 45
        return width

    if len(name) > 20:
        return "Error: Name is too long!", 400

    # font_pil = ImageFont.truetype("./FZXIANGSU12.TTF", 80)
    font_pil = ImageFont.truetype(sourcePath +"STXINWEI.TTF",100, encoding="unic")
    draw = ImageDraw.Draw(img)
    x0, y0 = img.size
    ascent, descent = font_pil.getsize(name)
    text_width = get_text_width(name, font_pil)
    x = x0 / 2 - ascent / 2
    # height = (img.height) / 2 - 30
    height = (img.height) / 2 - 200
    draw.text((x, height), name.encode('unicode_escape').decode('unicode_escape'), font=font_pil, fill=(94, 94, 94))

    #img.paste(avatar, (((img.width) //2 - 118),((img.height) // 2 - 300)), avatar)
    img.paste(avatar, (((img.width) //2-185),((img.height) // 2 -576 )), avatar)

    output_buffer = BytesIO()
    img.save(output_buffer, format='JPEG')
    output_buffer.seek(0)
    # img.show()
    
    return base64.b64encode(output_buffer.getvalue()).decode()

# x = generate_invitation('shenghuo2',1308357113)
# print(x)