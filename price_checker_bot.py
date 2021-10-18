import logging
from aiogram import Bot, Dispatcher, executor, types
from utils import price_checker_help as helper
from bs4 import BeautifulSoup
import time
from utils.utils import get_url
import sqlite3
from price_checker import get_price, set_account_status
import traceback

token = "2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM"

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def check_account_isset(link):
    cur.execute("select * from accounts where link = ?", (link, ))
    res = cur.fetchone()

    if res:
        return True
    return False

def add_account(link, soup, buy_price=0, sender=''):
    if check_account_isset(link):
        return 2

    got = False
    for i in range(10):
        first_price = get_price(soup)
        if not first_price:
            time.sleep(2)
            continue
        got = True
        break
    
    if not got:
        return 5
    
    sql = "insert into accounts(link, first_price, status, buy_price, added_by) values (?, ?, 0, ?, ?)"
    
    data = (link, first_price, buy_price, sender)
    try:
        cur.execute(sql, data)
        conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

    return first_price

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)

@dp.message_handler(commands=['status'])
async def change_status(message: types.Message):
    spl = message.text.split()
    if len(spl) != 3:
        # print(1)
        await message.reply("Ошибка, пример:\n/status https://lolz.guru/market/20961267/ 2")
        return
    if not helper.check_link_valid(spl[1]):
        # print(20)
        await message.reply("Ошибка, пример:\n/status https://lolz.guru/market/20961267/ 2")
        return
    
    set_account_status(spl[1], spl[2])

    await message.reply(f"Статус изменен на {spl[2]}")

@dp.message_handler(commands=['list'])
async def send_list(message: types.Message):
    cur.execute("select * from accounts where status=0")
    res = cur.fetchall()
    txt = ""
    for r in res:
        txt += f"{r['link']} - {r['first_price']}\n"
    
    await message.reply(txt)



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowere by fukc")

@dp.message_handler(commands=["help"])
async def help(message: types.Message):
    help = "Помощь:\nДля добавления аккаунта нужно просто отправить ссылку на аккаунт боту\n\nСписок доступных команд:\n/list - выводит список акков на проверке\n /help - помощь"

    await message.reply(help)

@dp.message_handler()
async def echo(message: types.Message):
    print(f"{message.text} from {message.from_user.first_name} {message.from_user.last_name}")

    spl = message.text.split(" ")
    if not helper.check_link_valid(spl[0]):
        # print(spl[0])
        await message.reply("что - то указано не так\nшаблон отправки:\n[ссылка на акк] [цена покупки аккаунта или ничего]\nпример:\nhttps://lolz.guru/market/1233321/ 5000")
        return
    if check_account_isset(spl[0]):
        await message.reply("Этот аккаунт уже чекается")
        return
    try:
        acc_page = BeautifulSoup(get_url(spl[0]).text, 'html.parser')
    except:
        print("ошибка при получении страницы с маркета")
        time.sleep(10)
        return

    if len(spl) == 2:
        if not helper.is_digit(spl[1]):
            await message.reply("что - то указано не так\nшаблон отправки:\n[ссылка на акк] [цена покупки аккаунта или ничего]\nпример:\nhttps://lolz.guru/market/1233321/ 5000")
            return
        res = add_account(spl[0], buy_price=spl[1], sender=message.from_user.first_name)
        if res != 2:
            await message.reply("аккаунт добавлен с ценой покупки = %s(текущая цена = %s)" % (spl[1], res))
        elif res == 5:
            await message.reply("Ошибка, попробуйте позже.")
        else:
            await message.reply("Этот аккаунт уже чекается")

        return
    elif len(spl) == 1:
        res = add_account(spl[0], acc_page, sender=message.from_user.first_name)
        if res != 2:
            await message.reply("аккаунт добавлен без цены покупки(текущая цена = %s)" % res)
        elif res == 5:
            await message.reply("ошибка, попробуй позже")
        else:
            await message.reply("Этот аккаунт уже чекается")
    else:
        await message.reply("что - то указано не так\nшаблон отправки:\n[ссылка на акк] [цена покупки аккаунта или ничего]\nпример:\nhttps://lolz.guru/market/1233321/ 5000")


if __name__ == '__main__':
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("crash")
            print(traceback.format_exc())
            time.sleep(5)
            