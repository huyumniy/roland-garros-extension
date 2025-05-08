import nodriver as uc
import random
import sounddevice as sd
import soundfile as sf
import time
import requests
import sys, os
from filtration import filter_seats
import eel
import threading
import socket
from colorama import init, Fore


init(autoreset=True)

async def get_court(page, desired_time=None, desired_court=None):
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
            if desired_time:
                if court_time not in desired_time: continue
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
                    if category not in categories: continue
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


async def configure_proxy(tab, proxyList):
    try:
        await tab.get('chrome://extensions/')
        script = """
                (async () => {let data = await chrome.management.getAll(); return data;})();
        """

        extensions = await tab.evaluate(expression=script, await_promise=True)
        # print("extensions", extensions)
        if extensions is None: 
            print('Проксі розширення не встановлене!')
            return None
        filtered_extensions = [extension for extension in extensions if "BP Proxy Switcher" in extension['name']]

        vpn_id = [extension['id'] for extension in filtered_extensions if 'id' in extension][0]
        vpn_url = f'chrome-extension://{vpn_id}/popup.html'
        await tab.get(vpn_url)
        # await tab.get(vpn_url)
        delete_tab = await tab.select('#deleteOptions')
        # driver.evaluate("arguments[0].scrollIntoView();", delete_tab)
        await delete_tab.mouse_click()
        time.sleep(1)
        temp = await tab.select('#privacy > div:first-of-type > input')
        await temp.mouse_click()
        time.sleep(1)
        temp1 = await tab.select('#privacy > div:nth-of-type(2) > input')
        await temp1.mouse_click()
        time.sleep(1)
        temp2 = await tab.select('#privacy > div:nth-of-type(4) > input')
        await temp2.mouse_click()
        time.sleep(1)
        temp3 = await tab.select('#privacy > div:nth-of-type(7) > input')
        await temp3.mouse_click()


        optionsOK = await tab.select('#optionsOK')

        # driver.execute_script("arguments[0].scrollIntoView();", optionsOK)
        await optionsOK.mouse_click()
        time.sleep(1)
        edit = await tab.select('#editProxyList > small > b')
        # driver.execute_script("arguments[0].scrollIntoView();", edit)
        await edit.mouse_click()
        time.sleep(1)
        text_area = await tab.select('#proxiesTextArea')
        for proxy in proxyList:
            js_function = f"""
            (elem) => {{
                elem.value += "{proxy}\\n";
                return elem.value;
            }}
            """
            await text_area.apply(js_function)
        time.sleep(1)
        ok_button = await tab.select('#addProxyOK')
        await ok_button.mouse_click()
        time.sleep(3)
        
        proxy_switch_list = await tab.find_all('#proxySelectDiv > div > div > ul > li')
        if len(proxy_switch_list) == 3: 
            await proxy_switch_list[2].mouse_click()
        else: 
            await proxy_switch_list[random.randint(2, len(proxy_switch_list)-1)].mouse_click()
        time.sleep(5)
        
        proxy_auto_reload_checkbox = await tab.select('#autoReload')
        # driver.execute_script("arguments[0].scrollIntoView();", proxy_auto_reload_checkbox)
        await proxy_auto_reload_checkbox.mouse_click()
        time.sleep(2)

        return True
    except Exception as e:
        print('configure_proxy', e)
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


async def main(browserId, browsersAmount, proxyList=None, adspower=None, adspower_id=None):
    try:
        link = 'https://tickets.rolandgarros.com/en/'

        interface_extension_path = os.path.join(os.path.dirname(__file__), 'interface-extension')

        if all([adspower, adspower_id]):
            adspower_link = f"{adspower}/api/v1/browser/start?serial_number={adspower_id}"

            resp = requests.get(adspower_link).json()
            if resp["code"] != 0:
                print(resp["msg"])
                print("please check ads_id")
                sys.exit()
            host, port = resp['data']['ws']['selenium'].split(':')

            config = uc.Config(user_data_dir=None, headless=False, browser_executable_path=None, \
            browser_args=None, sandbox=True, lang='en-US', host=host, port=int(port))
            config.add_extension(extension_path=interface_extension_path)
            driver = await uc.Browser.create(config=config)
        

        elif not all([adspower, adspower_id]):
            config = uc.Config(user_data_dir=None, headless=False, browser_executable_path=None,\
            browser_args=None, sandbox=True, lang='en-US')
            config.add_extension(extension_path="./BPProxySwitcher.crx")
            config.add_extension(extension_path=interface_extension_path)
            driver = await uc.Browser.create(config=config)
            if proxyList:
                await driver.get(link)
                tab = driver.main_tab
                await configure_proxy(tab, proxyList)

        page = await driver.get(link)
        if adspower_id:
            print(Fore.GREEN + f"Browser {adspower_id}: Successfully started!\n")
        else:
            print(Fore.GREEN + f"Browser {browserId}: Successfully started!\n")
        while True:
            try:
                ticketBotSettings = await get_indexeddb_data(page, 'TicketBotDB', 'settings')
                input_date = ticketBotSettings.get('date')
                categories = ticketBotSettings.get('categories')
                desired_time = ticketBotSettings.get('sessions')
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
                        court = await get_court(page, desired_time, desired_court)
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


@eel.expose
def start_workers(browsersAmount, proxyInput, adspowerApi, adspowerIds):
    threads = []
    print('start_workers', browsersAmount, proxyInput, adspowerApi, adspowerIds)

    # Case: using adspower API + IDs
    if not browsersAmount and all([adspowerApi, adspowerIds]):
        total = len(adspowerIds)
        for i in range(1, total + 1):
            ads_id = adspowerIds[i - 1]
            # bind i, total, ads_id into lambda defaults
            thread = threading.Thread(
                target=lambda idx=i, tot=total, aid=ads_id:
                    uc.loop().run_until_complete(
                        main(idx, tot, proxyInput, adspowerApi, aid)
                    )
            )
            threads.append(thread)
            thread.start()

    # Case: fixed number of browsers
    elif browsersAmount and not any([adspowerApi, adspowerIds]):
        total = int(browsersAmount)
        for i in range(1, total + 1):
            # bind i, total into lambda defaults
            thread = threading.Thread(
                target=lambda idx=i, tot=total:
                    uc.loop().run_until_complete(
                        main(idx, tot, proxyInput)
                    )
            )
            threads.append(thread)
            thread.start()

    # Wait for all to finish
    for thread in threads:
        thread.join()



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


def is_port_open(host, port):
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect((host, port))
    return True
  except (socket.timeout, ConnectionRefusedError):
    return False
  finally:
    sock.close()


if __name__ == "__main__":
    eel.init('gui')

    port = 8000
    while True:
        try:
            if not is_port_open('localhost', port):
                eel.start('main.html', size=(600, 800), port=port)
                break
            else:
                port += 1
        except OSError as e:
            print(e)
