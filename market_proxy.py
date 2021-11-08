import time
import traceback
from typing import List
from enum import Enum
from dataclasses import dataclass
import sqlite3
from bs4 import BeautifulSoup
import json
# from utils.utils import get_url
from utils.test_utils import get_url
import telebot
from utils import config
import datetime
import random

with open('utils/proxy.txt') as f:
    proxies = f.readlines()

i=0

def take_proxy():
    global lines
    global i
    # a = random.randint(1,len(proxies)-1)

    proxy = proxies[i].replace('\n', '')
    prox = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}",
    }
    i+=1
    # print(prox)
    return prox


class Announce(Enum):
    """Кого надо оповещать"""
    ALL = 'all'
    DAN = 'dan'
    ADMIN = 'admin'
    HARITON = 'hariton'

class MarketLinks:
    """['ссылка на маркет, которую надо чекать', 'Кого оповещать если появится новый акк']"""
    link: str
    announce: Announce

    def __init__(self, link, announce):
        self.link = link
        self.announce = announce

@dataclass
class Account:
    id: int
    link: str
    name: str
    # сделать class Seller, который возвращает селлера по айди
    seller_id: int
    seller_name: str
    cost: int

@dataclass
class MarketItemAccount(Account):
    created_at: str
    otlega: str
    week_hours: str
    bumped: bool
    sticky: bool

class MarketChecker():
    links: List[MarketLinks] = []

    def __init__(self):
        self.links = []
        self.tokens = {}
        self.conn = sqlite3.connect('databases/lolz_market_bot.db')
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.xftoken = ""
        # TODO: вынести токен в конфиг
        self.bot = telebot.TeleBot(token=config.market_bot_token)
        self.proxy = ''

    def get_account(self, link: str) -> Account or None:
        """Возвращает Account или False если такого аккаунта нет(по указанной ссылке)"""
        self.cur.execute("select * from accounts_check where link = ?", (link, ))
        res = self.cur.fetchone()
        if not res:
            return None

        return Account(res['id'], res['link'], res['name'], res['seller'],'', res['cost'])
        
    def parse_links(self) -> List[MarketLinks] or None:
        self.cur.execute("select * from links")
        res = self.cur.fetchall()
        if not res:
            return None
        list: List[MarketLinks] = []
        for r in res:
            list.append(MarketLinks(r['link'], Announce(r['announce'])))

        return list

    def get_account_info_market_item(self, market_item) -> MarketItemAccount:
        """Takes market_item soup (market_items div on lolz) and returns Account object with data from lolz page"""
        link = "https://lolz.guru/" + market_item.find("a", class_="marketIndexItem--Title").get('href')
        name = market_item.find("a", class_="marketIndexItem--Title").text
        seller_id = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").get('href').split("/")[1]
        seller_name = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").text
        div_cost = market_item.find("div", class_='marketIndexItem--Price').text.split()
        cost = int(''.join(div_cost))

        stats = market_item.find_all("span", class_="stat")
        otlega = stats[0].text.strip()
        week_hours = stats[2].text.strip()
        if "фишинг" in week_hours.lower() or "стилер" in week_hours.lower() or "гарантии" in week_hours.lower():
            week_hours = stats[3].text.strip()
            if "гарантии" in week_hours.lower() or "фишинг" in week_hours.lower():
                week_hours = stats[4].text.strip()

        created_at = market_item.find("span", class_="muted").text
        bumped = True if 'bumped' in market_item['class'] else False
        sticky = True if 'sticky' in market_item['class'] else False

        return MarketItemAccount(0, link, name, seller_id, seller_name, cost, created_at, otlega, week_hours, bumped, sticky)

    def parse_xftoken(self):
        print("начинаю парсить xftoken")
        asd = get_url("https://lolz.guru/", self.proxy, True)
        if not asd:
            return None
        soup = BeautifulSoup(asd.text, 'lxml')
        if "Please enable JavaScript and Cookies in your browser" in soup.text:
            print("Please enable JavaScript and Cookies in your browser")
            return None
        xftoken = soup.find('input', {'name':'_xfToken'})['value']

        return xftoken

    def book_account(self, account: MarketItemAccount) -> dict or None:
        market_id = account.link.split('/')[-2]

        link = f"https://lolz.guru/market/{market_id}/balance/check?price={account.cost}&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={self.xftoken}&_xfResponseType=json"
        # print(linkk)
        page = get_url(link, self.proxy)
        if not page:
            return None
        answer = json.loads(page.text)
        if 'error' in answer:
            print(answer['error'])
            return None
        # print(answer)
        print(f"аккаунт забронен {account.link}")
        return answer

    def send_announce_telegram(self, account: MarketItemAccount, link: MarketLinks):
        msg = f"""
            <b>[{datetime.datetime.now().strftime("%H:%M:%S")}] Новый аккаунт, выложен {account.created_at}</b>
            {account.name}

            {account.otlega} + {account.week_hours}
            {account.cost} руб. аккаунт от {account.seller_name}
            Ссылка - {account.link}
        """
        
        if link.announce == Announce.ADMIN:
            self.bot.send_message(config.telegram_id, msg, parse_mode='html')
        elif link.announce == Announce.ALL:
            self.bot.send_message(1647564460, msg, parse_mode='html')
            self.bot.send_message(578827447, msg, parse_mode='html')
            self.bot.send_message(1243095585, msg, parse_mode='html')
            self.bot.send_message(1140617968, msg, parse_mode='html')
            self.bot.send_message(473485315, msg, parse_mode='html')
        elif link.announce == Announce.HARITON:
            self.bot.send_message(1647564460, msg, parse_mode='html')
            self.bot.send_message(473485315, msg, parse_mode='html')
            
    def check_booking(self) -> bool:
        """Проверяет в бд, нужно ли бронировать аккаунты, возвращает тру если надо"""
        self.cur.execute("select * from settings where id = 1")
        res = self.cur.fetchone()

        if res['book_market'] == 1:
            return True
        elif res['book_market'] == 0:
            return False

    def insert_account_db(self, account: Account):
        sql = "insert into accounts_check(link, name, seller, cost, otlega) values (?, ?, ?, ?, 0)"
        data = (account.link, account.name, account.seller_id, account.cost)
        try:
            self.cur.execute(sql, data)
            self.conn.commit()

        except sqlite3.Error as error:
            print("Failed to insert Python variable into sqlite table", error)

    def new_account_job(self, account: MarketItemAccount, link: MarketLinks):
        # Попыться забронировать аккаунт
        # Внести акк в бд
        # Отправить оповещение
        
        if self.check_booking():
            book = self.book_account(account)
        self.insert_account_db(account)
        self.send_announce_telegram(account, link)
        
    def start_check(self):
        self.links = self.parse_links()
        self.proxy = take_proxy()
        
        print(self.proxy['http'])
        
        proxy = self.cur.execute("select * from proxy where ip = ?", (self.proxy['http'], ))
        prox = proxy.fetchone()
        if not prox:
            print("no proxy in db")
            self.xftoken = self.parse_xftoken()
            if self.xftoken == None:
                print("ошибка при парсе хфтокен")
                return
            self.cur.execute("update proxy set xftoken=? where ip=?", (self.xftoken, self.proxy['http']))
            self.conn.commit()
        else:
            self.xftoken = prox['xftoken']
            print(self.xftoken)
        # return
        dd = ['назад', 'сегодня', 'вчера', 'только']
        for link in self.links:
            
            page = get_url(link.link, self.proxy)
            while not page:
                print("changing cookie and xftoken")
                page = get_url(link.link, self.proxy, remake_cookie=True)
                # self.xftoken = self.parse_xftoken()
                time.sleep(2)

            soup = BeautifulSoup(page.text, 'lxml')

            market_items = soup.find_all("div", class_="marketIndexItem")

            for market_item in market_items[:3]:
                if not 'itemIgnored' in market_item['class']: #проверка на блок продавца
                    account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)
                    if self.get_account(account.link) == None:
                        if account.sticky and not account.bumped and 'назад' in account.created_at:
                            self.new_account_job(account, link)
                        elif not account.sticky and not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                            self.new_account_job(account, link)

            for market_item in market_items[3:]:
                if not 'itemIgnored' in market_item['class']: #проверка на блок продавца
                    account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)
                    if self.get_account(account.link) == None:
                        if not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                            print(account.name)
                            self.new_account_job(account, link)

        
        
market = MarketChecker()

while True:
    try:
        market.start_check()
        print('sleep')
        time.sleep(0.5)
    except Exception as e:
        print(traceback.format_exc())
        print("crash, sleep 2 sec")
        time.sleep(2)
