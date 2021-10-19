import logging
from aiogram import Bot, Dispatcher, executor, types
import aiogram
from requests import check_compatibility
from utils import price_checker_help as helper
from bs4 import BeautifulSoup
import time
from utils.utils import get_url
import sqlite3
from price_checker import get_price, set_account_status
import traceback
from utils import config

token = "2095381518:AAHv9IxWYbMHvQuRWMHLNlTl5bYpYA5LoZM"

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def check_user(telegram_id):
    cur.execute("select * from users where telegram_id = ?", (telegram_id, ))
    asd = cur.fetchone()
    if asd:
        if asd['approve'] == 0:
            return False
        if asd['admin'] == 1:
            return 2
        return True
    return False

def check_account_isset(link):
    cur.execute("select * from accounts where link = ?", (link, ))
    res = cur.fetchone()

    if res:
        return True
    return False

def add_account(link, soup, buy_price=0, sender:types.Message=''):
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
    sql2 = "update users set accs_amount = accs_amount + 1 where telegram_id = ?"
    data = (link, first_price, buy_price, sender.from_user.id)
    data2 = (sender.from_user.id, )
    try:
        cur.execute(sql, data)
        conn.commit()
        cur.execute(sql2, data2)
        conn.commit()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

    return first_price

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)

def add_user(telegram_id, name):
    sql = "insert into users(telegram_id, name, accs_amount, notify, admin) values (?, ?, 0, 0, 0)"
    
    data = (telegram_id, name)
    try:
        cur.execute(sql, data)
        conn.commit()
        print("new user added")
        

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

def approve_user(telegram_id):
    try:
        cur.execute("update users set approve = 1 where telegram_id = ?", (telegram_id, ))
        conn.commit()
    except:
        print("user not approved")
        return False
    print("user approved")
    return True

async def check_user_and_answ(message):
    if check_user(message.from_user.id):
        return True
    else:
        await message.reply("Вы не зарегистрированы или ваша заявка пока что не одобрена, напишите /start")
        return False

@dp.message_handler(commands=['status'])
async def change_status(message: types.Message):
    if not check_user(message.from_user.id) == 2:
        return
    # print(check_user)
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
    if not await check_user_and_answ(message):
        return
    cur.execute("select * from accounts where status=0")
    res = cur.fetchall()
    txt = ""
    for r in res:
        txt += f"{r['link']} - {r['first_price']}\n"
    
    await message.reply(txt)

@dp.message_handler(commands=['newusers'])
async def send_new_users(message: types.Message):
    if not check_user(message.from_user.id) == 2:
        return
    cur.execute("select * from users where approve = 0")
    msg = ""
    for r in cur.fetchall():
        msg += f"{r['telegram_id']} -  {r['name']}"
    
    if msg != "":
        await message.reply(msg)
    else:
        await message.reply("нет новых заявок")

@dp.message_handler(commands=['approve'])
async def appr_user(message: types.Message):
    if not check_user(message.from_user.id) == 2:
        return
    spl = message.text.split()

    if not approve_user(spl[1]):
        await message.reply("Ошибка")
        return
    await message.reply("user approved")



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if check_user(message.from_user.id):
        await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowere by fukc")
    else:
        add_user(message.from_user.id, message.from_user.first_name)
        await bot.send_message(1647564460, "Новый юзер")
        await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowere by fukc")

@dp.message_handler(commands=["help"])
async def help(message: types.Message):
    if not await check_user_and_answ(message):
        return
    help = "Помощь:\nДля добавления аккаунта нужно просто отправить ссылку на аккаунт боту\n\nСписок доступных команд:\n/list - выводит список акков на проверке\n /help - помощь"
    if check_user(message.from_user.id) == 2:
        help += "\n\nAdmin commands:\n/newusers показывается неапрувленных юзеров\n/approve [user_id] аппрувит юзера"
    

    await message.reply(help)

@dp.message_handler()
async def echo(message: types.Message):
    if not await check_user_and_answ(message):
        return

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
        res = add_account(spl[0], buy_price=spl[1], sender=message)
        if res != 2:
            await message.reply("аккаунт добавлен с ценой покупки = %s(текущая цена = %s)" % (spl[1], res))
        elif res == 5:
            await message.reply("Ошибка, попробуйте позже.")
        else:
            await message.reply("Этот аккаунт уже чекается")

        return
    elif len(spl) == 1:
        res = add_account(spl[0], acc_page, sender=message)
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
            