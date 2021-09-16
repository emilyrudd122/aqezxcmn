import config
import sqlite3
import telebot
from utils import conn, cursor


bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")



# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    msg = message.text
    link = msg.split()[0]
    print(link)
    def check_link(link):
        sql = cursor.execute("select * from resell_price where link = ?", (link, )).fetchone()

        if sql:
            return 1
        return 0

    if check_link(link):
        bot.reply_to(message, "Для этого аккаунта уже установлена цена")
        return
    splitmsg = msg.split('/')
    if splitmsg[2] == "lolz.guru" and splitmsg[3] == 'market':
        acc_price = splitmsg[-1].split()[0]

        sql = "insert into resell_price(link, price) values (?, ?)"
        data = (link, acc_price)
        try:
            cursor.execute(sql, data)
            conn.commit()
            bot.reply_to(message, "Принято!")
            print("link added")

        except sqlite3.Error as error:
            print("Failed to insert Python variable into sqlite table", error)

def bot_run():
    bot.polling()
