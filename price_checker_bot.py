import logging
from os import stat
from aiogram import Bot, Dispatcher, executor, types
import aiogram
from aiogram.types import message
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from requests import check_compatibility
from utils import price_checker_help as helper
from bs4 import BeautifulSoup
import time
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from utils.utils import get_url, get_post
import sqlite3
from price_checker import get_price, set_account_status
import traceback
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sys

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

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def add_user(telegram_id, name):
    sql = "insert into users(telegram_id, name, accs_amount, notify, admin, approve) values (?, ?, 0, 0, 0, 0)"
    
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

# @dp.message_handler(commands=['exit'])
# async def exit(message: types.Message):
#     if check_user(message.from_user.id) == 2:
#         sys.exit()

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

@dp.message_handler(commands=['announce'])
async def ann(message: types.Message):
    if check_user(message.from_user.id) == 2:
        ids = [config.telegram_id, "1243095585", "473485315", "578827447"]
        for id in ids:
            await bot.send_message(id, "пропишите /start")


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

class Buy_Acc(StatesGroup):
    confirm_buy = State()
    check_payment = State()
    buy = State()




@dp.callback_query_handler(lambda c: c.data and c.data.startswith('buy'))
async def buy_callback(callback_query: types.CallbackQuery, state: FSMContext):
    res = callback_query.data.split()
    if check_buying(res[1]):
        await bot.send_message(callback_query.from_user.id, 'Этот аккаунт уже покупают')
        return
    
    start_buying(res[1])

    
    async with state.proxy() as data:
        data['link'] = res[1]
        data['cost'] = res[2]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Да", "Нет")

    await Buy_Acc.confirm_buy.set()

    await bot.send_message(callback_query.from_user.id, f"Вы хотите купить аккаунт? {res[1]}", reply_markup=markup)

# @dp.message_handler(state='*', commands='отмена')
# @dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
# async def cancel_handler(message: types.Message, state: FSMContext):
#     """
#     Allow user to cancel any action
#     """
#     current_state = await state.get_state()
#     if current_state is None:
#         await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())
#         return

#     logging.info('Cancelling state %r', current_state)
#     # Cancel state and inform user about it
#     async with state.proxy() as data:
#         print(data)
#         if data['link'] != '':
#             print(data['link'])
#             stop_buying(data['link'])
#     await state.finish()
#     # And remove keyboard (just in case)
#     await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text not in ["Да", "Нет"], state=Buy_Acc.confirm_buy)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Неправильный вариант ответа")

@dp.message_handler(state=Buy_Acc.confirm_buy)
async def confirmbuy(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == "Да":
            await Buy_Acc.check_payment.set()
            txt = f"Для покупки аккаунта отправьте сюда(https://lolz.guru/zxxxcqq/) сумму = {data['cost']}\n\nПосле отправки нажмите кнопку \"Проверить оплату\""
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("Проверить оплату", "Отмена")
            await Buy_Acc.buy.set()
            await message.reply(txt, reply_markup=markup)
        if message.text == "Нет":
            current_state = await state.get_state()
            if current_state is None:
                return

            logging.info('Cancelling state %r', current_state)
            # Cancel state and inform user about it
            stop_buying(data['link'])
            await state.finish()
            # And remove keyboard (just in case)
            await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())

def check_payment(payer, pp):
    print(f"ищу {payer} с {pp}")
    kk = get_url("https://lolz.guru/market/user/3764769/payments?type=money_transfer")

    soup = BeautifulSoup(kk.text, 'html.parser')

    pays = soup.find_all("div", class_="item")
    for pay in pays:
        amount = pay.find("div", class_="amountChange").text.split()
        sender = pay.find("a", class_="username").text.lower()
        # print(f"{sender} - {amount}")
        try:
            data = pay.find("div", class_="paymentFooter").find("abbr", class_="DateTime").get("data-diff")
        except AttributeError:
            break
        
        # print(data)
        if len(amount) > 1:
            # print(amount)
            if int(amount[1]) == int(pp) and payer == sender and int(data) < 600:
                print("Платеж найден")
                return True
            
    return False


def buy_account(link):
    confirm_buy_link = link + 'confirm-buy'
    data = {
        "_xfToken": "3764769,1634793573,06fb428c2ebd74695ea34c9c527280912fc7b800",
        "_xfConfirm": '1'
    }
    get_post(confirm_buy_link, data)

@dp.message_handler(state=Buy_Acc.buy)
async def checkpayment(message: types.Message, state: FSMContext):
    if message.text == "Проверить оплату":
        async with state.proxy() as data:
            users = {
                1243095585: 'shkila',
                578827447: 'ihate4',
                473485315: 'sashasty',
            }
            if not check_payment(users[message.from_user.id], data['cost']):
                # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                # markup.add("Проверить оплату", "Отмена")
                await message.reply("Платеж не найден")
            else:
                buy_account(data['link'])
                await message.reply("Ваш платеж найден, аккаунт куплен, для получения писать сюда - @zxxxcqq", reply_markup=ReplyKeyboardRemove())

                logging.info('Куплен аккаунт')
                # Cancel state and inform user about it
                stop_buying(data['link'])
                await state.finish()
                
                # And remove keyboard (just in case)
                # await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())
    elif message.text == "Отмена":

        current_state = await state.get_state()
        if current_state is None:
            return

        logging.info('Cancelling state %r', current_state)
        # Cancel state and inform user about it
        async with state.proxy() as data:
            stop_buying(data['link'])
        await state.finish()
        # And remove keyboard (just in case)
        await message.reply('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())


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
            