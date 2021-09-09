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
sum = 0
async def check(session, url):
    global sum
    try:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

            resell_block = soup.find_all("div", class_="marketItemView--sameItem")
            for res_block in resell_block:
                resellers = res_block.find_all("a", class_="username")
                if resellers[0].text == 'NealCaffrey':
                    qweqwe = res_block.find("span", class_="marketIndexItem--icon--deleted")
                    if qweqwe:
                        print('account invalid')
                        sql = "update accounts set sell_price = ? where link = ?"
                        data = (0, url)
                        db.cur.execute(sql, data)
                    else:
                        price = int(res_block.find("span", class_="price").text.split()[0])
                        if price != 9999:
                            sold = res_block.find("span", class_="marketIndexItem--icon--paid")
                            if sold:
                                sum+=price
                                sql = "update accounts set sell_price = ? where link = ?"
                                data = (price, url)
                                db.cur.execute(sql, data)
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
        pass


async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), cookies=cokie, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/86.0.4240.75 Safari/537.36"}) as session:
        tasks = []
        rows = db.cur.execute("select * from accounts")

        for row in rows:
            line = row['link']
            try:
                link = line.split()[0]
                if line == '':
                    continue
            except IndexError:
                pass
            
            task = asyncio.create_task(check(session, link))
            tasks.append(task)
        await asyncio.gather(*tasks)
        


asyncio.run(main())
print('final sum = %d ' % sum)
asd = db.cur.execute("select * from accounts")
buy_sum = 0
for row in asd:
    try:
        buy_sum+=int(row['buy_price'])
    except TypeError:
        pass

print(buy_sum)
db.conn.commit()
