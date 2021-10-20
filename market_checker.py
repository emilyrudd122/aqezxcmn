import sys
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
import datetime

def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    soup = BeautifulSoup(asd.text, 'html.parser')
    xftoken = soup.find('input', {'name':'_xfToken'})['value']
    print('token = %s' % xftoken)

    return xftoken
def getXenforoCookie():
    r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    res = base64.b64decode(base64DfId).decode()
    return res
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

bot = telebot.TeleBot("2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM")

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cookies = make_coki()
headers = {'User-Agent':'Mozilla/5.0'}

def check_account_exists(link):
    cur.execute("select * from accounts_check where link = ?", (link, ))
    if cur.fetchone():
        return True
    return False

def add_account(link, name, seller_id, cost):
    sql = "insert into accounts_check(link, name, seller, cost, otlega) values (?, ?, ?, ?, 0)"
    data = (link, name, seller_id, cost)
    try:
        cur.execute(sql, data)

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

def announce(link, name, seller_name, cost, created_at, type):
    tt = datetime.datetime.now().strftime("%H:%M:%S")
    txt = f'---------------\n<b>[{tt}] Новый аккаунт, выложен {created_at}</b>\n\n{name}\n{cost}руб. from {seller_name}\nСсылка - {link}\n---------------'
    txt = f"""
<b>[{tt}] Новый аккаунт, выложен {created_at}</b>

{name}
{cost} руб. аккаунт от {seller_name}

Ссылка - {link}

"""
    print(txt)
    if type == 'all':
        print('all')
        bot.send_message(config.telegram_id, txt, parse_mode="html")
        bot.send_message("1243095585", txt, parse_mode="html")
    elif type == 'dan':
        txt = f"""
<b>[{tt}] Новый аккаунт, выложен {created_at}</b> DDD

{name}
{cost} руб. аккаунт от {seller_name}

Ссылка - {link}

"""
        print('dan')
        bot.send_message(config.telegram_id, txt, parse_mode="html")
        bot.send_message('578827447', txt, parse_mode='html')

async def parse_accounts(session, linkkk):
    print("checking")
    html = ""
    try:
        async with session.get(linkkk[0], proxy="http://eNmpWw:Qtxd0t@213.226.76.161:8000") as resp:
            assert resp.status == 200

            html = await resp.text()
    except Exception as e:
        print(traceback.format_exc())
        return

    soup = BeautifulSoup(html, 'html.parser')

    market_items = soup.find_all("div", class_="marketIndexItem")
    for market_item in market_items:
        a_link = market_item.find("a", class_="marketIndexItem--Title")
        link = f"https://lolz.guru/{a_link.get('href')}"
        seller_id = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").get('href').split("/")[1]
        seller_name = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").text
        div_cost = market_item.find("div", class_='marketIndexItem--Price').text.split()
        cost = ''.join(div_cost)
        name = a_link.text
        created_at = market_item.find("span", class_="muted").text

        if 'назад' in created_at or 'только' in created_at:
            if not check_account_exists(link):
                add_account(link, name, seller_id, cost)
                announce(link, name, seller_name, cost, created_at, linkkk[1])

links = [
        ["https://lolz.guru/market/steam/?game[]=730&inv_game=730&inv_min=1000&order_by=pdate_to_down&fromBtn=1", 'all'],
        # ["https://lolz.guru/market/steam/?pmax=2000&game[]=252950&hours_played[252950]=400&origin[]=brute&origin[]=stealer&origin[]=fishing&origin[]=autoreg&origin[]=personal&nsb=1&order_by=price_to_up", "dan"],
        # ["https://lolz.guru/market/steam/?pmax=500&game[]=730&daybreak=10&no_vac=1&rmin=1&rmax=1", "dan"],
        # ["https://lolz.guru/market/steam/?pmax=525&game[]=221100&daybreak=10&no_vac=1&order_by=price_to_up", "dan"],
        # ["https://lolz.guru/market/steam/?game[]=730&inv_game=730&inv_min=3000&order_by=price_to_up", "dan"],
        # ["https://lolz.guru/market/steam/?game[]=252490&inv_game=252490&inv_min=500&order_by=price_to_up", "dan"],
        # ["https://lolz.guru/market/steam/?game[]=570&inv_game=570&inv_min=1000&order_by=price_to_up", "dan"],
        # ["https://lolz.guru/market/steam/?pmax=470&game[]=1293830&daybreak=15&order_by=price_to_up", "dan"],
]

async def main():
    
    # link = "https://lolz.guru/market/steam/?game[]=730&inv_game=730&inv_min=1000&order_by=pdate_to_down&fromBtn=1"
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, trust_env=True) as session:
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
                task = asyncio.create_task(parse_accounts(session, link))
                tasks.append(task)
            # print(tasks)
            await asyncio.gather(*tasks)
            tasks = []
            time.sleep(5)

        if l > 0:
            l = -l
            for link in links[l:]:
                task = asyncio.create_task(parse_accounts(session, link))
                tasks.append(task)
        
            await asyncio.gather(*tasks)
            tasks = []
            time.sleep(1.2)


    conn.commit()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            bot.send_message(config.telegram_id, "краш автобая", parse_mode="html")
            print(traceback.format_exc())
            continue