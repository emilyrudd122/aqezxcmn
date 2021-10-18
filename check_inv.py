from utils import get_url
from bs4 import BeautifulSoup

def get_price(link):
    soup = BeautifulSoup(get_url(link).text, 'html.parser')

    items = soup.find_all("div", class_="marketable")
    full = 0
    for item in items:
        price = float(item.get("data-value"))
        if price > 100:
            full += price
        else:
            break

    print(full)

get_price("https://lolz.guru/market/steam-value?link=https%3A%2F%2Flolz.guru%2Fmarket%2F20768744%2F&app_id=570")
