from openpyxl import load_workbook
import time

import requests
from utils import get_url
from bs4 import BeautifulSoup
wb = load_workbook(filename = 'new.xlsx', data_only=True)

sheet = wb['вывод инв']

import sqlite3

conn = sqlite3.connect('databases/test.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

accs = []

for i in range(5, 1000):
    ycheika = "E"+str(i)
    ycheikaa = "J"+str(i)
    # print(ycheika)
    link = (sheet[ycheika].value)
    profit = (sheet[ycheikaa].value)

    if link ==  None:
        continue
    # format = [link, profit]
    accs.append([link, profit])
    
def get_seller_nickname(link):
    try:
        soup = BeautifulSoup(get_url(link).text, 'html.parser')
        nickname = soup.find("div", class_="marketItemView--sidebarUser--Username").find("a", class_="username").text
        return nickname
    except AttributeError:
        return None
    except requests.exceptions.ConnectionError:
        try:
            time.sleep(2)
            soup = BeautifulSoup(get_url(link).text, 'html.parser')
            nickname = soup.find("div", class_="marketItemView--sidebarUser--Username").find("a", class_="username").text
            return nickname
        except requests.exceptions.ConnectionError:
            return None
        except AttributeError:
            return None
    except requests.exceptions.MissingSchema:
        return None
    # print(nickname)

def work():
    bad_accs = []
    cursor.execute("DELETE FROM sellers")
    conn.commit()

    for link, profit in accs:
        print(link)
        # if link == "lolz.guru":
        #     continue
        nick = get_seller_nickname(link)
        if not nick:
            bad_accs.append(link)
            continue

        cursor.execute("select * from sellers where nickname = ?", (nick,))
        res = cursor.fetchone()

        if res:
            sql = "update sellers set profit = profit + ?, accs = accs + 1 where nickname = ?"
            data = (int(profit), nick)
            try:
                cursor.execute(sql, data)
                # conn.commit()
                print("updated %s " % nick)

            except sqlite3.Error as error:
                print("Failed to update Python variable into sqlite table", error)

        else:
            sql = "insert into sellers(nickname, profit, accs) values (?, ?, ?)"
            data = (nick, profit, 1)
            try:
                cursor.execute(sql, data)
                # conn.commit()
                print("added new seller - %s" % nick)

            except sqlite3.Error as error:
                print("Failed to insert Python variable into sqlite table", error)

    conn.commit()
    time.sleep(1)

# work()

cursor.execute("select * from sellers order by profit asc")
res = cursor.fetchall()

sum = 0

for r in res:
    sum += r['profit']
    print("%s : %s : %s" % (r['nickname'], r['profit'], r['accs']))

print(sum)