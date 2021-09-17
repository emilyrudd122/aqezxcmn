import sqlite3

from bs4 import BeautifulSoup
from utils import get_url, get_post
from loguru import logger
import asyncio
import aiohttp
import utils
import db

cokie = utils.make_coki()

def check_exist(link):
    db.cur.execute("select link from accounts where link = ?", (link))

    res = db.cur.fetchone()

    if res:
        print("this link already in db")
# sum = 0
async def check(session, url):
    # global sum
    
    try:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

            resell_block = soup.find_all("div", class_="marketItemView--sameItem")
            for res_block in resell_block:
                resellers = res_block.find_all("a", class_="username")
                if resellers[0].text == 'NealCaffrey':
                    # print(f"{url} - account resold")
                    qweqwe = res_block.find("span", class_="marketIndexItem--icon--deleted")
                    if qweqwe:
                        print(f'{url} - account invalid')
                        sql = "update accounts set sell_price = ? where link = ?"
                        data = (0, url)
                        db.cursor.execute(sql, data)
                    else:
                        price = int(res_block.find("span", class_="price").text.split()[0])
                        if price != 9999:
                            sold = res_block.find("span", class_="marketIndexItem--icon--paid")
                            if sold:
                                # sum+=price
                                print(f'{url} sold for {price}')
                                sql = "update accounts set sell_price = ? where link = ?"
                                data = (price, url)
                                db.cursor.execute(sql, data)
                            else:
                                print(url)
                        # print('price = %s' % price)

            # try:
            #     qww = soup.find("h1", class_="marketItemView--titleStyle")
            #     qq = qww.find("span", class_="marketIndexItem--icon--deleted")
            #     price = soup.find("span", class_="price").text.split()[0]
            #     if qq:
            #         pass
            #     else:
            #         sum += int(price)
            # except AttributeError:
            #     asd = soup.find("div", class_="errorOverlay")
    except aiohttp.client_exceptions.InvalidURL:
        print("invalid url")
        pass


async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), cookies=cokie, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}) as session:
        tasks = []
        rows = db.cursor.execute("select * from accounts").fetchall()
        i=0
        for row in rows:
            line = row['link']
            if row['sell_price'] == 0:
                continue
            try:
                link = line.split()[0]
                if line == '':
                    continue
            except IndexError:
                pass
            
            task = asyncio.create_task(check(session, link))
            tasks.append(task)
            i+=1
            if i==6:
                break
        await asyncio.gather(*tasks)
        


asyncio.run(main())
asd = db.cursor.execute("select * from accounts")
buy_sum = 0
sell_sum = 0
for row in asd:
    try:
        buy_sum+=int(row['buy_price'])
        sell_sum+=int(row['sell_price'])
    except TypeError:
        pass

print(buy_sum)
print(sell_sum)
db.conn.commit()
