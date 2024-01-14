import errno
import json
import random
import re
import requests
import base64
# from configs.path_config import IMAGE_PATH

# 从关键词获取pid
def getPid(tag):
    
    # 获取json  待添加多页功能
    url = "https://www.pixiv.net/ajax/search/artworks/" + str(tag)
    heads = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    proxy = {
            'https': 'http://127.0.0.1:10809',
            'http': 'http://127.0.0.1:10809',
        }
    setuList = requests.get(url=url,headers=heads,proxies=proxy).content
    # print(setuList)
    setuList = json.loads(setuList)
    # 判断是否存在数据
    if setuList['body']['illustManga']['total'] == 0:
        return "None"
    # 随机获取pid
    setuCount = len(setuList['body']['illustManga']['data'])
    # 生成随机数
    num = random.randint(0,setuCount - 1)
    setuDict = setuList['body']['illustManga']['data'][num]
    return setuDict

def getCount(tag):
    url = "https://www.pixiv.net/ajax/search/artworks/" + str(tag)
    heads = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    proxy = {
            'https': 'http://127.0.0.1:10809',
            'http': 'http://127.0.0.1:10809',
        }
    setuList = requests.get(url=url,headers=heads,proxies=proxy).content
    # print(setuList)
    setuList = json.loads(setuList)
    return setuList['body']['illustManga']['total']

# 从pid获取图片的base数据
def pidToImagebase(PID):

    url = f'https://www.pixiv.net/ajax/illust/{PID}/pages'
    heads = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        }
    proxy = {
                'https': 'http://127.0.0.1:10809',
                'http': 'http://127.0.0.1:10809',
            }
    # 获取二进制数据
    PicList1 = requests.get(url,headers=heads,proxies=proxy).content
    PicList = json.loads(PicList1)
    PicUrl = PicList['body'][0]['urls']['original'].replace('i.pximg.net','i.pixiv.re')
    # print(PicUrl)
    # print(type(PicList))
    
    PicDataList = []
    for i in range(len(PicList['body'])):
        PicUrl = PicList['body'][i]['urls']['original'].replace('i.pximg.net','i.pixiv.re')
        print(PicUrl)
        get_data = requests.get(PicUrl).content
        get_data_base64 = str(base64.b64encode(get_data))[2:-1:]
        PicDataList.append(get_data_base64)
    # # 对被屏蔽的色情内容进行挽救（？）
    # print(PicDataList)
    # print('got')
    # get_data_base64 = str(base64.b64encode(get_data))[2:-1:]
    # # print(get_data_base64[:100])
    return PicDataList

# pidToImagebase("100083845")
def pidToImageUrl(PID):

    url = f'https://www.pixiv.net/ajax/illust/{PID}/pages'
    heads = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        "Referer": "https://www.pixiv.net",
        }
    proxy = {
                'https': 'http://127.0.0.1:10809',
                'http': 'http://127.0.0.1:10809',
            }
    # 获取二进制数据
    PicList1 = requests.get(url,headers=heads,proxies=proxy).content
    # print(PicList1)
    PicList = json.loads(PicList1)
    
    PicUrlList = []
    # if 
    for i in range(len(PicList['body'])):
        PicUrl = PicList['body'][i]['urls']['original'].replace('i.pximg.net','i.pixiv.re')
        # print(PicUrl)
        PicUrlList.append(PicUrl)
    # print(PicUrlList)
    return PicUrlList

# pidToImageUrl('100464008')

# def pidToImageUrl(PID):

#     url = f'https://www.pixiv.net/ajax/illust/{PID}/pages'
#     heads = {
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
#         "Referer": "https://www.pixiv.net",
#         }
#     proxy = {
#                 'https': 'http://127.0.0.1:10809',
#                 'http': 'http://127.0.0.1:10809',
#             }
#     # 获取二进制数据
#     PicList1 = requests.get(url,headers=heads,proxies=proxy).content
#     # print(PicList1)
#     PicList = json.loads(PicList1)
#     PicUrlList = []
#     # if PicList['error'] == True:
#     #     R18Url = pidTorR18Image(PID)
#     #     if R18Url =="not exist":
#     #         return
#     #     else:
#     #         PicUrlList.append(R18Url)
#     if len(PicList['body']) == 1:
#         PicUrl = f"https://pixiv.re/{PID}.png"
#         PicUrlList.append(PicUrl)
#     else:
#         for i in range(len(PicList['body'])):
#             PicUrl = f"https://pixiv.re/{PID}-{i+1}.png"
#             PicUrlList.append(PicUrl)
#     # print(PicUrlList)
#     return PicUrlList

# print(pidToImageUrl('100464008'))

# def pidTorR18Image(PID):

#     url = "https://pixiv.shojo.cn/" + str(PID)
#     # 获取二进制数据
#     get_data = requests.get(url).content
#     # print(get_data)
#     # 对被屏蔽的色情内容进行挽救（？）
#     if "\\xe8\\xaf\\xa5\\xe5\\x9b\\xbe\\xe7\\x89\\x87\\xe5\\xb7\\xb2\\xe8\\xa2\\xab\\xe5\\xb1\\x8f\\xe8\\x94\\xbd" in str(get_data):
#         # return "r18"
#         # 正则表达式匹配
#         reurl = re.compile(r'<p><a href="(.*?)" target="_blank">')
#         reurl = reurl.findall(str(get_data))[0]
#         return reurl
#         # get_data = requests.get(reurl).content
#         # print(get_data)
#     elif "\\xe8\\xaf\\xa5\\xe5\\x9b\\xbe\\xe7\\x89\\x87\\xe4\\xb8\\x8d\\xe5\\xad\\x98\\xe5\\x9c\\xa8\\xef\\xbc\\x8c" in str(get_data):
#         return "not exist"
    
#     else:
#         get_data_base64 = str(base64.b64encode(get_data))[2:-1:]
#         return get_data_base64

# pidToImageUrl("996388111")

# def pidToTags(PID):

#     url = f'https://api.pixivel.moe/v2/pixiv/illust/search/{PID}?page=0'
#     heads = {
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
#         'Referer': 'https://pixivel.moe/',
#         }
#     # 获取二进制数据
#     PicList1 = requests.get(url,headers=heads).content
#     print(PicList1)
#     PicList = json.loads(PicList1)
#     print(PicList)
#     PicUrl = PicList['data']['title']
#     print(PicUrl)
#     # return get_data_base64

# pidToTags("草神")

def pidQueryTags(PID:str):
    url = f'https://www.pixiv.net/ajax/illust/{PID}'
    heads = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        }
    proxy = {
                'https': 'http://127.0.0.1:10809',
                'http': 'http://127.0.0.1:10809',
            }
    # 获取二进制数据
    PicList1 = requests.get(url,headers=heads,proxies=proxy).content
    PicList = json.loads(PicList1)
    # if PicList['error'] != True:
    # print( PicList['body']['tags']['tags'])
    return PicList
    # tagList = ""
    # for tags in PicList['body']['tags']['tags']:
    #     # print(i['tag'],end=',')
    #     tagList += tags['tag'] + ","    
    # tagList = tagList[:-1]

    # print(tagList)
        # print(f"{PicList['body']['tags']['tags'][i]['tag']}",end=',')
import os
from threading import Thread
# print(pidQueryTags("99679655"))
# 异步调用
def async_call(fn):
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper

image_path = "C:\\Users\\Administrator\\Desktop\\new_bot\\zhenxun_bot\\resources\\image\\xin_setu"
@async_call
def storagePic(UrlList:list):
    # for i,PicUrl in enumerate(UrlList):
    #     print(i,PicUrl)
    for PicUrl in UrlList:
        filename = os.path.basename(PicUrl) 
        if not os.path.exists(f"{image_path}\\{filename}"):
            fb = requests.get(url=PicUrl).content
            with open(f"{image_path}\\{filename}",'wb') as f:
                f.write(fb)
            f.close()
            
    print("下载完成")

# storagePic(pidToImageUrl("100291134"))


import os

# 下载文件到本地的函数
# def download(fileUrl):    
#     # 获取网络文件的文件名
#     filename = os.path.basename(fileUrl) 
#     fb = requests.get(url=fileUrl).content
#     # img=rsp.read()
#     with open(filename,'wb') as f:
#         f.write(fb)

# download("https://pixiv.re/100305242.png")

# 两个合起来
def tagToImage(tag):
    if (tag.isnumeric()&(len(tag)==8))|(tag.isnumeric()&(len(tag)==9)):
        imgUrl = pidToImageUrl(tag)
        setuInfoList = pidQueryTags(tag)
        # print(type(setuInfoList['error']))
        if (setuInfoList['error'] == False) & (imgUrl == []):
            for pageCount in range(setuInfoList['body']['pageCount']):
                imgUrl.append(setuInfoList['body']['urls']['original'].replace('i.pximg.net','i.pixiv.re').replace('_p0',f'_p{pageCount}'))
        storagePic(imgUrl)
        # print(imgUrl)
        return setuInfoList,imgUrl
    else:
        setuDict = getPid(tag)
        if setuDict == "None" :
            return "1"
        imgUrl = pidToImageUrl(setuDict['id'])
        return setuDict, imgUrl
# setuInfoList,imgUrl = tagToImage("96287848")
# print(imgUrl)
def getSetuList(tag):
    
    # 获取json  待添加多页功能
    url = "https://www.pixiv.net/ajax/search/artworks/" + str(tag)
    heads = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    }
    proxy = {
            'https': 'http://127.0.0.1:10809',
            'http': 'http://127.0.0.1:10809',
        }
    setuList = requests.get(url=url,headers=heads,proxies=proxy).content
    setuList = json.loads(setuList)
    # 判断是否存在数据
    if setuList['body']['illustManga']['total'] < 5:
        return "None"
    # 随机获取pid
    setuCount = len(setuList['body']['illustManga']['data'])
    # 生成随机数
    num = random.randint(0,setuCount - 5)
    setuDict = []
    # print(setuCount)
    # print(num)
    for i in range(num,num+5):
        setuDict.append([setuList['body']['illustManga']['data'][i]['id'] , str(setuList['body']['illustManga']['data'][i]['url']).replace('i.pximg.net','i.pixiv.re').replace('/c/250x250_80_a2','').replace('/c/250x250_80_a2/custom-thumb','img-master').replace('custom1200','master1200').replace('square1200','master1200')])
        # print(i)
    # print(setuDict)
    # for i in setuDict:
    #     print(i[0],i[1])
    return setuDict

# tag = "萝莉 00user"
# setuList = getSetuList(tag)
# # # print(setuList)
# for i in setuList:
#     print(i)
# tag = "100305242"
# setuInfoList,imageDict = tagToImage(tag)
# print(setuInfoList)
# pidToImagebase(100305242)

# sou = tagToImage("蝠")
# if len(sou) == 1:
#     print("怪")
# else:
#     print(sou[0])
#     print(sou[1])

# tag = "瓜"
# url = "https://www.pixiv.net/ajax/search/artworks/" + str(tag)
# heads = {
# 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
# }
# proxy = {
#         'https': 'http://127.0.0.1:10809',
#         'http': 'http://127.0.0.1:10809',
#     }
# setuList = requests.get(url=url,headers=heads,proxies=proxy).content
# setuList = json.loads(setuList)
# setu = setuList['body']['illustManga']['data'][15]
# print(setu)
# print(setuDict['url'])
# url = str(setuDict['url']).replace('i.pximg.net','i.pixiv.re').replace('c/250x250_80_a2/img-master','img-original').replace('p0_square1200','p0')
# print(url)
# print(setu)

# str = f"pid：{setuDict['id']}\n作品名：{setuDict['title']}\n"
# str += f"标签：{','.join(setuDict['tags'])}\n分辨率：{setuDict['height']}x{setuDict['width']}"
# print(str)


# str1 = ','.join(setuList['body']['illustManga']['data'][15]['tags'])
# print(str1)

# tag = "俄"
# search_result = tagToImage(tag)
# if len(search_result) == 1:
#     print("怪")
# image = search_result[1]
# setuDict = search_result[0]
# str = f"pid：{setuDict['id']}\n作品名：{setuDict['title']}\n"
# str += f"标签：{','.join(setuDict['tags'])}\n分辨率：{setuDict['height']}x{setuDict['width']}"
# print(str)