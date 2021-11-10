from os import curdir
import requests
from utils import config
import base64
import re
import datetime
import traceback
import sqlite3

conn = sqlite3.connect('databases/lolz_market_bot.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def getXenforoCookie(proxy):
    print('parse df_id')
    cur.execute("select*from proxy where ip = ?", (proxy['http'],))
    prox = cur.fetchone()
    if not prox:
        try:
            r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'}, proxies=proxy, timeout=5)
        except:
            print("xf return")
            return None
        cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
        base64DfId = eval(cookieArray)[-1]
        res = base64.b64decode(base64DfId).decode()
        # cur.execute("insert into proxy(ip, df_id) values(?, ?)", (proxy['http'], res))
        # conn.commit()
    else:
        res = prox['df_id']
    return res

def make_coki(proxy):
    cokies = config.cokies
    asd = cokies.split(';')
    ckies = {}
    xf = getXenforoCookie(proxy)
    if xf == None:
        print("Ошибка при парсе куков")
        return None
    for qwe in asd:
        qq = qwe.split("=")
        if qq[0].split()[0] == 'df_id':
            ckies[qq[0].split()[0]] = xf
            continue
        ckies[qq[0].split()[0]] = qq[1]

    cookies = ckies

    return cookies
coki = ""
def get_url(url, proxy, remake_cookie=False):
    """ returns page(requests object) """
    print(f"""[{str(datetime.datetime.now().strftime("%H:%M:%S"))}] отправил запрос {url}""")
    global coki
    try:
        if remake_cookie:
            print("меняю куки")
            coki = make_coki(proxy)
        elif coki == "":
            print("меняю куки")
            coki = make_coki(proxy)
        url = url.replace(' ', '')
        asd = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "}, cookies=coki, timeout=5, proxies=proxy)
    except Exception as e:
        print("Ошибка при парсе страницы")
        print(traceback.format_exc())
        return None
    # print(page.cookies)
    print(f"""[{str(datetime.datetime.now().strftime("%H:%M:%S"))}] ответ от страницы получен >>>""")
    return asd

def get_post(url, data):
    """ returns page(requests object) """

    page = requests.post(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=make_coki(), data=data, timeout=5)
    return page