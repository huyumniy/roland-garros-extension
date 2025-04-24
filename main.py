import os
import ast
from urllib.parse import urlparse
import tempfile
import nodriver as uc
import random
from nodriver import cdp
import shutil
import sounddevice as sd
import soundfile as sf
import undetected_chromedriver
import time
import requests
import sys, os
import nodriver


async def get_court(page, restricted_time, desired_court=None):
    try:
        courts = await page.query_selector_all('div[class="collection-item-2 w-dyn-item"]')
        for court in courts:
            court_data = await court.query_selector('.block-lect.courts.mb-20')
            court_text_element = await court_data.query_selector('div')
            court_text = court_text_element.text
            court_time_element = await court.query_selector('.text-block-65')
            court_time = court_time_element.text.lower()
            if desired_court:
                if court_text.lower() not in desired_court: continue
            if court_time in restricted_time: continue
            return {'court': court, 'court_name': court_text}
    except Exception as e:
        # print('get_court', e)
        return False


async def get_ticket(page, amount, categories=None):
    try:
        if await page.wait_for("div[class='category dropdown-np w-dropdown-toggle']"):
            tickets = await page.query_selector_all("div[class='category dropdown-np w-dropdown-toggle']")
            while True:
                ticket = random.choice(tickets)
                category_element = await ticket.query_selector('h2 div')
                category = category_element.text.lower()
                if categories:
                    if category in categories: continue
                await ticket.click()
                    # remaining = await custom_wait(page, 'div[class="tooltip-inner"]', timeout=5)
                    # print(remaining.text)

                return True
    except Exception as e: 
        print('get_ticket', e)
        return False
    

async def get_polygon(page):
    try:
        if await check_for_element(page, "polygon[class='polygon has-tooltip']", debug=True) or \
            await check_for_element(page, "polygon[class='polygon']", debug=True):
            await check_for_element(page, "polygon[class='polygon has-tooltip']", debug=True, click=True)
            await check_for_element(page, "polygon[class='polygon']", debug=True, click=True)
            return True
    except Exception as e:
        print('get_polygon', e)
        return False
    

async def get_stadion_ticket(page):
  try:
    if await page.query_selector("a[class='bt-main orange-aa w-inline-block']"):
      add = await page.query_selector("a[class='bt-main orange-aa w-inline-block']")
      await add.click()
      return True
  except Exception as e: 
      print('get_station_ticket', e)
      return False


async def custom_wait(page, selector, timeout=10):
    print('in custom wait')
    for _ in range(0, timeout):
        try:
            element = await page.query_selector(selector)
            if element: return element
            time.sleep(1)
        except Exception as e: 
            time.sleep(1)
            print(e)
    return False


async def custom_wait_elements(page, selector, timeout=10):
    print('in custom wait')
    for _ in range(0, timeout):
        try:
            element = await page.query_selector_all(selector)
            if element: return element
            time.sleep(1)
        except Exception as e: 
            time.sleep(1)
            print(e)
    return False


async def check_seat_recursively(page, seat_id, direction, required_seats):
    count = 0
    while count < required_seats-1:
        seat = await check_for_element(page, f'polygon[id="{seat_id}"]')
        if seat and seat.attrs['class_'] == 'polygon':
            await seat.click()
            await get_stadion_ticket(page)
            count += 1
            if count >= required_seats:
                return True
        else:
            break
        seat_id += direction
    return False


async def get_seat(page, amount):
    try:
        print('in get_seat')
        if await check_for_element(page, "polygon[class='polygon has-tooltip']", debug=True) or \
        await check_for_element(page, "polygon[class='polygon']", debug=True):
            try: seats = await page.query_selector_all("polygon[class='polygon has-tooltip']")
            except Exception as e: print('seats has-tooltoip', e)
            if seats == []:
                try:seats = await page.query_selector_all("polygon[class='polygon']")
                except Exception as e: print('seats polygon', e)
            seat = random.choice(seats)
            seat_id = str(seat.attrs['id'])
            seat_element = await page.query_selector(f'polygon[id="{seat_id}"]')
            await seat_element.mouse_move()
            time.sleep(1)
            await seat_element.mouse_click()
            if await custom_wait(page, 'input[class="quantity text-field-2 w-input"]', timeout=2):
                for _ in range(0, amount):
                    await check_for_element(page, 'button[class="increment less button w-button"]', click=True, debug=True)
                await check_for_element(page, 'button.add-to-cart', click=True, debug=True)
                time.sleep(2)
                if await custom_wait(page, '#alert_error', timeout=5): return False
                elif await custom_wait(page, 'div[class="ConfirmationSelectionPanel"]', timeout=5):
                    data, fs = sf.read('notify.wav', dtype='float32')  
                    sd.play(data, fs)
                    status = sd.wait()
                    input('continue?')
                    return False
            else:
                seats = await custom_wait_elements(page, "polygon[class='polygon']", timeout=3)
                if not seats: 
                    print('no seat available')
                    return False
                print(seats)
                seat = random.choice(seats)
                seat_id = str(seat.attrs['id'])
                print(seat_id)
                if int(amount) == 1:
                    await seat.mouse_move()
                    time.sleep(1)
                    await seat.mouse_click()
                    time.sleep(1)
                    await get_stadion_ticket(page)
                    print('after click')

                elif int(amount) > 1:
                    forward_seats_found = await check_seat_recursively(page, int(seat_id) + 1, 1, int(amount))
                    backward_seats_found = await check_seat_recursively(page, int(seat_id) - 1, -1, int(amount))

                    if forward_seats_found or backward_seats_found:
                        print('Found enough seats')
                        await seat.mouse_move()
                        time.sleep(1)
                        await seat.mouse_click()
                        time.sleep(1)
                        await get_stadion_ticket(page)
                        print('after click')
                    else:
                        print('Not enough seats found')
                if await custom_wait(page, 'div[class="ConfirmationSelectionPanel"]', timeout=5):
                    data, fs = sf.read('notify.wav', dtype='float32')  
                    sd.play(data, fs)
                    status = sd.wait()
                    input('continue?')
                    return False
                return True
    except Exception as e:
        print('get_seat', e)
        return False
    

async def check_for_element(page, selector, click=False, debug=False):
    try:
        element = await page.query_selector(selector)
        if click:
            await element.click()
        return element
    except Exception as e:
        if debug: print("selector", selector, '\n', e)
        return False


async def main(input_date, categories, restricted_time, amount, desired_court=None):
    try:
        # print(input_date, categories, restricted_time, amount, desired_court)
        link = 'https://tickets.rolandgarros.com/en/'
        
        adspower = input('adspower api: ').strip()
        adspower_id = input('adspower id: ').strip()
        adspower_link = f"{adspower}/api/v1/browser/start?user_id={adspower_id}"

        resp = requests.get(adspower_link).json()
        if resp["code"] != 0:
            print(resp["msg"])
            print("please check ads_id")
            sys.exit()
        host, port = resp['data']['ws']['selenium'].split(':')
        # print(adspower_link)

        config = nodriver.Config(user_data_dir=None, headless=False, browser_executable_path=None, \
        browser_args=None, sandbox=True, lang='en-US', host=host, port=int(port))
        driver = await uc.Browser.create(config=config)

        page = await driver.get(link)
        input('continue?')
        while True:
            try:
                if await check_for_element(page, '.stadium-image', debug=True): await check_for_element(page, 'div.nav-web > div > div > button', click=True, debug=True)
                if await check_for_element(page, 'div[class="EmptyCart container-main py-40"]', debug=True): await check_for_element(page, 'div.nav-web > div > div > button', click=True, debug=True)
                dates = await page.query_selector_all('.cal-card.lb1.w-inline-block.w-tab-link > div')
                date_for_click = ''
                for date in dates:
                    if date.text == input_date:
                        date_for_click = date
                await date_for_click.scroll_into_view()
                await date_for_click.click()
                attrs = ['tab-offres w-inline-block w-tab-link w--current unavailable-offers', 'tab-offres w-inline-block w-tab-link unavailable-offers']
                time.sleep(1)
                left_menu = await page.query_selector_all('.tab-offres.w-inline-block.w-tab-link')
                for left_block in left_menu:
                    time.sleep(1)
                    if left_block.attrs['class_'] not in attrs:
                        h2 = await left_block.query_selector('h2')
                        h2_text = h2.text.strip()
                        if h2_text == 'Premium Offers': continue
                        await left_block.click()
                        try: await page.wait_for('div[class="content-billet"] > div:nth-child(2) > a.orange-a', timeout=10)
                        except Exception as e:
                            print(e)
                            continue
                        court = await get_court(page, restricted_time, desired_court)
                        if court:

                            print(court['court_name'])
                            if court['court_name'] == 'Outside Courts':
                                # print('TRUE')
                                # buy_button = await court['court'].query_selector('div.bottom-wrapper > a.orange-a')
                                # await buy_button.click()
                                pass
                            else:
                                print('FALSE')
                                buy_button = await court['court'].query_selector('div.bottom-wrapper > a.orange-a')
                                await buy_button.click()
                                time.sleep(2)
                                await custom_wait(page, '.stadium-image', timeout=5)
                                while True:  
                                    if not await check_for_element(page, '.stadium-image', debug=True): break
                                    try:
                                        if await get_ticket(page, categories):
                                            if await get_polygon(page):
                                                if await get_seat(page, amount):
                                                    pass
                                        back_button = await page.query_selector('div.nav-web > div > div > button')
                                        await back_button.click()
                                        time.sleep(random.randint(1, 6))
                                        await page.back()
                                        time.sleep(1)
                                    except Exception as e: print(e)

                time.sleep(random.randint(3, 10))
            except Exception as e: 
                print(e)
                time.sleep(30)
                continue

                
        
        
    except Exception as e: print(e)

if __name__ == '__main__':

    input_date = ''
    amount = 1
    categories = []
    restricted_time = []
    while True:
        input_amount = input('Введіть бажану кількість квитків: ')
        try: 
            amount = int(input_amount)
            break
        except: pass
    court_name = input('Court name or press Enter: ').lower()
    while True:
        input_date = input('Введіть дату в наступному форматі: "TUE 30 MAY":\n')
        if not input_date == '': break
    restricted_time = [element.lower() for element in input('Введіть сесії матчів, які НЕ потрібно переглядати в наступному форматі: "night, day, end of day":\n').split(', ')]
    categories = [category.lower() for category in input('Введіть категорії, які НЕ потрібно переглядати в наступному форматі: "category 3, category gold":\n').split(', ')]

    uc.loop().run_until_complete(main(input_date, categories, restricted_time, amount, court_name))
