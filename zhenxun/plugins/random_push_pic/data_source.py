import requests

def get_image_from_lolicon_app_api():
    # 你可以替换成任何你需要的图片API URL
    url = "https://api.lolicon.app/setu/v2?tag=%E3%83%AD%E3%83%AA"  # 替换为你自己的 Unsplash API Key
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["data"][0]['urls']["original"].replace("i.pixiv.re","i.yuki.sh")
    return None

def get_image_from_lolicon_api():
    # 你可以替换成任何你需要的图片API URL
    url = "https://www.loliapi.com/bg/?type=url"  # 替换为你自己的 Unsplash API Key
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text
        return data
    return None

def get_image_from_anosu_top_api():
    # 你可以替换成任何你需要的图片API URL
    url = "https://image.anosu.top/pixiv/json?keyword=%E3%83%AD%E3%83%AA&proxy=i.yuki.sh"  # 替换为你自己的 Unsplash API Key
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]['url']
    return None

# print(get_image_from_anosu_top_api())


