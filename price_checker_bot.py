import logging
from os import stat
from aiogram import Bot, Dispatcher, executor, types
from requests import check_compatibility
from utils import price_checker_help as helper
from bs4 import BeautifulSoup
import time
from utils.utils import get_url, get_post
import sqlite3
from new_price_checker import get_price, set_account_status
import traceback
from utils import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage

token = config.market_bot_token

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def check_user_exists(telegram_id):
    cur.execute("select * from users where telegram_id = ?", (telegram_id, ))
    asd = cur.fetchone()
    if asd:
        return True
    return False


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

def stop_buying(link):
    try:
        cur.execute("update accounts_check set buying = 0 where link = ?", (link, ))
        conn.commit()
    except:
        print(f"error when starting buying {link}")
        return False
    print(f"started buying {link}")
    return True

def start_buying(link):
    try:
        cur.execute("update accounts_check set buying = 1 where link = ?", (link, ))
        conn.commit()
    except:
        print(f"error when starting buying {link}")
        return False
    print(f"started buying {link}")
    return True

def check_buying(link):
    cur.execute("select * from accounts_check where link = ?", (link, ))
    res = cur.fetchone()
    if res['buying']:
        if int(res['buying']) == 1:
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


def add_user(telegram_id, name):
    sql = "insert into users(telegram_id, name, accs_amount, notify, admin, approve) values (?, ?, 0, 0, 0, 0)"
    
    data = (telegram_id, name)
    try:
        cur.execute(sql, data)
        conn.commit()
        print("new user added")
        

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)

async def approve_user(telegram_id):
    try:
        cur.execute("update users set approve = 1 where telegram_id = ?", (telegram_id, ))
        conn.commit()
        await bot.send_message(telegram_id, "Регистрация подтверждена")
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

@dp.message_handler(commands=['new_users'])
async def new_users(message: types.Message):
    if not check_user(message.from_user.id) == 2:
        return

    cur.execute("select * from users where approve=0")
    not_approved_users = cur.fetchall()
    if not_approved_users:
        for user in not_approved_users:
            msg = f"{user['telegram_id']} - {user['name']}"
            await bot.send_message(message.from_user.id, msg)
    else:
        await bot.send_message(message.from_user.id, "Нет новых заявок")
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


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if check_user_exists(message.from_user.id) == True:
        if check_user(message.from_user.id) == 2:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["/list", "/new_users"]
            keyboard.add(*buttons)
            await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowered by zxxxcqq", reply_markup=keyboard)
        else:
            await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowered by zxxxcqq")

    else:
        add_user(message.from_user.id, message.from_user.first_name)
        await bot.send_message(1647564460, "Новый юзер")
        await message.reply("Привет я бот для маркета, список функций доступен по команде /help\n\nPowere by zxxxcqq")

@dp.message_handler(commands=["book"])
async def book_market(message: types.Message):
    if check_user(message.from_user.id) != 2:
        return
    cur.execute("select * from settings where id = 1")
    asd = cur.fetchone()

    if asd['book_market'] == 1:
        await message.reply("Бронирование маркет выключено")
        cur.execute("update settings set book_market = 0 where id = 1")
        conn.commit()
    elif asd['book_market'] == 0:
        await message.reply("Бронирование маркет включено")
        cur.execute("update settings set book_market = 1 where id = 1")
        conn.commit()


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
        res = add_account(spl[0], acc_page, buy_price=spl[1], sender=message)
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
            