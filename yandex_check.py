import traceback
from utils.utils import get_url
from utils import config
from bs4 import BeautifulSoup
import telebot
import time

bot = telebot.TeleBot(token=config.token)

min_amount = int(input("Минимальная сумма заявки: "))
link_for_check = input("ссылка: ")

def gg():
    url = link_for_check

    site = get_url(url)

    soup = BeautifulSoup(site.text, 'html.parser')

    reqs = soup.find_all("a", class_="request")

    for req in reqs:
        amount = req.find("span", class_="value").text
        if int(amount) > min_amount:
            bot.send_message(config.telegram_id, f'новая заяка на {amount} {link_for_check}')
    

while True:
    try:
        print('parsing xDxDxDxDxDxDxDxDxDxDxDxDxDxDxDxD')
        gg()
        time.sleep(5)
    except Exception as e:
        print(traceback.format_exc())
        bot.send_message(config.telegram_id, 'краш чекера юмани')