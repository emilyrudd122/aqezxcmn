

def parse_xftoken():
    print("начинаю парсить xftoken")
    asd = get_url("https://lolz.guru/")
    print(asd)
    soup = BeautifulSoup(asd.text, 'html.parser')
    xftoken = soup.find('input', {'name':'_xfToken'})['value']
    print('token = %s' % xftoken)

    return xftoken

xftoken = parse_xftoken()

bot = telebot.TeleBot(config.market_bot_token)

conn = sqlite3.connect('databases/lolz_market_bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

async def main(loop):
    users = cur.execute("select * from users where approve = 1").fetchall()
    ids = []
    for user in users:
        ids.append(user['telegram_id'])


    
    async with aiohttp.ClientSession(loop=loop, headers=headers, cookies=cookies) as session:
        while True:

            # check_license()
            for i in range(100):
                cur.execute("select * from accounts where status=0 or status=5")
                res = cur.fetchall()
                if not res:
                    print('net akkov')
                    time.sleep(10)
                    continue
                links = []
                for r in res:
                    links.append([r['link'], r['first_price']])
                for link in links:

                    asyncio.ensure_future(check_account(session, link, ids))
                    await asyncio.sleep(0.5)
                        
                # await asyncio.sleep(0.4)

if __name__ == "__main__":
    while True:
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(main(loop))
            loop.run_forever()
        except:
            print(traceback.format_exc())
            print('creash')
            time.sleep(5)
        # time.sleep(3)