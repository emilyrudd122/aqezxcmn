import requests
import re
import base64

def getXenforoCookie():
    r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    return base64.b64decode(base64DfId).decode()

cokies = 'cookies'

asd = cokies.split(';')
ckies = {}
for qwe in asd:
    qq = qwe.split("=")
    if qq[0] == ' df_id':
        ckies[qq[0]] = getXenforoCookie()
        continue
    ckies[qq[0]] = qq[1]

cookies = ckies

telegram_id = 123 # телеграм айди кому будут приходить сообщения
token = '213' # токен для бота телеграм
guarant_time = 900 # время до конца гарантии в секундах
restart_script_interval = 270

# названия меток для ворка
guarant_tag = 'гарантия'
resell_tag = 'перепродать'
arbitrage_tag = 'написать арб'
guard_tag = 'гвард'
