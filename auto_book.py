def book_account(self, account: MarketItemAccount) -> dict or None:
    market_id = account.link.split('/')[-2]

    link = f"https://lolz.guru/market/{market_id}/balance/check?price={account.cost}&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={self.xftoken}&_xfResponseType=json"
    # print(linkk)
    page = get_url(link)
    if not page:
        return None
    answer = json.loads(page.text)
    if 'error' in answer:
        print(answer['error'])
        return None
    return answer