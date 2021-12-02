import sqlite3
import time
import aiohttp
import asyncio
import traceback
from utils.utils import make_coki
from bs4 import BeautifulSoup
import requests
from utils import config
import re
import base64

cookies = "G_ENABLED_IDPS=google; xf_tfa_trust=j6AWJD-cDM6FtL5v8J0Mt20nRErnw5K2; timezoneOffset=10800,0; _ga=GA1.1.1142729890.1631613987; _ym_uid=1634806435741829229; _ym_d=1634806435; _ga_J7RS527GFK=GS1.1.1634898778.487.1.1634899585.0; xf_user=3764769,50f9ea3798690c72f00f28f1465b025e6d6dfb92; xf_logged_in=1; xf_disable_market_warning_page=1; xf_session=28865dd21e5ab33b0c16b7535ce548bd; xf_is_not_mobile=1; df_id=ec1211699c2791c82751702f5fe9baa8; xf_last_read_article_date=1636484340; xf_market_search_url=/market/user/2952337/items; xf_language_id=2; xf_market_items_viewed=18433497,22178548,22083114,21020914"
headers = {'User-Agent':'Mozilla/5.0'}



df_id = ''
def getXenforoCookie():
    global df_id
    if df_id == '':
        print('parse df')
        try:
            r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
        except:
            return None
        cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
        base64DfId = eval(cookieArray)[-1]
        res = base64.b64decode(base64DfId).decode()
        df_id = res
        print('parsed df')
        return res
    else:
        return df_id

def make_coki():
    global cookies
    cokies = cookies
    asd = cokies.split(';')
    ckies = {}
    xf = getXenforoCookie()
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

# cookie = make_coki()
async def check_account(session, link, cur, conn):
    try:
        async with session.get(link) as resp:
            assert resp.status == 200
            html = await resp.text()
    except AssertionError:
        print('Проблема с получением страницы')
        return None

    soup = BeautifulSoup(html, 'lxml')
    print(link)
    #   блок для первого этапа
    # resell_same_items = soup.find_all("div", class_="marketItemView--sameItem")
    # for item in resell_same_items:
    #     sellere = item.find_all("a", class_="username")
    #     seller = sellere[0].text
    #     if seller == 'zxxxcqq':
    #         respawn = item.find("span", class_="marketIndexItem--icon--deleted")
    #         if respawn:
    #             print(f"{link} был реснут")
    #             sql = "update accounts set sell_price = 0 where link = ?"
    #             data = (link, )
    #             try:
    #                 cur.execute(sql, data)
    #                 conn.commit()

    #             except sqlite3.Error as error:
    #                 print("Failed to insert Python variable into sqlite table", error)
    #             return
    #         resell_link = item.find("div", class_="title").find("a").get("href")
    #         resell_link = f"https://lolz.guru/{resell_link}"
            # print(resell_link)
            # sql = "update accounts set resell_link = ? where link = ?"
            # data = (resell_link, link)
            # try:
            #     cur.execute(sql, data)
            #     conn.commit()

            # except sqlite3.Error as error:
            #     print("Failed to insert Python variable into sqlite table", error)

    wee = soup.find("div", class_="marketItemView--mainInfoContainer")
    counters = wee.find_all("div", class_="marketItemView--counters")
    # otlega = counters[1].find_all("div", class_="counter")[0].text.strip().replace('\n', '').replace('Последняя активность', '')
    chasov = int(counters[1].find_all("div", class_="counter")[1].find("div", class_="label").text.strip()[:-2])

    # seller_name = soup.find("div", class_="marketItemView--sidebarUser--Username").find("a", class_="username").text
    # price = soup.find("span", class_="price").find("span", class_="value").get("data-value")
    # print(price)
    sql = "update accounts_old set hours = ? where link = ?"
    data = (chasov, link)
    try:
        cur.execute(sql, data)
        # conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    
    


async def main():

    # res = cur.fetchall()

    accs = cur.execute("select * from accounts_old").fetchall()
    links = []
    for r in accs:
        links.append(r['link'])
    
    # links = ['https://lolz.guru/market/18433517/', ]
    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        tasks = []
        ch = 4
        ll = len(links)//ch
        l = len(links)%ch

        # print(ll)
        # print(l)

        for i in range(1, ll+1):
            q = i*ch
            w = q-ch
            # print(list[w:q])
            for link in links[w:q]:
                task = asyncio.create_task(check_account(session, link, cur, conn))
                tasks.append(task)
            # print(tasks)
            try:
                await asyncio.gather(*tasks)
            except:            
                print("creah")
                print(traceback.format_exc())
                return None
            tasks = []
            time.sleep(2)

        if l > 0:
            l = -l
            for link in links[l:]:
                task = asyncio.create_task(check_account(session, link, cur, conn))
                tasks.append(task)
        
            try:
                await asyncio.gather(*tasks)
            except:
                print("creah")
                print(traceback.format_exc())
                return None
            tasks = []
            time.sleep(2)
    
    conn.commit()



if __name__ == "__main__":
    # while True:
    #     try:
    #         # asyncio.run(main())
    #         loop = asyncio.get_event_loop()
    #         loop.run_until_complete(main())
    #     except:
    #         print(traceback.format_exc())
    #         print('creash')
    #         time.sleep(5)
    # asyncio.run(main())

    conn = sqlite3.connect('databases/market.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("select * from accounts_old where id <= 249 and sell_price = 0")
    res = cur.fetchall()
    print(len(res))
    buy = 0
    sell = 0
    income = 0
    for r in res:
        buy += int(r['buy_price'])
        # print(f"{r['link']} {r['sell_price']}")
        sell += int(r['sell_price'])
    income = sell - buy

    print(f"{sell/len(res)}  ")

    # print(f"invested = {buy}")
    # print(f"got back = {sell}")
    # print(f"\nincome = {sell-buy}")