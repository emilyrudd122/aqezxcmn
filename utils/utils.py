import traceback
import requests
import base64
import re
from bs4 import BeautifulSoup
from requests.api import head
from utils import config
import sqlite3
import datetime
import dfuid
coki = ""

df_id = ''
def getXenforoCookie():
    global df_id
    if df_id == '':
        print('parse df')
        try:
            r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
        except:
            return None
        cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
        base64DfId = eval(cookieArray)[-1]
        res = base64.b64decode(base64DfId).decode()
        df_id = res
        print('parsed df')
        return res
    else:
        return df_id

def make_coki():
    cokies = config.cokies
    asd = cokies.split(';')
    ckies = {}
    # xf = getXenforoCookie()
    # if xf == None:
    #     print("Ошибка при парсе куков")
    #     return None
    for qwe in asd:
        qq = qwe.split("=")
        # if qq[0].split()[0] == 'df_uid':

        #     # ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        #     df_id_fetcher = dfuid.DfUid("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
        #     df_uid = df_id_fetcher.fetch()
        #     print(df_uid)
        #     if df_uid == 0:
        #         print("error")
        #         return 0
        #     ckies[qq[0].split()[0]] = df_uid
        #     continue
        ckies[qq[0].split()[0]] = qq[1]

    cookies = ckies

    return cookies



def get_url(url):
    global coki
    """ returns page(requests object) """
    print(f"""{str(datetime.datetime.now().strftime("%H:%M:%S"))} отправил запрос {url}""")
    try:
        # s = requests.Session()
        # cookies = config.cookies
        # url = "https://lolz.guru/market/16461695/"

        # print(cookies)
        if coki == "":
            coki = make_coki()
        url = url.replace(' ', '')
        
        if coki == None:
            return None
        # print(1)
        page = requests.get(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=coki, timeout=5)
        # print(2)
    except Exception as e:
        print(traceback.format_exc())
        print("Ошибка при парсе страницы")
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

def get_post(url, data, headers=None, timeout=15):
    """ returns page(requests object) """

    global coki
    # cookies = config.cookies
    # url = "https://lolz.guru/market/16461695/"

    if not headers:
        if coki == "":
            coki = make_coki()
        page = requests.post(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=coki, data=data, timeout=timeout)
    else:
        # headers['cookie'] = str(make_coki())
        page = requests.post(url,headers=headers, cookies=make_coki(), data=data, timeout=timeout)
    return page

def get_user_id():
    """ returns user_id on lolz.guru """
    main_page = get_url("https://lolz.guru/")
    if not main_page:
        return None
    soup = BeautifulSoup(main_page.text, 'html.parser')
    
    asd = soup.find(id="AccountMenu")
    
    asdd =  asd.find_all("a")
    
    url_id = asdd[3]
    user_id = url_id.get("href").split("/")[2]
    
    return user_id

def make_table_invs():
    conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    table = """CREATE TABLE "invents_check" (
            "id"	INTEGER,
            "link"	INTEGER,
            PRIMARY KEY("id" AUTOINCREMENT)
        );"""
    try:
        qwe = cursor.execute(table)
        conn.commit()
        print('table created')
    except sqlite3.OperationalError:
        # print('table existst')
        pass

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
