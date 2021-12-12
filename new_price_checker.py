import traceback
import time
import aiohttp
import requests
import base64, re
import asyncio
import json
from bs4 import BeautifulSoup
from utils import config
import sqlite3
from utils.utils import get_url
import telebot

def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    soup = BeautifulSoup(asd.text, 'html.parser')
    xftoken = soup.find('input', {'name':'_xfToken'})['value']
    print('token = %s' % xftoken)

    return xftoken

xftoken = parse_xftoken()

bot = telebot.TeleBot(config.market_bot_token)

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ids = [config.telegram_id, "1243095585", "473485315", "578827447"]

def getXenforoCookie():
    r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    res = base64.b64decode(base64DfId).decode()
    return res

def send_notification(ids='', link='', first_price='', new_price='', system=False, msg='', tt=""):
    if system:
        bot.send_message(config.telegram_id, msg)
        return
    try:
        for id in ids:
            bot.send_message(id, "%s цена изменена с %s на %s %s" % (link, first_price, new_price, tt))
    except Exception as e:
        print(traceback.format_exc())
        print("ошибка при отправке оповещения в телеграм")


def make_coki():
    cokies = config.cokies
    asd = cokies.split(';')
    ckies = {}
    for qwe in asd:
        qq = qwe.split("=")
        if qq[0].split()[0] == 'df_id':
            ckies[qq[0].split()[0]] = getXenforoCookie()
            continue
        ckies[qq[0].split()[0]] = qq[1]

    cookies = ckies

    return cookies


cookies = make_coki()
# print(cookies)
headers = {'User-Agent':'Mozilla/5.0'}

def set_account_status(link, status):
    sql = "update accounts set status = ? where link = ?"
    data = (int(status), link)
    print(data)
    try:
        cur.execute(sql, data)
        conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

def check_del(soup, link):
    asd = soup.find("label", class_="OverlayCloser")

    if asd:
        print("объявление удалено")
        set_account_status(link, 3)

        return 0
    
    return 1

def check_account_bought(soup):
    try:
        # soup = BeautifulSoup(get_url(link).text, 'html.parser')
        buy_button = soup.find("a", class_="marketViewItem--buyButton")
        if buy_button:
            return False

        bron = soup.find("span", class_="disabled")
        if bron:
            return 2

        return 1
    except Exception as e:
        print("ошибка при получении цены")
        # bot.send_message(config.telegram_id, 'поломалось что то')
        print(traceback.format_exc())

        return None

def book_account(link, price, soup):

    buy_button = soup.find_all("a", class_="marketViewItem--buyButton")
    if len(buy_button) > 1:
        return 1

    market_id = link.split('/')[-2]
    linkk = f"https://lolz.guru/market/{market_id}/balance/check?price={price}&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={xftoken}&_xfResponseType=json"
    # print(linkk)
    asd = get_url(linkk)
    answer = json.loads(asd.text)

    return answer

def get_price(soup):
    try:
        price = soup.find("span", class_="price").text.split()
        price = ''.join(price)
        price = int(price)

        return price
    except Exception as e:
        print("ошибка при получении цены")
        try:
            bot.send_message(config.telegram_id, 'поломалось что то')
        except:
            pass
        print(traceback.format_exc())

        return None

def change_price(link, new_price):
    sql = "update accounts set first_price = ? where link = ?"
    data = (new_price, link)

    try:
        cur.execute(sql, data)
        conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

async def check_account(session, link, ids):
    html = ""
    try:
        async with session.get(link[0], verify_ssl=False) as resp:
            assert resp.status == 200

            html = await resp.text()
    except Exception as e:
        print(traceback.format_exc())
        return None

    soup = BeautifulSoup(html, 'html.parser')
    username = soup.find("a", class_="username")
    if not username:
        return None

    if not check_del(soup, link[0]):
        return
    bought = check_account_bought(soup)
    price = get_price(soup)
    if bought == 1:
        print("аккаунт был куплен, ставлю статус 1 %s " % link[0])
        set_account_status(link[0], 1)
        return
    tt = ""
    if bought == 2:
        tt = "(забронирован)"
    changed = False
    if price != int(link[1]):
        print("price changed")
        send_notification(ids, link[0], link[1], price, tt=tt)
        change_price(link[0], price)
        changed = True

    def check_booking():
        cur.execute("select * from settings where id = 1")
        res = cur.fetchone()

        if res['book_market'] == 1:
            return True
        elif res['book_market'] == 0:
            return False

    if changed and check_booking():
        qwe = book_account(link[0], price, soup)
        if qwe == 1:
            print("аккаунт уже забронирован")
            return
        send_notification(system=True, msg='можно покупать аккаунт %s' % link[0])
        if "error" in qwe:
            print("ошибка при брони")
            print(qwe)
            send_notification(system=True, msg='аккаунт не забронировался')

    print(f"{price} - {link[0]}")
        


async def main():
    users = cur.execute("select * from users where approve = 1").fetchall()
    ids = []
    for user in users:
        ids.append(user['telegram_id'])

    cur.execute("select * from accounts where status=0")
    res = cur.fetchall()
    if not res:
        print('net akkov')
        time.sleep(40)
        return
    links = []
    for r in res:
        links.append([r['link'], r['first_price']])
    
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
                task = asyncio.create_task(check_account(session, link, ids))
                tasks.append(task)
            # print(tasks)
            try:
                await asyncio.gather(*tasks)
            except:            
                print("creah")
                print(traceback.format_exc())
                return None
            tasks = []
            time.sleep(1)

        if l > 0:
            l = -l
            for link in links[l:]:
                task = asyncio.create_task(check_account(session, link, ids))
                tasks.append(task)
        
            try:
                await asyncio.gather(*tasks)
            except:
                print("creah")
                print(traceback.format_exc())
                return None
            tasks = []
            time.sleep(1)




if __name__ == "__main__":
    while True:
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        except:
            print(traceback.format_exc())
            print('creash')
            time.sleep(5)
        # time.sleep(3)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())