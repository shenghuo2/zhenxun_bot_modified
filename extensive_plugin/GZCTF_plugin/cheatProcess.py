import requests
import json


def removeTheEndSlash(url:str):
    if url.endswith('/') or url.endswith('\\'):
        return url[:-1]
    else:
        return url

def cheatDetect(GZCTF_Token:str, platURL:str, GameID)->str:
    """
    GZCTF_Token:需要Monitor级别才能查询作弊信息
    platURL:不需要在最后加\\
    GameID:数字
    """

    cookies = {
        'GZCTF_Token': GZCTF_Token,
    }
    platURL = removeTheEndSlash(platURL)

    response = requests.get(f'{platURL}/api/game/{GameID}/cheatinfo', cookies=cookies, verify=False)

    cheatinfo = json.loads(response.text)
    message = ""
    cheat_list = {}
    for i in cheatinfo:
        # print()
        if i['ownedTeam']['status'] == 'Accepted':
            if i['submitTeam']['team']['name'] == "Nixiak":
                continue
            if i['ownedTeam']['id'] in cheat_list and cheat_list[i['ownedTeam']['id']] == i['submitTeam']['id']:
                continue
            cheat_list[i['ownedTeam']['id']] = i['submitTeam']['id']
            message += ("检测到未处理的作弊!!!\n" \
            +f"检测时间: {i['submission']['time']}\n"\
            +f"题目信息：{i['submission']['challenge']}，flag：{i['submission']['answer']}\n" \
            +f"被提交flag的队伍：{i['ownedTeam']['team']['name']}\n提交flag的队伍：{i['submitTeam']['team']['name']}\n"\
            +f"提交者{i['submission']['user']}\n" \
            )
            # print(i)
            # print(message)
    # print(cheat_list)
    if message != "":
        return message
    else:
        return "暂无未处理的作弊信息\n"




def banCheatTeam(GZCTF_Token:str, platURL:str, GameID):
    """
    GZCTF_Token:需要Admin级别才能封禁队伍
    platURL:不需要在最后加\\
    GameID:数字
    """
    cookies = {
        'GZCTF_Token': GZCTF_Token,
    }
    platURL = removeTheEndSlash(platURL)
    response = requests.get(f'{platURL}/api/game/{GameID}/cheatinfo', cookies=cookies, verify=False)
    
    cheatinfo = json.loads(response.text)
    cheat_list = {}
    message = "封禁队伍："
    
    for infos in cheatinfo:
        if infos['ownedTeam']['status'] == 'Accepted':
            if infos['submitTeam']['team']['name'] == "Nixiak":
                continue
            if infos['ownedTeam']['id'] in cheat_list and cheat_list[infos['ownedTeam']['id']] == infos['submitTeam']['id']:
                continue
            cheat_list[infos['ownedTeam']['id']] = infos['submitTeam']['id']
            unprocessedCheatingTeamID = str(infos['ownedTeam']['id'])
            
        
            requests.put(
                f'http://shctf.club:8000/api/admin/participation/{unprocessedCheatingTeamID}/Suspended',
                cookies=cookies,
                verify=False,
            )
            unprocessedCheatingTeamID = str(infos['submitTeam']['id'])
            

            requests.put(
                f'http://shctf.club:8000/api/admin/participation/{unprocessedCheatingTeamID}/Suspended',
                cookies=cookies,
                verify=False,
            )
            message += f"{infos['ownedTeam']['team']['name']}\t{infos['submitTeam']['team']['name']}\t\n"
    
    if message != "封禁队伍：":
        return message
    else:
        return "暂无未处理的作弊信息\n"


def SHCTF_team_cheat_Detect():
    """
    为SHCTF写的处理
    """

    token = 'CfDJ8H0VcAGFzb9PkHRVJnzmzQMFxYIRvgJBjggLo4r9SqmLdQEZAosgDBpqCE4xaU8KidQx2dqxDUJcO9cq6Psu_JTFjM1oA4HtKW6MxhL4V9ckA6cyO_3JYaR4HmIaY5d-5MOuWeXgrBm97N9NDTWvXnGreM1PIr0uVEMd1seZda_TUKntWCmxOtlNLkQk4LrU2EMS7pzvd5QeCbwoZ12p08FXdOwaFHoh4U56qSUXbjbFJYuhu3NMfuROeWK8yYMvlglrVDbn7Ad-1ypi_YcdDPWdHwLzJGKJwcNQGjR2mMPcv5xns5w4cDXI9grN0P7Y7qWwYu9rSRI7eRnh9F5eHmJY2TVBRKTUmiquv6PySmj31iGd9fZXWfwu8xTElkNnTE7u90hyJVjh8I1wAnlrDuiMGH4jLrS-MaysaPcs3cRcn0xk-gpOKi5mBkxgNcQXQdHvUDUKp3Y2jfeZ6M0DUGwp5BQpt5Hu3H7Fq4IQYKRhjuCbpPyMXj45vjGwJeu4u0JRT6sxAgAlVpNB6F-CqKrmtBxz-fggg6cDnBVDuIdOjUpUMLAIqun9tDXfOJ2EBu9Kismr5SolJq_DVTwAod7_u_PNIdyGUsgCC_VALIxeFH9nCxMcyE1DiVXJYGD8GiyYWHmZ62z0KyokyZkXMZMcIlO_bbTMNQMuuIpfMEKuWdakaEWy3o61gkUdA-2EiuIt7OE4Uk4hNNzgkzgEghfTks55V2AR6_CmMdj24zEN'
    platURL = 'http://shctf.club:8000'
    messages = ""
    messages += "校内赛道未处理的作弊情况：\n"
    messages += cheatDetect(token, platURL,1)
    messages += "\n校外赛道未处理的作弊情况：\n"
    messages += cheatDetect(token, platURL,2)
    return messages


def SHCTF_ban_cheat_team():
    """
    为SHCTF写的处理
    """
    token = 'CfDJ8H0VcAGFzb9PkHRVJnzmzQMFxYIRvgJBjggLo4r9SqmLdQEZAosgDBpqCE4xaU8KidQx2dqxDUJcO9cq6Psu_JTFjM1oA4HtKW6MxhL4V9ckA6cyO_3JYaR4HmIaY5d-5MOuWeXgrBm97N9NDTWvXnGreM1PIr0uVEMd1seZda_TUKntWCmxOtlNLkQk4LrU2EMS7pzvd5QeCbwoZ12p08FXdOwaFHoh4U56qSUXbjbFJYuhu3NMfuROeWK8yYMvlglrVDbn7Ad-1ypi_YcdDPWdHwLzJGKJwcNQGjR2mMPcv5xns5w4cDXI9grN0P7Y7qWwYu9rSRI7eRnh9F5eHmJY2TVBRKTUmiquv6PySmj31iGd9fZXWfwu8xTElkNnTE7u90hyJVjh8I1wAnlrDuiMGH4jLrS-MaysaPcs3cRcn0xk-gpOKi5mBkxgNcQXQdHvUDUKp3Y2jfeZ6M0DUGwp5BQpt5Hu3H7Fq4IQYKRhjuCbpPyMXj45vjGwJeu4u0JRT6sxAgAlVpNB6F-CqKrmtBxz-fggg6cDnBVDuIdOjUpUMLAIqun9tDXfOJ2EBu9Kismr5SolJq_DVTwAod7_u_PNIdyGUsgCC_VALIxeFH9nCxMcyE1DiVXJYGD8GiyYWHmZ62z0KyokyZkXMZMcIlO_bbTMNQMuuIpfMEKuWdakaEWy3o61gkUdA-2EiuIt7OE4Uk4hNNzgkzgEghfTks55V2AR6_CmMdj24zEN'
    platURL = 'http://shctf.club:8000'
    messages = ""
    messages += "校内赛道的作弊情况：\n"
    messages += banCheatTeam(token, platURL,1)
    messages += "\n校外赛道的作弊情况：\n"
    messages += banCheatTeam(token, platURL,2)
    messages += "现已对以上队伍进行封禁"
    return messages


# def 
def statistCheatDetect(GZCTF_Token:str, platURL:str, GameID)->str:
    """
    GZCTF_Token:需要Monitor级别才能查询作弊信息
    platURL:不需要在最后加\\
    GameID:数字
    """

    cookies = {
        'GZCTF_Token': GZCTF_Token,
    }
    platURL = removeTheEndSlash(platURL)

    response = requests.get(f'{platURL}/api/game/{GameID}/cheatinfo', cookies=cookies, verify=False)

    cheatinfo = json.loads(response.text)
    message = ""
    cheat_list = {}
    for i in cheatinfo:
        # print()
        # if i['ownedTeam']['status'] == 'Accepted':
            # if i['submitTeam']['team']['name'] == "Nixiak":
                # continue
        if i['ownedTeam']['id'] in cheat_list and cheat_list[i['ownedTeam']['id']] == i['submitTeam']['id']:
            continue
        cheat_list[i['ownedTeam']['id']] = i['submitTeam']['id']
        # message += ("检测到未处理的作弊!!!\n" \
        # +f"检测时间: {i['submission']['time']}\n"\
        # +f"题目信息：{i['submission']['challenge']}，flag：{i['submission']['answer']}\n" \
        # +f"被提交flag的队伍：{i['ownedTeam']['team']['name']}\n提交flag的队伍：{i['submitTeam']['team']['name']}\n"\
        # +f"提交者{i['submission']['user']}\n" \
        # )
    cheats_list = set( list(cheat_list.keys()) + list(cheat_list.values()))
    # print((cheats_list))
    # print(len((cheats_list)))
    # print(', '.join([str(i) for i in cheats_list]))
    
    message += "目前作弊队伍ID列表为:" + ', '.join([str(i) for i in cheats_list])
    message += "\n目前作弊队伍数量为:" + str(len((cheats_list)))
    # print(list(cheat_list.keys()) + list(cheat_list.values()))
            # print(i)
            # print(message)
    # print(cheat_list)
    if message != "":
        return message
    else:
        return "暂无作弊队伍信息\n"

def SHCTF_team_static_cheat_Detect():
    """
    为SHCTF写的处理
    """

    token = 'CfDJ8H0VcAGFzb9PkHRVJnzmzQMFxYIRvgJBjggLo4r9SqmLdQEZAosgDBpqCE4xaU8KidQx2dqxDUJcO9cq6Psu_JTFjM1oA4HtKW6MxhL4V9ckA6cyO_3JYaR4HmIaY5d-5MOuWeXgrBm97N9NDTWvXnGreM1PIr0uVEMd1seZda_TUKntWCmxOtlNLkQk4LrU2EMS7pzvd5QeCbwoZ12p08FXdOwaFHoh4U56qSUXbjbFJYuhu3NMfuROeWK8yYMvlglrVDbn7Ad-1ypi_YcdDPWdHwLzJGKJwcNQGjR2mMPcv5xns5w4cDXI9grN0P7Y7qWwYu9rSRI7eRnh9F5eHmJY2TVBRKTUmiquv6PySmj31iGd9fZXWfwu8xTElkNnTE7u90hyJVjh8I1wAnlrDuiMGH4jLrS-MaysaPcs3cRcn0xk-gpOKi5mBkxgNcQXQdHvUDUKp3Y2jfeZ6M0DUGwp5BQpt5Hu3H7Fq4IQYKRhjuCbpPyMXj45vjGwJeu4u0JRT6sxAgAlVpNB6F-CqKrmtBxz-fggg6cDnBVDuIdOjUpUMLAIqun9tDXfOJ2EBu9Kismr5SolJq_DVTwAod7_u_PNIdyGUsgCC_VALIxeFH9nCxMcyE1DiVXJYGD8GiyYWHmZ62z0KyokyZkXMZMcIlO_bbTMNQMuuIpfMEKuWdakaEWy3o61gkUdA-2EiuIt7OE4Uk4hNNzgkzgEghfTks55V2AR6_CmMdj24zEN'
    platURL = 'http://shctf.club:8000'
    messages = ""
    messages += "校内赛道的作弊情况：\n"
    messages += statistCheatDetect(token, platURL,1)
    messages += "\n校外赛道的作弊情况：\n"
    messages += statistCheatDetect(token, platURL,2)
    return messages

print(SHCTF_team_static_cheat_Detect())