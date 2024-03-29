import requests
from enum import Enum
#from requests import exceptions
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from http import HTTPStatus
import re
import unicodedata
from collections import defaultdict
import concurrent.futures
#from circuitbreaker import circuit
#from circuitbreaker import CircuitBreaker
#from html.parser import HTMLParser
#from lxml.etree import tostring
#class MyCircuitBreaker(CircuitBreaker):
#    FAILURE_THRESHOLD = 3
#    RECOVERY_TIMEOUT = 20
#    EXPECTED_EXCEPTION = requests.exceptions.RequestException

from misc.class_bcolors import *
from class_store_config import *
#from Class_push_send_log import *
from notifications.push.Push_notifications import *
from class_settings import *
from class_aux import *

from stores.game_store import *    

def send_push(message: str, title: str, url_title: str, url: str, destinataries):
    if settings.disablePushForAll: return

    for to in destinataries:
        #https://pushover.net/api
        #settings.group_by_store[item['store']].append(item)
        delayBetween = destinataries[to].delayBetween_seconds
        pushkey = settings.users_pushKeys[to]

        unique_key_push_item:str = f'{pushkey}_{url}'
        item_push_send_log = Class_push_send_log(pushkey, unique_key_push_item)

        push_sent_offset:int = 0
        if aux.push_send_log[unique_key_push_item].unique_store_item is not None:

            if aux.push_send_log[unique_key_push_item].unique_store_item == unique_key_push_item:
                
                if aux.push_send_log[unique_key_push_item].latest_send is None:
                    send_push = True
                else:
                    push_sent_offset = (datetime.utcnow() - aux.push_send_log[unique_key_push_item].latest_send).total_seconds() 

                    if push_sent_offset <= delayBetween:
                        send_push = False
                    else:
                        send_push = True
            else:
                send_push = True

        else:
            aux.push_send_log[unique_key_push_item] = item_push_send_log
            send_push = True
        #Class_push_send_log.push_key = pushkey
        #Class_push_send_log.first_send
        #Class_push_send_log.latest_send
        #Class_push_send_log.unique_store_item
        if settings.enableLogInfo:
            print (f'\t{to} send_push = {send_push} seconds ({push_sent_offset}) delay={delayBetween}')
        
        if send_push == True:
            aux.push_send_log[unique_key_push_item].latest_send = datetime.utcnow()

        if not send_push : return
        #continue
        request_push = {
                'user': pushkey,
                'message':message,
                'token': settings.token_push,
                'title': title,
                'url_title': url_title,
                'url':url
            }
        
        x = requests.post(settings.url_push, data = request_push)

        if x.status_code == HTTPStatus.OK:
            aux.push_send_log[pushkey].latest_send = datetime.utcnow()
            print (f'\t Push send to {to} (next after {round(delayBetween,2)}s)')    
            f.write(f'\n\t{datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")}\tPush send to {to} ({x.status_code})')
        else:
            print (f'\t Push Error to {to} ({x.status_code})')    
            f.write(f'\n\t{datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")}\tPush Error to {to} ({x.status_code})')

class setting_store_item:
    name: str = ''
    url: str = ''
    ignore: bool = False
    sendpush: bool = False
    sendpush_to = defaultdict (Class_sendpush_to)
    timeoutRequest:int = 0
    store: str = ''
    def __init__(self, json_item):
        if "url" in json_item: self.url = json_item['url']
        if "name" in json_item: self.name = json_item['name']
        if "ignore" in json_item: self.ignore = json_item['ignore']
        if "sendpush" in json_item: self.sendpush = json_item['sendpush']
        if "sendpush_to" in json_item:
            self.sendpush_to.clear()
            sendpush_to_local = json_item['sendpush_to']
            for item in sendpush_to_local:
                config_sendpush_to = Class_sendpush_to(item, sendpush_to_local[item]['delayBetween'])
                self.sendpush_to[item] = config_sendpush_to

        if "store" in json_item: self.store = json_item['store']
        
        self.timeoutRequest = settings.timeoutRequest[self.store]

class setting_store_desired_price_item (setting_store_item):
    desiredPrice: float = 0.0
    desiredPriceOffset: int = 0
    def __init__(self, json_item):
        setting_store_item.__init__(self, json_item)
        if "desiredPrice" in json_item: self.desiredPrice:float = json_item['desiredPrice']
        if "desiredPriceOffset" in json_item: self.desiredPriceOffset = json_item['desiredPriceOffset']

class setting_pccomponentes_item(setting_store_desired_price_item):
    pass

class setting_fnac_item(setting_store_desired_price_item):
    urlStock: str = ''
    def __init__(self, json_item):
        setting_store_desired_price_item.__init__(self, json_item)
        if "urlStock" in json_item: self.urlStock = json_item['urlStock']

class settings_amazon_item(setting_store_desired_price_item):
    pass

class settings_game_by_search_item(setting_store_item):
    criteria: str = ''
    def __init__(self, json_item):
        setting_store_item.__init__(self, json_item)
        if "criteria" in json_item: self.criteria = json_item['criteria']

class setting_coolmod_item(setting_store_desired_price_item):
    pass

class setting_mediamark_item(setting_store_desired_price_item):
    pass

def log(color:bcolors, col1: str, col2:str, col3: str, col4: str, col5: str, col6: str):
    max_col2: int = 35
    col2 = col2[:max_col2-3] + (col2[max_col2-3:], '...')[len(col2) > max_col2]
    f.write("\n{: <18}{: <40}{: >10}{: >10} {: <20}{: <20}".format(col1, col2, col3, col4, col5, col6))
    print("{: <18}{: <40}{: >10}{: >10} {: <20}{: <20}".format(col1, col2, col3, col4, col5, f'{color}{col6}{bcolors.ENDC}'))

def remove_duplicates_list(x):
  return list(dict.fromkeys(x))

#@MyCircuitBreaker()
def make_web_call(url:str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }
    
    return requests.get(url, headers=headers)

def search_in_pccomponentes_store_v2(item, session:requests.Session):
    x = setting_pccomponentes_item(item)

    if x.ignore == True: return False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }

    page = requests.get(x.url, timeout= x.timeoutRequest,headers = headers)
    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(pcomponentes.es)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False

    soup = BeautifulSoup(page.content, 'html.parser')


    #<script type='application/ld+json' id="microdata-product-script">
    soap_product_script = soup.find('script',id='microdata-product-script')

    product_json = json.loads(soap_product_script.string.strip())

    lookStock = product_json['offers']['offers']['availability']

    #lookPrice = soup.find(id='priceBlock')

def search_in_pccomponentes_store(x, session:requests.Session):

    if x.ignore == True: return False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }

    page = session.get(x.url, timeout= x.timeoutRequest,headers = headers)
    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(pcomponentes.es)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False

    soup = BeautifulSoup(page.content, 'html.parser')
    
    lookStock = soup.find(id='btnsWishAddBuy')
    lookPrice = soup.find(id='priceBlock')
    lookPriceElement = lookPrice.find_all('div', id='precio-main')

    if lookStock is not None: #means nothing to check stock, then no stock
        #return False
        bothABClassP = re.compile("(?=.*btn)(?=.*btn-primary)(?=.*btn-lg)(?=.*buy)(?=.*GTM-addToCart)(?=.*buy-button)(?=.*js-article-buy)", re.I)
        job_elems = lookStock.find_all('button',attrs={"class": bothABClassP})


    price:float = 0

    if len(lookPriceElement) == 1:
        price = float(lookPriceElement[0].get('data-price'))

    if lookStock is not None and len(job_elems) > 0:

        soup_data_offer = job_elems[0].get('data-offer')
        if soup_data_offer is not None and int(soup_data_offer) > 0 : #to now if is sell by 3th party
            log(bcolors.WARNING
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price}€'
            , f'({x.desiredPrice}€)'
            , '(pcomponentes.es)'
            , f'FOUND 3th Party')
            return True 

        log(bcolors.OKGREEN
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price}€'
            , f'({x.desiredPrice}€)'
            , '(pcomponentes.es)'
            , f'FOUND!!!')

        if settings.onlySendPushWhenMatchPrice:
            if x.sendpush and x.desiredPrice >= price - x.desiredPriceOffset:
                x.sendpush = True
            else:
                x.sendpush = False            

        if x.sendpush == True:            
            send_push(f'{x.name} {price}€ ({x.desiredPrice}€) FOUND!!!\nPccomponentes',
                f'{x.name} FOUND!!!!',
                f'{x.name} {price}€',
                x.url,
                x.sendpush_to
            )
            
        else:
            print(f' Push not send. sendpush: {x.sendpush} settings.disablePushForAll: {settings.disablePushForAll}')
    else:
        log(bcolors.RED
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price}€'
            , f'({x.desiredPrice}€)'
            , '(pcomponentes.es)'
            , f'OUT OF STOCK')

    return True

def search_in_fnac_store(x, session:requests.Session):
    if x.ignore == True: return False

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'es-ES,es;q=0.9'
    }

    page = session.get(x.urlStock, timeout= x.timeoutRequest,headers = headers)
    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(fnac.es)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False

    soup = BeautifulSoup(page.content, 'html.parser')
    lookStock = soup.find(class_='f-buyShopBox')

    #esto checquea stock online, falta dispiniviladad entienda, peor no merece la pena
    availability = lookStock.find_all('div', class_='f-buyBox-availability f-buyBox-availabilityStatus-available')

    lookPrices = soup.find_all('div', class_='f-productOffer f-productOffer--options clearfix')
    price:float = 0

    for item in lookPrices: 
        price_tag = item.find('span', class_='f-priceBox-price f-priceBox-price--reco checked')
        if price_tag is not None:
            price_text = price_tag.text
            if price_text != '':
                price_text = price_text.replace('€','').replace(',','.')
                price =  float(price_text)

    if len(availability) >= 1:
        log(bcolors.OKGREEN
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price}€'
            , f'({x.desiredPrice}€)'
            , '(fnac.es)'
            , f'FOUND!!!')

        if settings.onlySendPushWhenMatchPrice:
            if x.sendpush and x.desiredPrice >= price - x.desiredPriceOffset:
                x.sendpush = True
            else:
                x.sendpush = False            

        if x.sendpush == True:            
            send_push(f'{x.name} {price}€ ({x.desiredPrice}€) FOUND!!!\nFnac',
                f'{x.name} FOUND!!!!',
                f'{x.name} {price}€',
                x.url,
                x.sendpush_to
            )
            
        else:
            print(f' Push not send. sendpush: {x.sendpush} settings.disablePushForAll: {settings.disablePushForAll}')
    else:
        log(bcolors.RED
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price}€'
            , f'({x.desiredPrice}€)'
            , '(fnac.es)'
            , f'OUT OF STOCK')

    
    return True

def search_in_game_store_by_search(item, session:requests.Session):
    
    x = settings_game_by_search_item(item)
    
    if x.ignore: return False

    #url = ''
    #if "url" in item: url = item['url']
    #if "criteria" in item: criteria = item['criteria']
   # if "desiredPrice" in item: desiredPrice:float = item['desiredPrice']
   # if "sendpush" in item: sendpush: bool = item['sendpush']
    #if "sendpush_to" in item: sendpush_to = item['sendpush_to']

    headers = {
        'User-Agent': 'User-agent header sent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Content-Type': 'application/json'
    }
    page = session.post(x.url, timeout= x.timeoutRequest,json=x.criteria,headers=headers)
    lookSearchElements = json.loads(page.text)

    for item in lookSearchElements['Products']:

        result_item = item_game(item)
        
        if 'Playstation 5' in x.name and not result_item.family_Name == 'PLAYSTATION 5':
            log(bcolors.OKCYAN
                    , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                    , f'{result_item.name}'
                    , f'{result_item.sellPrice}€'
                    , ''
                    , '(game.es)'
                    , f'FALSE POSITIVE'
                )
            return True

        if result_item.isNew:   
            if result_item.hasStock:
                log(bcolors.OKGREEN
                    , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                    , f'{result_item.name}'
                    , f'{result_item.sellPrice}€'
                    , ''
                    , '(game.es)'
                    , f'FOUND!!!')

                if x.sendpush:
                    send_push(f'{result_item.name} {result_item.sellPrice}€ FOUND!!!!\nGame.es',
                        f'{result_item.name} FOUND!!!!',
                        f'{result_item.name} {result_item.sellPrice}€',
                        result_item.url,
                        x.sendpush_to
                    )
            elif result_item.isReserve:
                log(bcolors.WARNING
                    , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                    , f'{result_item.name}'
                    , f'{result_item.sellPrice}€'
                    , ''
                    , '(game.es)'
                    , f'TO RESERVE!!!')
                if x.sendpush:
                    send_push(f'{result_item.name} {result_item.sellPrice}€ TO RESERVE!!!\nGame.es',
                        f'{result_item.name} TO RESERVE!!!',
                        f'{result_item.name} {result_item.sellPrice}€',
                        result_item.url,
                        x.sendpush_to
                    )
            else:
                log(bcolors.RED
                    , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                    , f'{result_item.name}'
                    , f'{result_item.sellPrice}€'
                    , ''
                    , '(game.es)'
                    , f'OUT OF STOCK'
                )
    return True

def search_in_amazon(item, session:requests.Session):
    x = settings_amazon_item(item)

    if x.ignore == True: return False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',

    }
    
    #page = make_web_call(x.url) # 
    page = session.get(x.url, timeout= x.timeoutRequest, headers=headers)

    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(amazon.es)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False
    
    #soup = BeautifulSoup(page.content, 'html.parser')
    #soup = BeautifulSoup(page.content, 'lxml')
    #with open("output1.html", "w") as file:
    #    file.write(str(soup))
    soup_buybox = soup.find(id='buybox')
    soup_outOfStock = soup_buybox.find_all('div', id='outOfStock')

    name_from_store = ''

    soup_titleSection = soup.find('div', id='titleSection')
    if soup_titleSection is not None:
        soup_productTitle = soup_titleSection.find('span', id = 'productTitle')
    if soup_productTitle is not None:
        name_from_store = soup_productTitle.text.strip()

    if len(soup_outOfStock) == 1:
        log(bcolors.RED
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{name_from_store}'
            , f''
            , f'({x.desiredPrice}€)'
            , '(amazon.es)'
            , f'OUT OF STOCK')
        return True

    soap_inStock = None
    in_stock: bool = False
    soap_buy_now = soup_buybox.find('div', id='buyNow_feature_div')

    if soap_buy_now is not None:
        soap_inStock = soap_buy_now.find('span', id = 'submit.buy-now-announce')
    if soap_inStock is not None:
        in_stock = True

    price = ''
    soup_price = soup_buybox.find('span', id='price_inside_buybox')
    if soup_price is not None:
        soup_price = soup_price.text.strip()
        soup_price = unicodedata.normalize("NFKD",soup_price)
        price = soup_price.replace(',', '.').replace(' ', '')

    if in_stock:
        log(bcolors.OKGREEN
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{name_from_store}'
            , f'{price}'
            , f'({x.desiredPrice}€)'
            , '(amazon.es)'
            , f'FOUND!!!')

        if settings.onlySendPushWhenMatchPrice:
            #if x.sendpush and x.desiredPrice >= price - x.desiredPriceOffset:
            if x.sendpush and x.desiredPrice >= price - x.desiredPriceOffset:
                x.sendpush = True
            else:
                x.sendpush = False            

        if x.sendpush == True:            
            send_push(f'{x.name} {price}€ ({x.desiredPrice}€) FOUND!!!\nAmazon.es',
                f'{x.name} FOUND!!!!',
                f'{x.name} {price}',
                x.url,
                x.sendpush_to
            )
        return True
    
    return True

def search_in_coolmod(item, session:requests.Session):
    x = setting_coolmod_item(item)

    if x.ignore == True: return False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }
    #page = requests.get(x.url, timeout= x.timeoutRequest, headers=headers)
    page = session.get(x.url, timeout= x.timeoutRequest, headers=headers)
    
    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(coolmod.com)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False
    
    soup = BeautifulSoup(page.content, 'html.parser')
    soup_desktop  = soup.find('div', class_='desktop-first')
    soup_stock = soup_desktop.find('span', class_='product-availability')

    soup_disponivility = soup_stock.text.strip()
    inStock:bool = False
    inReserve:bool = False
    if soup_disponivility == 'Envío en 2/15 días':
        inStock = True
    elif soup_disponivility == 'Envío Inmediato':
        inStock = True
    elif soup_disponivility == 'Reserva':
        inStock = False
        inReserve = True
    elif soup_disponivility == 'Sin Stock':
        inStock = False
        inReserve = False
    else:
        inStock = False
        inReserve = False

    soup_price = soup_desktop.find('div', class_='container-price-total')
    price_text = ''
    if soup_price is not None:
        soup_price_int = soup_price.find('span', class_='text-price-total')
        soup_price_dec = soup_price.find('span', class_='text-price-total-sup')
        price_text = soup_price_int.text + soup_price_dec.text.replace(',','.')

    if inStock :
        log(bcolors.OKGREEN
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price_text}'
            , f'({x.desiredPrice}€)'
            , '(coolmod.com)'
            , f'FOUND!!!')

        if x.sendpush == True:            
            send_push(f'{x.name} {price_text}€ ({x.desiredPrice}€) FOUND!!!\nCoolmod.com',
                f'{x.name} FOUND!!!!',
                f'{x.name} {price_text}',
                x.url,
                x.sendpush_to
            )
        return True
    elif inReserve:
        log(bcolors.WARNING
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price_text}'
            , f'({x.desiredPrice}€)'
            , '(coolmod.com)'
            , f'TO RESERVE')
        return True
    else:
        log(bcolors.RED
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , f'{price_text}'
            , f'({x.desiredPrice}€)'
            , '(coolmod.com)'
            , f'OUT OF STOCK')
        return True
    #soup_javascripts = soup.find_all('script', type='text/javascript', src='')

    #pattern = re.compile(r'\.val\("([^@]+@[^@]+\.[^@]+)"\);', re.MULTILINE | re.DOTALL)
    #soup_javascripts.find('script', text=pattern)
    #asdfsf= soup_javascripts   

def search_in_mediamark(item, session:requests.Session):
    x = setting_mediamark_item(item)

    if x.ignore == True: return False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }

    page = session.get(x.url, timeout= x.timeoutRequest, headers=headers)

    if not page.status_code == HTTPStatus.OK:
        log(bcolors.RED
            ,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{x.name}'
            , ''
            , f'({x.desiredPrice}€)'
            , '(mediamarkt.es)'
            , f'ERROR STATUS CODE {page.status_code}!!!')

        return False
    
    soup = BeautifulSoup(page.content, 'html.parser')

    soup_availability: str = ''
    soup_title: str = ''
    soup_price: str = ''

    soup_availability = soup.find('meta', attrs={'property': 'og:availability'})
    soup_title = soup.find('meta', attrs={'property': 'og:title'})
    soup_price = soup.find('meta', attrs={'property': 'product:price:amount'})

    inStock:bool = False
    name:str = soup_title['content']
    price: float = float(soup_price['content'])

    if soup_availability['content'] == 'in stock':
        inStock = True
    elif soup_availability['content'] == 'out of stock':
        inStock = False
    else:
        inStock = False

    if inStock:
        log(bcolors.OKGREEN
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{name}'
            , f'{price}'
            , f'({x.desiredPrice}€)'
            , '(mediamark.es)'
            , f'FOUND!!!')

        if x.sendpush == True:            
            send_push(f'{x.name} {price}€ ({x.desiredPrice}€) FOUND!!!\nmediamark.es',
                f'{name} FOUND!!!!',
                f'{name} {price}',
                x.url,
                x.sendpush_to
            )
        return True
    else:
        log(bcolors.RED
            , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
            , f'{name}'
            , f'{price}'
            , f'({x.desiredPrice}€)'
            , '(mediamark.es)'
            , f'OUT OF STOCK')
        return True

def process_pccpmponentes(items):
    session_pccomponentes:requests.Session = None
    if session_pccomponentes is None: session_pccomponentes = requests.Session()
    for item in items:
        x = setting_pccomponentes_item(item)
        try:
            return_satus = search_in_pccomponentes_store(x, session_pccomponentes)
        except Exception as e:
            log(bcolors.RED
                , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                , f'{x.name}'
                , ''
                , f'({x.desiredPrice}€)'
                , '(pcomponentes.es)'
                , f'ERROR')
                
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)

def process_fnac(items):
    session_fnac:requests.Session = None
    if session_fnac is None: session_fnac = requests.Session()
    for item in items:
        x = setting_fnac_item(item)
        try:
            return_satus = search_in_fnac_store(x, session_fnac)
        except Exception as e:
            log(bcolors.RED
                , datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")
                , f'{x.name}'
                , ''
                , f'({x.desiredPrice}€)'
                , '(fnac.es)'
                , f'ERROR')
                
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)


def process_amazon(items):
    session_amazon:requests.Session = None
    if session_amazon is None: session_amazon = requests.Session()
    for item in items:
        return_satus = search_in_amazon(item, session_amazon)
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)
    
def process_game(items):
    session_game:requests.Session = None
    if session_game is None: session_game = requests.Session()
    for item in items:
        return_satus = search_in_game_store_by_search(item, session_game)
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)

def process_coolmod(items):
    session_coolmod:requests.Session = None
    if session_coolmod is None: session_coolmod = requests.Session()
    for item in items:
        return_satus = search_in_coolmod(item, session_coolmod)
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)

def process_mediamark(items):
    session_mediamark:requests.Session = None
    if session_mediamark is None: session_mediamark = requests.Session()
    for item in items:
        return_satus = search_in_mediamark(item, session_mediamark)
        f.flush()
        if return_satus:
            time.sleep(settings.delayPerItem)

def readConfigFile():

    with open("settings.json", "r") as read_file :
        filejson = json.load(read_file)

        if "enviroment" in filejson: settings.enviroment = filejson['enviroment']
        if "enableLogInfo" in filejson: settings.enableLogInfo = filejson['enableLogInfo']
        if "readConfigEachSeconds" in filejson: settings.readConfigEachSeconds = filejson['readConfigEachSeconds']            
        if "stop" in filejson: settings.stopProcess = filejson['stopProcess']
        if "delayIfException" in filejson: settings.delayIfException = filejson['delayIfException']
        if "onlySendPushWhenMatchPrice" in filejson: settings.onlySendPushWhenMatchPrice = filejson['onlySendPushWhenMatchPrice']
        if "showConfigInfo" in filejson: settings.showConfigInfo = filejson['showConfigInfo']
        if "delayPerItem" in filejson: settings.delayPerItem = filejson['delayPerItem']
        if "timeoutRequest" in filejson: settings.timeoutRequest = filejson['timeoutRequest']        
        if "storeConfig" in filejson: storeConfig_local = filejson['storeConfig']

        settings.disablePushForAll = filejson['disablePushForAll']
        settings.itemsToLookFor = filejson['items']

        settings.storeConfig.clear()
        #generate the functions
        for item in storeConfig_local:
            function_to_use = storeConfig_local[item]['function']
            timeout_to_use = storeConfig_local[item]['timeoutRequest']
            st_config = store_config(item, globals()[function_to_use], timeout_to_use)
            settings.storeConfig[item] = st_config
            #no entiendo porque tengo que buscar en vez de coger el iterado iteem22

        settings.group_by_store.clear()

        for item in settings.itemsToLookFor:
            settings.group_by_store[item['store']].append(item)
    
        if not settings.disablePushForAll:
            enviroment:str = settings.enviroment

            if enviroment == '':
                raise Exception(f'you need and enviromers')
            
            # To get your credentials go to https://pushover.net/
            try:
                with open(f'pushover_settings.{enviroment}.json', "r") as read_file :
                    pushoverjson = json.load(read_file)
                    settings.token_push = pushoverjson['token_push']
                    settings.users_pushKeys = pushoverjson['users_pushKeys']
                    settings.url_push = pushoverjson['url_push']
            except FileNotFoundError:
                raise Exception(f'the file for the {enviroment} does not exists')

        if settings.showConfigInfo:
            print(f'\treadConfigEachSeconds: {settings.readConfigEachSeconds}\n' \
                + f'\ttopProcess: {settings.stopProcess}\n' \
                + f'\tdelayIfException: {settings.delayIfException}\n' \
                + f'\tdelayPerItem: {settings.delayPerItem}\n' \
                + f'\tonlySendPushWhenMatchPrice: {settings.onlySendPushWhenMatchPrice}\n' \
                + f'\token_push: {settings.token_push}\n'\
                + f'\turl_push: {settings.url_push}\n' \
                + f'\tdisablePushForAll: {settings.disablePushForAll}\n' \
                + f'\turl_push: {settings.timeoutRequest}'
                )

def main_v2():
    readConfigFile()
    lastReadConfigTime = datetime.utcnow()
    while True:
        global f
        f = open(settings.filetoLog, "a")
        startloopTime = datetime.utcnow()
        if settings.enableLogInfo:
            log(bcolors.OKBLUE, '', '', '' , '', 'Loop Start: ', startloopTime)
            
        try:
            #with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for itemsStore in settings.group_by_store:
                function_name = settings.storeConfig[itemsStore].function.__name__
                try:
                    function = settings.storeConfig[itemsStore].function
                    item = settings.group_by_store[itemsStore]
                    function(item)
                except Exception as e:
                    log(bcolors.RED,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S"),'','','',f'{function_name}', 'Error Unknow store')
                    continue
                
            offset = datetime.utcnow() - lastReadConfigTime

            if offset.total_seconds() > settings.readConfigEachSeconds:
                f.write(f'\nReading config file again')
                print(f'Reading config file again')
                readConfigFile()
                lastReadConfigTime = datetime.utcnow()
        except Exception as e:
            #print (f'{datetime.utcnow().strftime("%d-%m-%y %H:%M:%S")}\t {bcolors.RED}Error unknow{bcolors.ENDC}\n{e}')  
            log(bcolors.RED,datetime.utcnow().strftime("%d-%m-%y %H:%M:%S"),'','','','', 'Error Unknow')
            continue

        offset = datetime.utcnow() - lastReadConfigTime

        if offset.total_seconds() > settings.readConfigEachSeconds:
            f.write(f'\nReading config file again')
            print(f'Reading config file again')
            readConfigFile()
            lastReadConfigTime = datetime.utcnow()

        if settings.enableLogInfo:
            log(bcolors.OKBLUE, '', '', '' , f'takes {(datetime.utcnow() - startloopTime).total_seconds()}', 'Loop Ends: ', datetime.utcnow() )
        
        if settings.stopProcess == True:
            f.write(f'\nProcess stopped')
            print(f'Process stopped')
            f.close()
            break

        f.close()

if __name__ == '__main__':
    main_v2()