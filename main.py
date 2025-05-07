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
from filtration import filter_seats
import json


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
        if await custom_wait(page, "div[class='category dropdown-np w-dropdown-toggle']", timeout=3):
            tickets = await custom_wait_elements(page, "div[class='category dropdown-np w-dropdown-toggle']", timeout=1)
            if not tickets: return False
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
    for _ in range(0, timeout):
        try:
            element = await page.query_selector_all(selector)
            if element: return element
            time.sleep(1)
        except Exception as e: 
            time.sleep(1)
            # print(e)
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
        if await check_for_element(page, "polygon[class='polygon has-tooltip']") or \
        await check_for_element(page, "polygon[class='polygon']"):
            try: seats = await page.query_selector_all("polygon[class='polygon has-tooltip']")
            except Exception as e: print('seats has-tooltoip', e)
            if seats == []:
                try: seats = await page.query_selector_all("polygon[class='polygon']")
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
                polygon_ids = [seat.attrs['id'] for seat in seats if seat.attrs.get('id') is not None]
                print(polygon_ids)
                
                if int(amount) == 1:
                    seat = random.choice(seats)
                    seat_id = str(seat.attrs['id'])
                    print(seat_id)
                    await seat.mouse_move()
                    time.sleep(1)
                    await seat.mouse_click()
                    time.sleep(1)
                    await get_stadion_ticket(page)
                    print('after click')

                elif int(amount) > 1:
                    filtered_seats = filter_seats(polygon_ids, amount)
                    if not filtered_seats: 
                        print('Not enough seats found')
                        return False
                    random_seats_arr = random.choice(filtered_seats)
                    for seat_id in random_seats_arr:
                        seat = await check_for_element(page, f'polygon[class="polygon"][id="{seat_id}"]', debug=True)
                        if not seat: break
                        await seat.mouse_move()
                        time.sleep(1)
                        await seat.mouse_click()
                        time.sleep(1)
                        await get_stadion_ticket(page)
                        print('after click')

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


async def main():
    try:
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
        
        while True:
            try:
                ticketBotSettings = await get_indexeddb_data(page, 'TicketBotDB', 'settings')
                input_date = ticketBotSettings.get('date')
                categories = ticketBotSettings.get('categories')
                restricted_time = ticketBotSettings.get('sessions')
                amount = int(ticketBotSettings.get('amount')) if ticketBotSettings else None
                desired_court = ticketBotSettings.get('courts')
                stopExecutionFlag = ticketBotSettings.get('stopExecutionFlag')
                if stopExecutionFlag:
                    time.sleep(5)
                    continue
            except Exception as e:
                print(f"Error fetching data from IndexedDB: {e}")
                ticketBotSettings = None
                time.sleep(60)
                continue
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


# @eel.expose
# def start_workers(initialUrl, isSlack, browsersAmount, isVpn, proxyList):
#     print(initialUrl, isSlack, browsersAmount, isVpn, proxyList)
#     threads = []
#     if isSlack:
#         flask_thread = threading.Thread(target=run_flask)
#         flask_thread.daemon = True
#         flask_thread.start()
#     for i in range(1, int(browsersAmount)+1):  # Example: 3 threads, modify as needed
#         if i!= 1: time.sleep(i*30)
#         thread = threading.Thread(target=main, args=(i, initialUrl, isSlack, browsersAmount, isVpn, proxyList))
#         threads.append(thread)
#         thread.start()
#     # Wait for all threads to complete
#     for thread in threads:
#         thread.join()


async def get_indexeddb_data(driver, db_name, store_name, key=1):
    # Build a snippet that returns a Promise resolving to your settings JSON or null
    script = f"""
    (function() {{
        return new Promise((resolve, reject) => {{
            let openRequest = indexedDB.open("{db_name}");
            openRequest.onerror = () => resolve(null);
            openRequest.onsuccess = event => {{
                let db = event.target.result;
                let tx = db.transaction("{store_name}", "readonly");
                let store = tx.objectStore("{store_name}");
                let getRequest = store.get({key});
                getRequest.onerror = () => resolve(null);
                getRequest.onsuccess = () => {{
                    let data = getRequest.result;
                    // If you stored an object with a .settings field
                    resolve(data ? data.settings : null);
                }};
            }};
        }});
    }}())  /* immediately‐invoked because evaluate wants an expression */
    """

    # Evaluate the script, awaiting the promise, and return by value
    result = await driver.evaluate(
        script,
        await_promise=True,
        return_by_value=True
    )

    # result is now either your settings object (JSON‑compatible) or None
    return result


async def get_stop_execution_flag(driver):
    """
    Reads window.stopExecutionFlag from the page context.
    Returns its value (could be True/False/any JS value) or None if not set.
    """
    script = """
    (function() {
        // Read the global flag; resolve to null if undefined
        return window.stopExecutionFlag;
    }())
    """
    # await the promise, return the JS value directly
    flag_value = await driver.evaluate(
        script,
        await_promise=True,
        return_by_value=True
    )
    return flag_value



if __name__ == '__main__':

    uc.loop().run_until_complete(main())
