import requests
import base64
import re
from bs4 import BeautifulSoup
import config




def getXenforoCookie():
    r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    return base64.b64decode(base64DfId).decode()

def get_url(url):
    """ returns page(requests object) """

    s = requests.Session()
    cookies = config.cookies
    # url = "https://lolz.guru/market/16461695/"

    # print(cookies)
    page = s.get(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=cookies)
    # print(page.cookies)
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
    cookies = config.cookies
    # url = "https://lolz.guru/market/16461695/"


    page = s.post(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}, cookies=cookies, data=data, timeout=100)
    return page

def get_user_id():
    """ returns user_id on lolz.guru """
    main_page = get_url("https://lolz.guru/")
    soup = BeautifulSoup(main_page.text, 'html.parser')
    # print(soup)
    asd = soup.find(id="AccountMenu")
    asdd =  asd.find_all("a")
    url_id = asdd[3]
    user_id = url_id.get("href").split("/")[2]
    
    return user_id