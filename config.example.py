import requests
import re
import base64

cokies = 'cookies'

# cookies = {'G_ENABLED_IDPS': 'google', ' xf_tfa_trust': 'tU6gqaK5aJj98D-BaFaba0RKSUC1a6eM', ' xf_user': '3764769,e162b958a9ee984b93a37a7820b120553a66368b', ' xf_logged_in': '1', ' timezoneOffset': '10800,0', ' xf_disable_market_warning_page': '1', ' _gid': 'GA1.2.836018498.1628774032', ' xf_last_read_article_date': '1627904520', ' _ga': 'GA1.1.1170466874.1625776137', ' xf_market_items_viewed': '18161807,18161996,17934252,18161982', ' df_id': getXenforoCookie(), ' xf_session': 'ccc0520b9e8fff02c44fcc010e58e547', ' xf_market_search_url': '/market/user/3764769/items', ' _ga_J7RS527GFK': 'GS1.1.1629912053.373.1.1629912163.0'}

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