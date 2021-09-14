from bs4 import BeautifulSoup
import requests
import re
import base64

def getXenforoCookie():
    r = requests.get('https://lolz.guru/process-qv9ypsgmv9.js', headers={'User-Agent':'Mozilla/5.0'})
    cookieArray = re.search('^var _0x\w+=(.*?);', r.text).group(1)
    base64DfId = eval(cookieArray)[-1]
    return base64.b64decode(base64DfId).decode()

cookie = {
    'df_id': getXenforoCookie(),
    'xf_user': '',
    'xf_tfa_trust': ''
}

r=requests.get('https://lolz.guru/logout/', headers={'User-Agent':'Mozilla/5.0'}, cookies=cookie)
# print(r.text)
soup = BeautifulSoup(r.text, 'html.parser')
xftoken = soup.find('input', {'name':'_xfToken'})['value']
print(xftoken)