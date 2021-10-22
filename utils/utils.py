import traceback
import requests
import base64
import re
from bs4 import BeautifulSoup
from utils import config
import sqlite3


def getXenforoCookie():
    try:
        r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    except:
        return None
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    res = base64.b64decode(base64DfId).decode()
    return res

def make_coki():
    cokies = config.cokies
    asd = cokies.split(';')
    ckies = {}
    xf = getXenforoCookie()
    if xf == None:
        return None
    for qwe in asd:
        qq = qwe.split("=")
        if qq[0].split()[0] == 'df_id':
            ckies[qq[0].split()[0]] = xf
            continue
        ckies[qq[0].split()[0]] = qq[1]

    cookies = ckies

    return cookies

def get_url(url):
    """ returns page(requests object) """
    print(f"отправил запрос {url}")
    try:
        # s = requests.Session()
        # cookies = config.cookies
        # url = "https://lolz.guru/market/16461695/"

        # print(cookies)
        coki = make_coki()
        url = url.replace(' ', '')
        
        if coki == None:
            return None
        print(1)
        page = requests.get(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=coki, timeout=5)
        print(2)
    except Exception as e:
        print(traceback.format_exc())
        return None
    # print(page.cookies)
    print('ответ от страницы получен>>')
    return page

def display_time(seconds, granularity=2):
    intervals = (
        ('недель', 604800),  # 60 * 60 * 24 * 7
        ('дней', 86400),    # 60 * 60 * 24
        ('часов', 3600),    # 60 * 60
        ('минут', 60),
        ('секунд', 1),
    )
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(int(value), name))
    return ', '.join(result[:granularity])

def get_post(url, data):
    """ returns page(requests object) """

    s = requests.Session()
    # cookies = config.cookies
    # url = "https://lolz.guru/market/16461695/"


    page = s.post(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=make_coki(), data=data, timeout=500)
    return page

def get_user_id():
    """ returns user_id on lolz.guru """
    main_page = get_url("https://lolz.guru/")
    if not main_page:
        return None
    soup = BeautifulSoup(main_page.text, 'html.parser')
    # print(soup)
    asd = soup.find(id="AccountMenu")
    asdd =  asd.find_all("a")
    url_id = asdd[3]
    user_id = url_id.get("href").split("/")[2]
    
    return user_id

conn = sqlite3.connect('databases/market.db', check_same_thread=False)
cursor = conn.cursor()

first_table = """CREATE TABLE "accounts" (
	"id"	INTEGER,
	"link"	TEXT,
	"buy_price"	INTEGER,
	"sell_price"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);"""
second_table = """CREATE TABLE "resell_price" (
	"link"	TEXT,
	"price"	INTEGER
);"""
try:
    qwa = cursor.execute(second_table)
    conn.commit()
    qwe = cursor.execute(first_table)
    conn.commit()
    
    print('tables created')
except sqlite3.OperationalError:
    # print('table existst')
    pass
