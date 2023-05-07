import requests
import os
import pyzbar.pyzbar as pyzbar
import random
import cv2
import zxing


# try:
#     f.write(r.content)
#     f.close()
#     解码二维码
# image = cv2.imread("qrCode/64174489.png")
# barcode = pyzbar.decode(image)
hints = zxing.ScanHints(zxing.DecodeHintType.TRY_HARDER)  
reader1 = zxing.BarCodeReader()
barcode1 = reader1.decode("qrCode/64174489.png")
print(barcode1)
# print(barcode)
# except:
    # print("ERROR")

# os.remove("qrCode/81914222.png")
# false = False
# null = None
# true = True
# msg = {"time": 1682477173, "self_id": 286081187, "post_type": "message", "sub_type": "normal", "user_id": 1308357113, "message_type": "group", "message_id": 349977218, "message": [{"type": "text", "data": {"text": "12"}}], "original_message": [{"type": "text", "data": {"text": "12"}}], "raw_message": "12", "font": 0, "sender": {"user_id": 1308357113, "nickname": "\u3000", "sex": "unknown", "age": 0, "card": "dddd", "area": "", "level": "", "role": "admin", "title": ""}, "to_me": false, "reply": null, "group_id": 717944543, "anonymous": null, "message_seq": 51041}

# # msg = json.loads("""
# # """)
# if [types['data']['url']  for types in msg['message'] if types['type']=='image']:
#     print("you")
#     print([types['data']['url']  for types in msg['message'] if types['type']=='image'][0])
# print("".join([types['data']['text']  for types in msg['message'] if types['type']=='text']))




# from nonebot.adapters.onebot.v11 import Bot, MessageEvent,Message,Event,MessageSegment

# print(MessageEvent.json())