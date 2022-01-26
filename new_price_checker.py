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
from utils.utils import get_url, make_coki
import telebot
import datetime

def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    print(asd)
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
        arseniy_id = 1140617968
        # bot.send_message(config.telegram_id, msg)
        return
    try:
        arseniy_id = 1140617968
        msg = f'Цена изменена с {first_price} на {new_price} {link}'
        bot.send_message(config.telegram_id, msg)
        # bot.send_message(arseniy_id, msg)
        

    except Exception as e:
        print(traceback.format_exc())
        print("ошибка при отправке оповещения в телеграм")


# def make_coki():
#     cokies = config.cokies
#     asd = cokies.split(';')
#     ckies = {}
#     for qwe in asd:
#         qq = qwe.split("=")

#         ckies[qq[0].split()[0]] = qq[1]

#     cookies = ckies

#     return cookies


cookies = make_coki()
# print(cookies)
headers = {'User-Agent':'Mozilla/5.0'}

def get_account_status(link):
    cur.execute("select * from accounts where link = ?", (link, ))
    res = cur.fetchone()

    return res['status']

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
        if get_account_status(link) == 5 and 'закрыто' in asd.text:
            print(f"аккаунт {link} закрыт, продолжаю чекать")
            return 0
        elif get_account_status(link) == 5 and not 'закрыто' in asd.text:
            return 1
        # print(asd.text)
        if 'закрыто' in asd.text:
            print(f"аккаунт {link} закрыт")
            set_account_status(link, 5)
        if 'удалено' in asd.text:
            print(f"аккаунт {link} удален")
            set_account_status(link, 2)

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

mistakes = 0

async def check_account(session, link, ids):
    global mistakes
    html = ""
    # import random
    # qwe = random.randint(1, 5)
    # await asyncio.sleep((1/qwe))
    try:
        async with session.get(link[0], verify_ssl=False) as resp:
            assert resp.status == 200
            html = await resp.text()

    except Exception as e:
        print(traceback.format_exc())
        af = traceback.format_exc()
        if mistakes > 10:
            bot.send_message(config.telegram_id, f"{af}")
            mistakes = 0
        mistakes += 1
        await asyncio.sleep(0.3)
        return None

    soup = BeautifulSoup(html, 'lxml')
    
    if not check_del(soup, link[0]):
        return

    username = soup.find("a", class_="username")
    if not username:
        return None


    
    bought = check_account_bought(soup)
    price = get_price(soup)
    if bought == 1:
        print("аккаунт был куплен, ставлю статус 1 %s " % link[0])
        set_account_status(link[0], 1)
        return
    tt = ""
    if bought == 2:
        tt = "(забронирован)"
        print("аккаунт уже забронирован")
    changed = False

    if get_account_status(link[0]) == 5:
        print(f"бронирую аккаунт после открытия объявления {link[0]}")
        qwe = book_account(link[0], price, soup)
        set_account_status(link[0], 0)

    if price != int(link[1]):
        print("price changed")
        changed = True
        def check_booking():
            cur.execute("select * from settings where id = 1")
            res = cur.fetchone()

            if res['book_market'] == 1:
                return True
            elif res['book_market'] == 0:
                return False
        if changed and check_booking():
            print("бронирую")
            qwe = book_account(link[0], price, soup)
            if qwe == 1:
                print("аккаунт уже забронирован")
                return
            send_notification(system=True, msg='можно покупать аккаунт %s' % link[0])
            if "error" in qwe:
                print("ошибка при брони")
                print(qwe)
                send_notification(system=True, msg='аккаунт не забронировался')
            else:
                print(f"{link[0]} забронирован")
        send_notification(ids, link[0], link[1], price, tt=tt)
        change_price(link[0], price)
        


    # if changed and check_booking():
    #     qwe = book_account(link[0], price, soup)
    #     if qwe == 1:
    #         print("аккаунт уже забронирован")
    #         return
    #     send_notification(system=True, msg='можно покупать аккаунт %s' % link[0])
    #     if "error" in qwe:
    #         print("ошибка при брони")
    #         print(qwe)
    #         send_notification(system=True, msg='аккаунт не забронировался')

    print(f"{datetime.datetime.now().time()} {price} - {link[0]}")
        


async def main(loop):
    users = cur.execute("select * from users where approve = 1").fetchall()
    ids = []
    for user in users:
        ids.append(user['telegram_id'])


    
    async with aiohttp.ClientSession(loop=loop, headers=headers, cookies=cookies) as session:
        while True:

            # check_license()
            for i in range(100):
                cur.execute("select * from accounts where status=0 or status=5")
                res = cur.fetchall()
                if not res:
                    print('net akkov')
                    time.sleep(10)
                    continue
                links = []
                for r in res:
                    links.append([r['link'], r['first_price']])
                for link in links:

                    asyncio.ensure_future(check_account(session, link, ids))
                    await asyncio.sleep(0.5)
                        
                # await asyncio.sleep(0.4)



if __name__ == "__main__":
    while True:
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(main(loop))
            loop.run_forever()
        except:
            print(traceback.format_exc())
            print('creash')
            time.sleep(5)
        # time.sleep(3)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
