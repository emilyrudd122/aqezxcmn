import json
from utils.utils import get_url, get_post
import time
import traceback
from bs4 import BeautifulSoup
import telebot
from utils import config
import sqlite3

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

bot = telebot.TeleBot("2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM")


def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    soup = BeautifulSoup(asd.text, 'html.parser')
    xftoken = soup.find('input', {'name':'_xfToken'})['value']
    print('token = %s' % xftoken)

    return xftoken

def send_notification(ids='', link='', first_price='', new_price='', system=False, msg='', tt=""):
    if system:
        bot.send_message(config.telegram_id, msg)
        return
    try:
        for id in ids:
            bot.send_message(id, "%s цена изменена с %s на %s %s" % (link, first_price, new_price, tt))
    except:
        print("ошибка при отправке оповещения в телеграм")


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
        bot.send_message(config.telegram_id, 'поломалось что то')
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

def get_waiting_links() -> list:
    cur.execute("select * from accounts where status = 0")
    res = cur.fetchall()
    if res:
        return res
    else:
        return None

def set_account_status(link, status):
    sql = "update accounts set status = ? where link = ?"
    data = (status, link)

    try:
        cur.execute(sql, data)
        conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

def change_price(link, new_price):
    sql = "update accounts set first_price = ? where link = ?"
    data = (new_price, link)

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

"""
statuses:
    0 - проверяем цену постоянно
    1 - аккаунт был куплен, цена не проверяется
    2 - неинтересно для покупки
    3 - объява удалена
"""

ids = [config.telegram_id, "1243095585", "473485315"]
# ids = [config.telegram_id]

if __name__ == "__main__":
    xftoken = parse_xftoken()

def main():
    links = get_waiting_links()

    if not links:
        print("no links to parse, waiting 1 minute")
        time.sleep(60)
        return
    
    for account in links:
        if account['status'] == 0:
            print("work with %s " % account['link'])
            
            try:
                acc_page = BeautifulSoup(get_url(account['link']).text, 'html.parser')
            except:
                print("ошибка при получении страницы с маркета")
                time.sleep(10)
                return
            
            qq = check_del(acc_page, account['link'])
            if not qq:
                continue

            price = get_price(acc_page)

            if not price:
                # если гет прайс возвращает None то ждем и перезапускаемся
                time.sleep(15)
                return
            
            
            bought = check_account_bought(acc_page)
            if bought == 1:
                print("аккаунт был куплен, ставлю статус 1 %s " % account['link'])
                set_account_status(account['link'], 1)
                continue
            tt = ""
            if bought == 2:
                tt = "(забронирован)"
            changed = False
            if price != int(account['first_price']):
                print("price changed")
                send_notification(ids, account['link'], account['first_price'], price, tt=tt)
                change_price(account['link'], price)
                changed = True
                # continue

            if changed:
                qwe = book_account(account['link'], price, acc_page)
                if qwe == 1:
                    print("аккаунт уже забронирован")
                    continue
                send_notification(system=True, msg='можно покупать аккаунт %s' % account['link'])
                if "error" in qwe:
                    print("ошибка при брони")
                    print(qwe)
                    send_notification(system=True, msg='аккаунт не забронировался')
            
            # time.sleep(0.2)
    
    print("все проверено, жду 5 сек и по новой.")
    time.sleep(1)
        
if __name__ == "__main__":
    while True:
        main()

    # asd = get_url("https://lolz.guru/market/17649360/balance/check?price=1&=&_xfRequestUri=/market/17649360/&_xfNoRedirect=1&_xfToken=3764769,1634319020,21b830212188e341fa0b0d5bfab7a78fd1b9d053&_xfResponseType=json")
    # print(json.loads(asd.text))