from typing import Dict, Any, Optional
from zhenxun.services.log import logger
from zhenxun.utils.http_utils import AsyncHttpx


# 固定的用户信息
USERS = {
    "东洋雪莲": 1060544882,
    "東雪蓮Official": 1437582453
}

# B站认证信息
BILI_COOKIES = {
    'buvid3': 'C5B1A7D1-3C34-F9FB-4A7C-4DAC6FA2644F29011infoc',
    'b_nut': '1724600929',
    '_uuid': '9ECB7DCE-21062-C57B-A2F10-EEA5E4B2ED6A29096infoc',
    'enable_web_push': 'DISABLE',
    'DedeUserID': '85894935',
    'DedeUserID__ckMd5': 'a2fd3f886169267b',
    'LIVE_BUVID': 'AUTO2117246010537149',
    'rpdid': '0zbfvRTQCK|QKeaILDc|4v7|3w1SIhnz',
    'hit-dyn-v2': '1',
    'buvid_fp_plain': 'undefined',
    'header_theme_version': 'CLOSE',
    'buvid4': '01579278-AC9C-4B0C-9C62-46BD1007E2BD30197-024082515-gBUeJlaoY4hJPWElx91%2BZr0KVEm9trCPNvjZVidwcr1uaYBVPcpYWvJ9blqRGV%2Fk',
    'deviceFingerprint': '2ff12cc803bce5ab881aaf892c122338',
    'match_float_version': 'ENABLE',
    'kfcSource': 'cps_comments_1265680561_cont-1-113877199099777',
    'msource': 'cps_comments_1265680561_cont-1-113877199099777',
    'enable_feed_channel': 'ENABLE',
    'timeMachine': '0',
    'share_source_origin': 'QQ',
    'CURRENT_QUALITY': '112',
    'bp_t_offset_85894935': '1071284647440154624',
    'SESSDATA': '30ff7e93%2C1763990533%2Cea783%2A51CjBrWa14hAjbFY5lcuTwE_nUcqqOQ_uf4-aaRJtOilMeEdrA6D5Sze3mxn9axMTc3hISVkowRFRmMzNfWlNCWFktZUo3SUVfUl9Ia09xUkp1cVp3eU81akpHWUJUU3UtbUlsT2tvWUc4d0s0RmpWcVdseWtjOUpiR2lhUmYxUlExOGRJRUtJeXZnIIEC',
    'bili_jct': '1a11035fd37f1a95ca9236870a896cdd',
    'sid': '6foodeg0',
    'PVID': '1',
    'home_feed_column': '4',
    'browser_resolution': '1232-828',
    'bili_ticket': 'eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDg3ODQ1NTMsImlhdCI6MTc0ODUyNTI5MywicGx0IjotMX0.RB8CxOor13WdTAQfiLy03n1OdDq4ZOET1G7GjNoK4eI',
    'bili_ticket_expires': '1748784493',
    'fingerprint': '3001f87a2fdc27ae692f05ba05fb8ce7',
    'CURRENT_FNVAL': '2000',
    'buvid_fp': '9d0d8484faaa52e1cc9e14633d7e9d6a',
    'b_lsid': 'E3A5FB83_19724327079',
    'bsource': 'search_bing',
}

BILI_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not.A/Brand";v="99", "Chromium";v="136"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
}


class SnowLotusComparator:
    """雪莲粉丝数比较器"""
    
    @staticmethod
    async def get_user_stat(mid: int) -> Optional[Dict[str, Any]]:
        """
        获取用户统计信息
        :param mid: B站用户ID
        :return: 用户统计信息
        """
        url = "https://api.bilibili.com/x/relation/stat"
        params = {"vmid": mid}
        
        try:
            response = await AsyncHttpx.get(
                url, 
                params=params,
                headers=BILI_HEADERS,
                cookies=BILI_COOKIES,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return data.get("data")
                else:
                    logger.warning(f"获取用户{mid}统计信息失败: {data.get('message')}")
            else:
                logger.error(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"获取用户{mid}统计信息异常: {e}")
        return None
    
    @classmethod
    async def compare_followers(cls) -> str:
        """
        比较两个雪莲的粉丝数
        :return: 比较结果
        """
        results = {}
        
        # 获取两个用户的粉丝数
        for name, mid in USERS.items():
            try:
                stat = await cls.get_user_stat(mid)
                if stat:
                    results[name] = {
                        "mid": mid,
                        "follower": stat.get("follower", 0),
                        "following": stat.get("following", 0)
                    }
                else:
                    logger.error(f"获取 {name} 的数据失败")
                    return f"获取 {name} 的数据失败"
            except Exception as e:
                logger.error(f"处理用户 {name} 时发生错误: {e}")
                return f"处理用户 {name} 时发生错误: {str(e)}"
        
        if len(results) != 2:
            return "数据获取不完整"
        
        # 安全地获取用户数据
        user_keys = list(USERS.keys())
        dongyang_key = user_keys[0]  # "东洋雪莲"
        dongxue_key = user_keys[1]   # "東雪蓮Official"
        
        if dongyang_key not in results or dongxue_key not in results:
            missing_users = []
            if dongyang_key not in results:
                missing_users.append(dongyang_key)
            if dongxue_key not in results:
                missing_users.append(dongxue_key)
            return f"缺少用户数据: {', '.join(missing_users)}"
        
        dongyang = results[dongyang_key]
        dongxue = results[dongxue_key]
        
        follower_diff = dongyang["follower"] - dongxue["follower"]
        
        # 构建结果消息
        msg = "🌸 雪莲粉丝数对比 🌸\n\n"
        msg += f"🔹 东洋雪莲: {dongyang['follower']:,} 粉丝\n"
        msg += f"🔹 東雪莲Official: {dongxue['follower']:,} 粉丝\n\n"
        
        if follower_diff > 0:
            msg += f"📊 东洋雪莲领先 {follower_diff:,} 粉丝"
        elif follower_diff < 0:
            msg += f"📊 東雪莲Official领先 {abs(follower_diff):,} 粉丝"
        else:
            msg += "📊 两人粉丝数相同！"
        
        # 计算百分比差距
        if dongxue["follower"] > 0:
            percentage = abs(follower_diff) / dongxue["follower"] * 100
            msg += f" ({percentage:.2f}%)"
        
        return msg


# 导出函数
async def get_snow_lotus_comparison() -> str:
    """获取雪莲粉丝数比较"""
    try:
        return await SnowLotusComparator.compare_followers()
    except Exception as e:
        logger.error(f"雪莲粉丝对比过程中发生错误: {e}")
        return f"比较过程中发生错误: {str(e)}"