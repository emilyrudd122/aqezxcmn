from typing import List, Tuple
from enum import Enum
from dataclasses import dataclass
import sqlite3
from bs4 import BeautifulSoup
from utils.utils import get_url


class Announce(Enum):
    """Кого надо оповещать"""
    ALL = 'all'
    ADMIN = 'admin'

class MarketLinks:
    """['ссылка на маркет, которую надо чекать', 'Кого оповещать если появится новый акк']"""
    link: str
    announce: Announce

    def __init__(self, link, announce):
        self.link = link
        self.announce = announce

qwe: List[MarketLinks] = []

@dataclass
class Account:
    id: int
    link: str
    name: str
    # сделать class Seller, который возвращает селлера по айди
    seller: int
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

    def get_account(self, link: str) -> Account or None:
        """Возвращает Account или False если такого аккаунта нет(по указанной ссылке)"""
        self.cur.execute("select * from accounts_check where link = ?", (link, ))
        res = self.cur.fetchone()
        if not res:
            return None

        return Account(res['id'], res['link'], res['name'], res['seller'], res['cost'])
        
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
        seller = market_item.find("div", class_="marketIndexItem--otherInfo").find("a", class_="username").get('href').split("/")[1]
        div_cost = market_item.find("div", class_='marketIndexItem--Price').text.split()
        cost = int(''.join(div_cost))

        created_at = market_item.find("span", class_="muted").text
        bumped = True if 'bumped' in market_item['class'] else False
        sticky = True if 'sticky' in market_item['class'] else False

        return MarketItemAccount(0, link, name, seller, cost, created_at, bumped, sticky)

    def new_account_job(self, account: MarketItemAccount):
        # Попыться забронировать аккаунт
        # Внести акк в бд
        # Отправить оповещение
        print(account.link)

    def start_check(self):
        self.links = self.parse_links()
        dd = ['назад', 'сегодня', 'вчера']
        for link in self.links:
            page = get_url(link.link)

            soup = BeautifulSoup(page.text, 'html.parser')
            market_items = soup.find_all("div", class_="marketIndexItem")

            for market_item in market_items[:3]:
                account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)
                if self.get_account(account.link) == None:
                    if account.sticky and not account.bumped and 'назад' in account.created_at:
                        self.new_account_job(account)
                    elif not account.sticky and not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                        self.new_account_job(account)
            for market_item in market_items[3:]:
                account: List[MarketItemAccount] = self.get_account_info_market_item(market_item)
                if self.get_account(account.link) == None:
                    if not account.bumped and any(qq in account.created_at.lower() for qq in dd):
                        self.new_account_job(account)
                    
            
        
market = MarketChecker()

market.start_check()