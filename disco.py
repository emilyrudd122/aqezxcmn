import time
import discord
from utils import config
import random
import json
from utils.utils import get_post, get_url
import requests
from bs4 import BeautifulSoup

def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    if not asd:
        return None
    soup = BeautifulSoup(asd.text, 'lxml')
    if "Please enable JavaScript and Cookies in your browser" in soup.text:
        print("Please enable JavaScript and Cookies in your browser")
        return None
    xftoken = soup.find('input', {'name':'_xfToken'})['value']

    return xftoken

def parse_inventory(link, xftoken):
    market_id = link.split('/')[-2]
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
        "link": link,
        "app_id": app_id,
        "_xfRequestUri": f"/market/steam-value?link=https%3A%2F%2Flolz.guru%2Fmarket%2F{market_id}%2F&app_id={app_id}",
        "_xfNoRedirect": 1,
        "_xfToken": xftoken,
        "_xfResponseType": "json"
    }
    parsed=False
    print("Начинаю парсить инв")
    for i in range(10):
        print(i)
        if not parsed:
            try:
                asd = get_post(post_url, data, headers, 5)
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


client = discord.Client()
xftoken = parse_xftoken()
guild_id = '609345136136028160' #kanava
@client.event
async def on_ready():
    print("Connected")

def get_info_acc(link):
    asd = get_url(link)
    soup = BeautifulSoup(asd.text, 'lxml')
    price = soup.find("span", class_="price").text.strip()
    name = soup.find("h1", class_="marketItemView--titleStyle").find("span").text
    try:
        rank = soup.find("img", class_="csgoRank").get("src")
    except AttributeError:
        rank = 'Без звания'

    wee = soup.find("div", class_="marketItemView--mainInfoContainer")
    counters = wee.find_all("div", class_="marketItemView--counters")
    otlega = counters[1].find_all("div", class_="counter")[0].text.strip().replace('\n', '').replace('Последняя активность', '')
    chasov = counters[1].find_all("div", class_="counter")[1].find("div", class_="label").text.strip()
    medals = 0
    try:
        medalss = soup.find("div", class_="steamCsgoMedals")
        mm = medalss.find_all("img", class_="medalImg")
        for medal in mm:
            # print(medal.get("src"))
            # medals += f' {medal.get("src")}'
            medals +=1
    except AttributeError:
        pass
    

    res = {
        'price': price,
        'name': name,
        'rank': rank,
        'otlega': otlega,
        'chasov': chasov,
        'medals': medals
    }

    return res

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]
    
    if message.content == '!dick':
        sm = random.randint(5,20)
        kek = await message.channel.send(f"проверка..... Your dick is {sm}см")
        
    def make_msg(info, inv=False, hide=False):
        response = f"""{info['name']}
Инвентарь = {inv if inv else 'Инвентарь парсится...'}руб.
Последний актив = {info['otlega']} |||  {info['chasov']} за 2 недели
{info['medals'] if int(info['medals'])>0 else '0'} медали

{info['rank'] if not hide else ''}
Цена = {info['price']} {message.content.split()[0]}
"""
        return response

    if message.content.startswith("https://lolz.guru/market/"):
        info = get_info_acc(message.content.split()[0])
        kek = await message.channel.send(make_msg(info), mention_author=True)
        # time.sleep(1)
        asd = parse_inventory(message.content.split()[0], xftoken)
        inv = asd['totalValueSimple']
        await kek.edit(content=make_msg(info, inv))
        
        

client.run(config.discord_token)