import time
import requests
import traceback
from typing import List, Tuple
from enum import Enum
from dataclasses import dataclass
import sqlite3
from bs4 import BeautifulSoup
import json
from utils.utils import get_url, get_post, make_table_invs
import telebot
from utils import config
import datetime

make_table_invs()

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


@dataclass
class MarketItemAccount(Account):
    name: str
    # сделать class Seller, который возвращает селлера по айди
    seller_id: int
    seller_name: str
    cost: int
    created_at: str
    otlega: str
    week_hours: str
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
        self.bot = telebot.TeleBot(token=config.market_bot_token)

    def get_account(self, link: str) -> Account or None:
        """Возвращает Account или False если такого аккаунта нет(по указанной ссылке)"""
        self.cur.execute("select * from invents_check where link = ?", (link, ))
        res = self.cur.fetchone()
        if not res:
            return None

        return Account(res['id'], res['link'])
        
    def parse_links(self) -> List[MarketLinks] or None:
        # self.cur.execute("select * from links")
        # res = self.cur.fetchall()
        # if not res:
        #     return None
        list: List[MarketLinks] = []

        list.append(MarketLinks('https://lolz.guru/market/steam/?game[]=730&country[]=China&inv_game=730&inv_max=1&order_by=pdate_to_down   ', Announce('dan')))

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
        asd = get_url("https://lolz.guru/")
        if not asd:
            return None
        soup = BeautifulSoup(asd.text, 'lxml')
        xftoken = soup.find('input', {'name':'_xfToken'})['value']
        # print('token = %s' % xftoken)

        return xftoken

    def book_account(self, account: MarketItemAccount) -> dict or None:
        market_id = account.link.split('/')[-2]

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

    def send_announce_telegram(self, account: MarketItemAccount, link: MarketLinks, inv):
        msg = f"""[{datetime.datetime.now().strftime("%H:%M:%S")}]{account.name}

<b>инвентарь - {inv['totalValueSimple']} руб.</b>

{account.otlega} + {account.week_hours}
{account.cost} руб. аккаунт от {account.seller_name}
Ссылка - {account.link}
        """
        
        if link.announce == Announce.ADMIN:
            print("announce admin")
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
        elif link.announce == Announce.DAN:
            self.bot.send_message(config.telegram_id, msg, parse_mode='html')
            self.bot.send_message(578827447, msg, parse_mode='html')
            
    def check_booking(self) -> bool:
        """Проверяет в бд, нужно ли бронировать аккаунты, возвращает тру если надо"""
        self.cur.execute("select * from settings where id = 1")
        res = self.cur.fetchone()

        if res['book_market'] == 1:
            return True
        elif res['book_market'] == 0:
            return False

    def insert_account_db(self, account: Account):
        sql = "insert into invents_check(link) values (?)"
        data = (account.link, )
        try:
            self.cur.execute(sql, data)
            self.conn.commit()

        except sqlite3.Error as error:
            print("Failed to insert Python variable into sqlite table", error)

    def parse_inventory(self, account: MarketItemAccount):
        market_id = account.link.split('/')[-2]
        post_url = "https://lolz.guru/market/steam-value"
        app_id = "730"
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-length": "210",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://lolz.guru",
            "referer": "https://lolz.guru/market/steam-value",
            "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "macOS",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "x-ajax-referer": "https://lolz.guru/market/steam-value",
            "x-requested-with": "XMLHttpRequest",
        }

        data = {
            "link": account.link,
            "app_id": app_id,
            "_xfRequestUri": f"/market/steam-value?link=https%3A%2F%2Flolz.guru%2Fmarket%2F{market_id}%2F&app_id={app_id}",
            "_xfNoRedirect": 1,
            "_xfToken": self.xftoken,
            "_xfResponseType": "json"
        }
        parsed=False
        print("Начинаю парсить инв")
        for i in range(10):
            print(i)
            if not parsed:
                try:
                    asd = get_post(post_url, data, headers)
                    qwe = json.loads(asd.text)
                except requests.exceptions.ReadTimeout:
                    continue
                if not 'error' in qwe:
                    parsed=True
                    print(f'parsed = true {qwe["totalValueSimple"]}')
                    return qwe
                else:
                    print(qwe)
                    continue
            else:
                print('break')
                break
        print('false')
        return False



    def new_account_job(self, account: MarketItemAccount, link: MarketLinks):
        # бронирование аккаунта
        # проверка на то, был ли аккаунт забронирован
        # внесение аккаунта в бд
        # парс инвентаря
        # отправка оповещения, если инвентарь больше {config.inv_price}, иначе скип и разбронирование
        # book = self.book_account(account)
        
        inv = self.parse_inventory(account)
        if inv == False:
            print(f"не получилось спарсить {account.link}")
        else:
            if float(inv['totalValueSimple']) > 1:
                self.send_announce_telegram(account, link, inv)
        self.insert_account_db(account)
        

    

    def start_check(self):
        self.links = self.parse_links()
        if self.xftoken == '':
            self.xftoken = self.parse_xftoken()
        dd = ['назад', 'сегодня', 'вчера', 'только']
        for link in self.links:
            page = get_url(link.link)

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
                    # print('1')
                    if self.get_account(account.link) == None:
                        # print('2')
                        if not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                            # print('3')
                            print(account.name)
                            self.new_account_job(account, link)
                            time.sleep(0.1)
                    
        # self.conn.commit()
        
market = MarketChecker()

while True:
    try:
        market.start_check()
        # time.sleep(1)
    except Exception as e:
        print(traceback.format_exc())
        print("crash, sleep 10 sec")
        time.sleep(10)
