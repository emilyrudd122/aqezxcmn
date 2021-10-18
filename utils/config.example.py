import requests
import re
import base64

cokies = 'cookies'

telegram_id = 123 # телеграм айди кому будут приходить сообщения
token = 'telegram bot token' # токен для бота телеграм
guarant_time = 4500 # время до конца гарантии в секундах
restart_script_interval = 270

# названия меток для ворка
guarant_tag = 'гарантия'
resell_tag = 'перепродать'
arbitrage_tag = 'написать арб'
guard_tag = 'гвард'
bot_sold_tag = 'перепродан'