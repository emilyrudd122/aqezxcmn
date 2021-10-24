import time
import traceback
from typing import List, Tuple
from enum import Enum
from dataclasses import dataclass
import sqlite3
from bs4 import BeautifulSoup
import json
from utils.utils import get_url
import telebot
from utils import config
import datetime


class Announce(Enum):
    """Кого надо оповещать"""
    ALL = 'all'
    DAN = 'dan'
    ADMIN = 'admin'

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
    bumped: bool
    sticky: bool

class MarketChecker():
    links: List[MarketLinks] = []

    def __init__(self):
        self.links = []
        self.conn = sqlite3.connect('databases/lolz_market_bot.db')
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.xftoken = ""
        # TODO: вынести токен в конфиг
        self.bot = telebot.TeleBot(token="2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM")

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

        created_at = market_item.find("span", class_="muted").text
        bumped = True if 'bumped' in market_item['class'] else False
        sticky = True if 'sticky' in market_item['class'] else False

        return MarketItemAccount(0, link, name, seller_id, seller_name, cost, created_at, bumped, sticky)

    def parse_xftoken(self):
        print("начинаю парсить xftoken")
        asd = get_url("https://lolz.guru/")
        if not asd:
            return None
        soup = BeautifulSoup(asd.text, 'lxml')
        xftoken = soup.find('input', {'name':'_xfToken'})['value']
        # print('token = %s' % xftoken)

        return xftoken

    def book_account(self, account: MarketItemAccount) -> dict or None:
        market_id = account.link.split('/')[-2]
        if self.xftoken == '':
            self.xftoken = self.parse_xftoken()
        link = f"https://lolz.guru/market/{market_id}/balance/check?price={account.cost}&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={self.xftoken}&_xfResponseType=json"
        # print(linkk)
        page = get_url(link)
        if not page:
            return None
        answer = json.loads(page.text)
        if 'error' in answer:
            print(answer['error'])
            return None
        return answer

    def send_announce_telegram(self, account: MarketItemAccount, link: MarketLinks):
        msg = f"""
            <b>[{datetime.datetime.now().strftime("%H:%M:%S")}] Новый аккаунт, выложен {account.created_at}</b>

            {account.name}

            {account.cost} руб. аккаунт от {account.seller_name}
            Ссылка - {account.link}
        """
        
        if link.announce == Announce.ADMIN:
            self.bot.send_message(config.telegram_id, msg, parse_mode='html')
        elif link.announce == Announce.ALL:
            self.bot.send_message(1647564460, msg, parse_mode='html')
            self.bot.send_message(578827447, msg, parse_mode='html')
            self.bot.send_message(1243095585, msg, parse_mode='html')
            

    def insert_account_db(self, account: Account):
        sql = "insert into accounts_check(link, name, seller, cost, otlega) values (?, ?, ?, ?, 0)"
        data = (account.link, account.name, account.seller_id, account.cost)
        try:
            self.cur.execute(sql, data)

        except sqlite3.Error as error:
            print("Failed to insert Python variable into sqlite table", error)

    def new_account_job(self, account: MarketItemAccount, link: MarketLinks):
        # Попыться забронировать аккаунт
        # Внести акк в бд
        # Отправить оповещение
        
        book = self.book_account(account)
        self.insert_account_db(account)
        self.send_announce_telegram(account, link)
        
    def start_check(self):
        self.links = self.parse_links()
        dd = ['назад', 'сегодня', 'вчера']
        for link in self.links:
            page = get_url(link.link)

            soup = BeautifulSoup(page.text, 'lxml')
            market_items = soup.find_all("div", class_="marketIndexItem")

            for market_item in market_items[:3]:
                account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)

                if self.get_account(account.link) == None:
                    if account.sticky and not account.bumped and 'назад' in account.created_at:
                        self.new_account_job(account, link)
                    elif not account.sticky and not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                        self.new_account_job(account, link)

            for market_item in market_items[3:]:
                account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)
                if self.get_account(account.link) == None:
                    if not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                        print(account.name)
                        self.new_account_job(account, link)
                    
        self.conn.commit()
        
market = MarketChecker()

while True:
    try:
        market.start_check()
        time.sleep(4)
    except Exception as e:
        print(traceback.format_exc())
        print("crash, sleep 10 sec")
        time.sleep(10)
