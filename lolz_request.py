#! /usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from logging import log
from bs4 import BeautifulSoup
from loguru import logger
import json
import telebot
import config
import steam.webauth as wa
import time
from utils import get_url, get_post, display_time, get_user_id

logger.add("logs/file_{time}.log", rotation="5 MB")

logger.info("cкрипт запущен")


class LolzWorker():

    def __init__(self):
        self.xftoken = ''
        self.guarant_tag = ''
        self.resell_tag = ''
        self.arbitrage_tag = ''
        self.guard_tag = ''
        self.tb = telebot.TeleBot(config.token)
        self.link = "" 
        self.user_id = get_user_id()

    def send_message(self, message):
        """ отправляет сообщение админу в тг с {message}"""
        try:
            now = datetime.now()
            t = now.strftime("%H:%M:%S")
            self.tb.send_message(config.telegram_id, "[%s] %s" % (t, message))
        except:
            logger.error("сообщение в тг не отправлено")

    def remove_tag(self, market_link, tag_id):
        """market_link format = https://lolz.guru/market/10643456/"""
        data = {
            "_xfRequestUri": "/market/user/%s/orders" % self.user_id,
            "_xfNoRedirect": "1",
            "_xfToken": self.xftoken,
            "_xfResponseType": "json"
        }
        link_for_del_tag = market_link+"tag/delete?tag_id=%s" % tag_id
        clear_guarant_tag = get_post(link_for_del_tag, data)

        logger.info('тег убран с %s' % market_link)
    
    def add_tag(self, market_link, tag_id):
        data = {
            "_xfRequestUri": "/market/user/%s/orders" % self.user_id,
            "_xfNoRedirect": "1",
            "_xfToken": self.xftoken,
            "_xfResponseType": "json"
        }
        link_for_arb_tag = market_link + "tag/add?tag_id=%s" % tag_id
        add_arb_mark = get_post(link_for_arb_tag, data)

        logger.info('добавлен тег к  %s' % market_link)


    def parse_xftoken(self):
        # print("начинаю парсить xftoken")
        logger.info("начинаю парсить xftoken")
        asd = get_url("https://lolz.guru/")
        soup = BeautifulSoup(asd.text, 'html.parser')
        self.xftoken = soup.find('input', {'name':'_xfToken'})['value']
        logger.info('token = %s' % self.xftoken)

    def parse_tags_id(self):
        url = "https://lolz.guru/market/user/tags?=&_xfRequestUri=/market/user/%s/orders&_xfNoRedirect=1&_xfToken=%s&_xfResponseType=json" % (self.user_id, self.xftoken)

        asd = get_url(url)
        answer = json.loads(asd.text)

        html = answer['templateHtml']
        soup = BeautifulSoup(html, 'html.parser')

        tags = soup.find_all("span", class_="singleTag")[:-1]
        i=0
        for tag in tags:
            tag_name = tag.text
            tag_id = tag.get("class")[2][3:]
            if config.guarant_tag.lower() == tag_name.lower():
                self.guarant_tag = tag_id
                i+=1
            if config.resell_tag.lower() == tag_name.lower():
                self.resell_tag = tag_id
                i+=1
            if config.arbitrage_tag.lower() == tag_name.lower():
                self.arbitrage_tag = tag_id
                i+=1
            if config.guard_tag.lower() == tag_name.lower():
                self.guard_tag = tag_id
                i+=1
            

        if i != 4:
            logger.error("не все теги были спаршены, проверьте правильно ли вы все создали+указали")
            exit()


    def get_time_till_guarantee(self, market_item):
        vremya_pokupki_accounta = market_item.find("div", class_="marketIndexItem--otherInfo").find("abbr", class_="DateTime").get("data-time")
        guarantee_time = market_item.find("span", class_="smallGuarantee")
        if guarantee_time == None:

            guarantee_time = market_item.find("span", class_="simpleGurantee")
            if guarantee_time == None:
                guarantee_time = market_item.find_all("span", class_="stat")[1].find("span", class_="extendedGuarantee")

        if guarantee_time == None:
            logger.info("похоже что гарантия отменена")
            # print("похоже что гарантия отменена")
            return 0

        vremya_garantii = int(guarantee_time.text.split()[0])
        if vremya_garantii == 3:
            vremya_garantii = 72

        vremya_konca_garantii = int(vremya_pokupki_accounta) + int(vremya_garantii)*3600

        ostalos_vremeni_dokonca = vremya_konca_garantii-time.time()
        
        return ostalos_vremeni_dokonca

    def parse_inventory(self, market_id):
        # парс инвентаря ксго
        link = f"https://lolz.guru/market/{market_id}/update-inventory?app_id=730&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={self.xftoken}&_xfResponseType=json"
        answer = json.loads(get_url(link).text)
        if answer['_redirectStatus'] == 'ok':
            logger.info('спаршен инвентарь для https://lolz.guru/market/%s' % market_id)

        # link = f"https://lolz.guru/market/{market_id}/update-inventory?app_id=753&=&_xfRequestUri=/market/{market_id}/&_xfNoRedirect=1&_xfToken={self.xftoken}&_xfResponseType=json"

    def resell_account(self, market_id, nazvanie, price):
        logger.info(f"Перепродаю аккаунт https://lolz.guru/market/{market_id} + nazvanie = {nazvanie} + price={price}")
        market_id = int(market_id)
        market_link = "https://lolz.guru/market/%d/" % market_id
        page = get_url(market_link)
        soup = BeautifulSoup(page.text, 'html.parser')

        login = soup.find("span", id="loginData--login").text
        password = soup.find("span", id="loginData--password").text

        resell_t = soup.find("a", class_="resellButton").get("href").split("=")[1]

        data = {
            "category_id": "1",
            "title": "%s" % nazvanie,
            "title_en": "check",
            "auto_translate": "1",
            "price": "%s" % price,
            "allow_ask_discount": "on",
            "extended_guarantee": "0",
            "description_html": "<p><br></p>",
            "_xfRelativeResolver": "https://lolz.guru/market/%d/resell?t=%d" % (int(market_id), int(resell_t)),
            "information_html": "<p><br></p>",
            "_xfToken": self.xftoken,
            "t": "%d" % int(resell_t),
            "_xfConfirm": "1",
            "submit": "Перейти+к+добавлению+товара",
            "_xfRequestUri": "/market/%d/resell?t=%d" % (int(market_id), int(resell_t)),
            "_xfNoRedirect": "1",
            "_xfResponseType": "json",
        }

        first_link = "https://lolz.guru/market/%d/resell" % market_id
        qwe = get_post(first_link, data)
        asd = json.loads(qwe.content)

        marketqq = asd['_redirectTarget'].split("/")[4]
        answer = asd['_redirectMessage']


        data = {
            "login": login,
            "password": password,
            "login_password":"",
            "_xfToken": self.xftoken,
            "resell_item_id": market_id,
            "random_proxy": "1",
            "_xfRequestUri": "/market/%d/goods/add?t=%d&resell_item_id=%d" % (int(marketqq), int(resell_t), market_id),
            "_xfNoRedirect": "1",
            "_xfResponseType": "json",
        }

        second_link = "https://lolz.guru/market/%d/goods/check" % int(marketqq)
        asd = get_post(second_link, data)
        answer = json.loads(asd.text)
        logger.info(answer)

        try:
            if answer['error']:
                error_text = answer['error'][0]
                q = ""
                for a in error_text.split()[0:4]:
                    q = q + a

                if q.lower() == "УВаснетправ".lower():
                    # print("ошибка у вас нет прав %d" % (market_id))
                    logger.error("ошибка у вас нет прав %d" % (market_id))
                    return
                if error_text == 'steam_captcha':
                    logger.info('вышла капча стима')
                    flag = True
                    i=0
                    while flag and i<=7:
                        asd = get_post(second_link, data)
                        answer = json.loads(asd.text)
                        if answer['error'][0] != 'steam_captcha':
                            logger.info("получилось выложить аккаунт после капчи")
                            self.send_message("выложен акккаунт после капчи %s" % (market_link))
                            flag = False
                        i+=1
                    if i>7:
                        logger.error('не получилось выложить акк(капча стима при проверке)')
                        return
        except KeyError:
            self.send_message("выложен акккаунт %s" % (market_link))
            logger.info(answer)
        self.remove_tag(market_link, self.guarant_tag) 
        time.sleep(0.3)
        self.remove_tag(market_link, self.resell_tag) 
        time.sleep(0.3)
        self.remove_tag(market_link, 13) 
        self.parse_inventory(marketqq)
        logger.info("конец resell")
        # time.sleep(20)

    def resell_accounts(self) -> None:
        """перепродает акки с меткой перепродать, без метки гарантии"""
        link_for_resell_accounts = "https://lolz.guru/market/user/%s/orders?order_by=pdate_to_down&tag_id[]= %s" % (self.user_id, self.resell_tag)
        qwe = get_url(link_for_resell_accounts)

        soup = BeautifulSoup(qwe.text, 'html.parser')

        market_items = soup.find_all("div", class_="marketIndexItem")
        accs_for_resell = []
        for market_item in market_items:
            market_link = market_item.find("a", class_="marketIndexItem--Title").get('href')
            full_market_link = "https://lolz.guru/" + market_link
            divv = market_item.find("div", class_="marketIndexItem--otherInfo")
            tags_div = divv.find("div", class_="itemTags").find_all("span", class_="tag")[:-1]
            flag = False
            if tags_div[0].text.lower() == 'невалид':
                logger.info("акк невалид, не могу перепродать %s " % full_market_link)
                self.send_message('этот аккаунт не валид. не могу его перепродать %s ' % (full_market_link))
                return
            for tag in tags_div:
                if tag.text.lower() == config.guarant_tag.lower():
                    flag = True
            
            if not flag:
                accs_for_resell.append(full_market_link)
        
        for acc in accs_for_resell:
            asd = self.check_valid(acc)
            if asd == 1:
                logger.info("акк валид можно перепродавать %s" % acc)
            elif asd == 2:
                logger.info("акк валид можно перепродавать %s" % acc)
            else:
                return
            
            market_id = acc.split('/')[-2]
            self.resell_account(market_id, 'resell by bot', '9999')
        






    def get_account_marks(self, message='123'):
        # self.link = "https://lolz.guru/market/user/3764769/orders?order_by=pdate_to_down&tag_id[]=%s" % self.guarant_tag
        asd = get_url(self.link)
        message = message
        soup = BeautifulSoup(asd.text, 'html.parser')
        try:
            last_page = int(soup.find('div', class_="PageNav").get("data-last"))
        except AttributeError:
            last_page = 1
        market_items = soup.find_all("div", class_="marketIndexItem")


        for i in range(1, last_page+1):
            linkk = self.link + "&page=%d" % i
            logger.info("Парсирую аккаунты")
            qwe = get_url(linkk)
            time.sleep(0.5)
            soupp = BeautifulSoup(qwe.text, 'html.parser')
            market_items = soupp.find_all('div', class_="marketIndexItem")
            
            i = 0
            for market_item in market_items:
                market_link = market_item.find("a", class_="marketIndexItem--Title").get('href')
                full_market_link = "https://lolz.guru/" + market_link
                divv = market_item.find("div", class_="marketIndexItem--otherInfo")
                tags_div = divv.find("div", class_="itemTags").find_all("span", class_="tag")[:-1]

                time_till_end_guarant = self.get_time_till_guarantee(market_item)
                if time_till_end_guarant < 0:
                    data = {
                        "_xfRequestUri": "/market/user/3764769/orders",
                        "_xfNoRedirect": "1",
                        "_xfToken": self.xftoken,
                        "_xfResponseType": "json"
                    }
                    self.remove_tag(full_market_link, self.guarant_tag)
                    logger.info("На аккаунте %s убрана метка гарантии(она закончилась)" % full_market_link)
                    self.send_message("Закончилась гарантия на %s, метка убрана" % full_market_link)
                        
                if tags_div[0].text.lower() == "Невалид".lower():
                    if i == 0:
                        message += "\n\nНевалид аккакунты:\n"
                        i=1
                    message+="%s\n" % full_market_link
                    logger.info("Убираю все теги с аккаунта %s(он невалид)" % full_market_link)
                    for div in tags_div[1:]:
                        tag_id = div.get("class")[1][3:]
                        data = {
                            "_xfRequestUri": "/market/user/3764769/orders",
                            "_xfNoRedirect": "1",
                            "_xfToken": self.xftoken,
                            "_xfResponseType": "json"
                        }
                        self.remove_tag(full_market_link, tag_id)
                    self.add_tag(full_market_link, self.arbitrage_tag)

                    if time_till_end_guarant>0:
                        seller_nickname = divv.find("a", class_="username").text
                        account_price = market_item.find("div", class_="marketIndexItem--Price").find("span", class_="Value").text
                        data = {
                            "as_responder": seller_nickname,
                            "as_is_market_deal": 1,
                            "as_market_item_link": full_market_link,
                            "as_amount": account_price,
                            "as_evidence": "res",
                            "title": '',
                            "message_html": "<p>res</p>",
                            "_xfRelativeResolver": "https://lolz.guru/forums/239/create-thread?market_item_id=%s" % full_market_link.split("/")[-1],
                            "tags": '',
                            "watch_thread": 1,
                            "watch_thread_state": 1,
                            "poll[question]": '',
                            "poll[responses][]": '',
                            "poll[responses][]": '',
                            "poll[max_votes_type]": "single",
                            "poll[change_vote]": 1,
                            "poll[view_results_unvoted]": 1,
                            "_xfToken": self.xftoken,
                            "_xfRequestUri": "/forums/239/create-thread?market_item_id=%s" % full_market_link.split("/")[-1],
                            "_xfNoRedirect": 1,
                            "_xfToken": self.xftoken,
                            "_xfResponseType": "json",
                        }
                        asd = get_post("https://lolz.guru/forums/arbitrage/add-thread", data)
                        print(json.loads(asd.text))

                        logger.info("Написал арбитраж на акк - %s (таймаут минута)" % full_market_link)
                        self.send_message("Написан арбитраж на %s" % (full_market_link))
                    else:
                        logger.info("Арбитраж на аккаунт %s не написан, так как закончилась гарантия, нужно проверить аккаунт в ручную")
                        self.send_message("Арбитраж на аккаунт %s не написан, так как закончилась гарантия, нужно проверить аккаунт в ручную")
                    time.sleep(60)
        
        return message 

    def check_valid(self, link):
        """принимает линк в формате https://lolz.guru/market/17946602/"""
        
        page = get_url(link)
        soup = BeautifulSoup(page.text, 'html.parser')

        tags = soup.find("div", class_="itemTags").find_all("span", class_="tag")[:-1]

        guard = False
        for tag in tags:
            if tag.text.lower() == config.guard_tag.lower():
                guard = True
                logger.info("Проверяю акк с гвардом на валид")
                login = soup.find("span", id="loginData--login").text
                password = soup.find("span", id="loginData--password").text

                user = wa.WebAuth(login)

                try:
                    user.login(password)
                except wa.LoginIncorrect:
                    self.send_message("(guardcheck) нашел невалид аккаунт %s" % link)
                    logger.error('нашел невалид аккаунт %s' % link)
                except wa.CaptchaRequired:
                    self.send_message("(guardcheck)Капча стима, не могу чекнуть акк на валид %s" % link)
                    logger.error("не могу чекнуть акк, нужна капча, пишите NealCaffrey")
                except wa.TwoFactorCodeRequired:
                    logger.info("валид аккаунт %s" % link)
                
                return
                    
        if guard:
            return


        link_for_check = link + "check-account?hide_info=1"
        market_id = link.split('/')[-1]
        data = {
            '_xfToken': self.xftoken,
            'random_proxy': 0,
            '_xfRequestUri': '/market/%s/validate' % market_id,
            '_xfNoRedirect': 1,
            '_xfToken': self.xftoken,
            '_xfResponseType': 'json'
        }
        logger.info("Проверяю аккаунт %s на валид" % link)
        asd = get_post(link_for_check, data)

         

        answer = json.loads(asd.text)
        try:
            if answer['error']:
                asd = answer['error'][0]
                q = ""
                for a in asd.split()[0:4]:
                    q = q + a

                if q.lower() == "УВаснетправ".lower():
                    logger.info("Пока что на валид нельзя проверить, нужно подождать некоторое время(%s)" % (market_id))
                    return 2
                if answer['error'][0] == 'steam_captcha':
                    logger.info("вышла капча стима")
                    flag = True
                    i=0
                    while flag and i<=7:
                        qwe = get_post(link_for_check, data) 
                        answer = json.loads(qwe.text)
                        if answer['error'][0] != 'steam_captcha':
                            logger.info('получилось проверить на валид после капчи')
                            flag = False
                            return 1
                        i+=1
                    if i>7:
                        logger.info('не получилось проверить на валид, иду дальше')
                        return 0
        except KeyError:
            print(answer)
            return 1
    
    def error(self):
        """отправляет письмо помощи"""
        self.send_message("GARANT CHECKER: СКРИПТ ПЕРЕСТАЛ РАБОТАТЬ, нужен перезапуск")
        

    @logger.catch
    def main(self):
        # Здесь начинается парсинг аккаунтов по указанной ссылке
        self.parse_xftoken()
        self.parse_tags_id()


        self.link = "https://lolz.guru/market/user/%s/orders?order_by=pdate_to_down&tag_id[]=%s" % (self.user_id, self.guarant_tag)
        wqe = get_url(self.link)
        soup = BeautifulSoup(wqe.text, 'html.parser')
        try:
            last_page = int(soup.find('div', class_="PageNav").get("data-last"))
        except AttributeError:
            last_page = 1

        accounts = []

        message = ""
        for i in range(1, last_page+1):
            linkk = self.link + "&page=%d" % i
            logger.info("парсирую аккаунты")
            qwe = get_url(linkk)
            time.sleep(0.5)
            soupp = BeautifulSoup(qwe.text, 'html.parser')
            market_items = soupp.find_all('div', class_="marketIndexItem")
            

            for market_item in market_items:
                market_link = market_item.find("a", class_="marketIndexItem--Title").get('href')
                full_market_link = "https://lolz.guru/" + market_link

                ostalos_vremeni_dokonca = self.get_time_till_guarantee(market_item)
                if ostalos_vremeni_dokonca < 0:
                    # TODO: если гарантия закончилась, сделать проверку на то был ли акк валид(через страницу history) или о нем не было инфы
                    accounts.append((full_market_link, 0))
                else:
                    accounts.append((full_market_link, int(ostalos_vremeni_dokonca)))

            logger.info("аккаунты спаршены")


        # функция для сортировки
        def takeSecond(elem):
            return elem[1]

        accounts.sort(key=takeSecond)

        message = ""
        for acc in accounts:
            if acc[1] == 0:
                message = message + "\n%s %s" % (acc[0], "гарантия закончилась")
                continue
            message = message + "\n%s %s" % (acc[0], display_time(acc[1]))

        logger.info("- - - - начинаю проверку аккаунтов на валид")
        for acc in accounts:
            if acc[1] < int(config.guarant_time) and acc[1] != 0:
                self.check_valid(acc[0])
            else:
                if acc[1] == 0:
                    logger.info("акк 0")
                else:
                    logger.info("аккаунт не подходит под критерии проверки на валид")
        logger.info("все аккаунты проверены")
        logger.info("начинаю получать статусы аккаунтов(валид/невалид)")
        msg = self.get_account_marks(message)
        self.resell_accounts()
        if msg != "":
            self.send_message(msg)
            logger.info("отправлено сообщение в телеграм")
            logger.info("скрипт завершен")
        else:
            print("msg == ''")
            logger.info("скрипт завершен")

doit = LolzWorker()
i = 0
while True:
    try:
        doit.main()
        logger.info("Перезапуск через %s секунд" % config.restart_script_interval)
        time.sleep(config.restart_script_interval)
    except:
        logger.error("скрипт крашнулся, жду 20 сек и перезапускаю")
        i+=1
        if i > 5:
            doit.error()
            i = 0
        time.sleep(20)
        continue