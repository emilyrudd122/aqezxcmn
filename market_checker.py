import logging
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
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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

token = "2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM"

bot = telebot.TeleBot(token)

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
conn.commit()   

xftoken = parse_xftoken()
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

def announce(link, name, seller_name, cost, created_at, type, booked=False):
    tt = datetime.datetime.now().strftime("%H:%M:%S")
    txt = f'---------------\n<b>[{tt}] Новый аккаунт, выложен {created_at}</b>\n\n{name}\n{cost}руб. from {seller_name}\nСсылка - {link}\n---------------'
    txt = f"""
<b>[{tt}] Новый аккаунт, выложен {created_at}</b>

{name}

{cost} руб. аккаунт от {seller_name}
Ссылка - {link} {'забронирован' if booked else ''}

"""
    print(txt)
    ids = []
    if type == 'all':
        ids = [config.telegram_id, "1243095585"]
    elif type == 'dan':
        txt += "\nddd"
        ids = [config.telegram_id, '578827447']
    elif type == 'test':
        ids = [config.telegram_id]

    for id in ids:
        if booked:
            pass
            # print('keyboard')
            # keyboard = InlineKeyboardMarkup()
            # keyboard.add(InlineKeyboardButton(text="Купить аккаунт", callback_data=f"buy {link} {cost}"))
            # bot.send_message(id, txt, reply_markup=keyboard, parse_mode='html')
        # else:
        bot.send_message(id, txt, parse_mode='html')

def book_account(link, price, soup=''):
    if not soup:
        try:
            soup = BeautifulSoup(get_url(link).text, 'html.parser')
        except:
            return False
    buy_button = soup.find_all("a", class_="marketViewItem--buyButton")
    if len(buy_button) > 1:
        return False

    market_id = link.split('/')[-2]
    linkk = f"https://lolz.guru/market/{market_id}/balance/check?price={price}&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={xftoken}&_xfResponseType=json"
    # print(linkk)
    asd = get_url(linkk)
    answer = json.loads(asd.text)

    return answer

def parse_accounts(linkkk):
    print("checking")
    html = ""
    try:
        asd = get_url(linkkk[0])
        # assert asd. == 200

        html = asd.text
    except Exception as e:
        print(traceback.format_exc())
        bot.send_message(config.telegram_id, "не парсится маркет", parse_mode="html")
        return

    soup = BeautifulSoup(html, 'html.parser')
    
    print(linkkk[0])
    balance = soup.find_all("span", class_="balanceNumber")[0].find("span", "balanceValue").text.split()
    # print(balance)
    balance = ''.join(balance)
    market_items = soup.find_all("div", class_="marketIndexItem")
    for market_item in market_items[:3]:
        a_link = market_item.find("a", class_="marketIndexItem--Title")
        link = f"https://lolz.guru/{a_link.get('href')}"
        seller_id = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").get('href').split("/")[1]
        seller_name = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").text
        div_cost = market_item.find("div", class_='marketIndexItem--Price').text.split()
        cost = ''.join(div_cost)
        name = a_link.text
        created_at = market_item.find("span", class_="muted").text

        
        dd = ['назад', 'сегодня', 'вчера']
        if 'sticky' in market_item['class'] and not 'bumped' in market_item['class'] and 'назад' in created_at.lower():
            if not check_account_exists(link):
                if int(balance) > int(cost):
                    asd = book_account(link, cost)
                add_account(link, name, seller_id, cost)
                if not asd:
                    announce(link, name, seller_name, cost, created_at, linkkk[1])
                if asd and not 'error' in asd:
                    print("забронирован акк")
                    print(asd)
                    announce(link, name, seller_name, cost, created_at, linkkk[1], booked=True)
        elif not 'sticky' in market_item['class'] and not 'bumped' in market_item['class'] and any(qq in created_at.lower() for qq in dd):
            if not check_account_exists(link):
                if int(balance) > int(cost):
                    asd = book_account(link, cost)
                add_account(link, name, seller_id, cost)
                if not asd:
                    announce(link, name, seller_name, cost, created_at, linkkk[1])
                if asd and not 'error' in asd:
                    print("забронирован акк")
                    print(asd)
                    announce(link, name, seller_name, cost, created_at, linkkk[1], booked=True)
            

    for market_item in market_items[3:]:
        # print(market_item['class'])
        a_link = market_item.find("a", class_="marketIndexItem--Title")
        link = f"https://lolz.guru/{a_link.get('href')}"
        seller_id = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").get('href').split("/")[1]
        seller_name = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").text
        div_cost = market_item.find("div", class_='marketIndexItem--Price').text.split()
        cost = ''.join(div_cost)
        name = a_link.text
        created_at = market_item.find("span", class_="muted").text
        
        dd = ['назад', 'сегодня', 'вчера']
        if not 'bumped' in market_item['class'] and any(qq in created_at.lower() for qq in dd):
            if not check_account_exists(link):
                if int(balance) > int(cost):
                    asd = book_account(link, cost)
                add_account(link, name, seller_id, cost)
                if not asd:
                    announce(link, name, seller_name, cost, created_at, linkkk[1])
                if asd and not 'error' in asd:
                    print("забронирован акк")
                    print(asd)
                    announce(link, name, seller_name, cost, created_at, linkkk[1], booked=True)


links = [
    # ['https://lolz.guru/market/steam/?pmin=1&pmax=1&game[]=444200&daybreak=500&order_by=price_to_up', 'all']
    ["https://lolz.guru/market/steam/?game[]=730&inv_game=730&inv_min=1000&order_by=pdate_to_down&fromBtn=1", 'all'],
    # ["https://lolz.guru/market/steam/?game[]=730&rmin=1&order_by=pdate_to_down", 'test']
]

def main():
    
    for link in links:
        parse_accounts(link)
        time.sleep(2)

    conn.commit()
    # # link = "https://lolz.guru/market/steam/?game[]=730&inv_game=730&inv_min=1000&order_by=pdate_to_down&fromBtn=1"
    # async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
    #     tasks = []
    #     ch = 4
    #     ll = len(links)//ch
    #     l = len(links)%ch

    #     # print(ll)
    #     # print(l)

    #     for link in links:
    #         task = asyncio.create_task(parse_accounts(session, link))
    #         tasks.append(task)

        # for i in range(1, ll+1):
        #     q = i*ch
        #     w = q-ch
        #     # print(list[w:q])
        #     for link in links[w:q]:
        #         task = asyncio.create_task(parse_accounts(session, link))
        #         tasks.append(task)
        #     # print(tasks)
        #     await asyncio.gather(*tasks)
        #     tasks = []
        #     time.sleep(0.5)

        # if l > 0:
        #     l = -l
        #     for link in links[l:]:
        #         task = asyncio.create_task(parse_accounts(session, link))
        #         tasks.append(task)
        
        # await asyncio.gather(*tasks)
        # time.sleep(0.5)


    

if __name__ == "__main__":
    while True:
        try:
            # policy = asyncio.WindowsSelectorEventLoopPolicy()
            # asyncio.set_event_loop_policy(policy)
            # asyncio.run(main())
            main()
        except Exception as e:
            bot.send_message(config.telegram_id, "краш market_checker", parse_mode="html")
            print(traceback.format_exc())
            time.sleep(5)
            continue