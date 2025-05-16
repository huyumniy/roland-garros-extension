import urllib.request
import re
import random
import json
import time
import sys, os
import threading
import socket
import nodriver as uc
# from nodriver.cdp.network import delete_cookies
import sounddevice as sd
import soundfile as sf
import requests
import eel
from colorama import init, Fore
import speech_recognition
import pydub
import textwrap
from datetime import datetime, timedelta
from filtration import filter_seats
from utils.sheetsApi import get_data_from_google_sheets


TIME_FROM_START = datetime.now()
TIME_TO_WAIT = TIME_FROM_START + timedelta(minutes=5)
pydub.AudioSegment.converter = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
print(os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"))
init(autoreset=True)
accounts = []

async def get_court(page, desired_time=None, desired_courts=None):
    try:
        # print('in get court', desired_time, desired_courts)
        courts = await page.query_selector_all('div[class="collection-item-2 w-dyn-item"]')
        for court in courts:
            court_data = await court.query_selector('.block-lect.courts.mb-20')
            court_text_element = await court_data.query_selector('div')
            court_text = court_text_element.text
            court_time_element = await court.query_selector('.text-block-65')
            court_time = court_time_element.text.strip().lower()
            # print(court_text, court_text not in desired_courts, 'if desired_courts statement')
            if desired_courts:
                if court_text not in desired_courts: continue
            # print(court_time, court_time not in desired_time, 'if desired_time statement')
            if desired_time:
                if court_time not in desired_time: continue
            # print({'court_name': court_text, 'court_time': court_time})
            return {'court': court, 'court_name': court_text, 'court_time': court_time}
    except Exception as e:
        print('get_court', e)
        return False


async def get_ticket(page, categories=None):
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
                

                return category
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
        
        proxy_auto_reload_checkbox = await tab.select('#autoReload')
       
        await proxy_auto_reload_checkbox.mouse_click()
        time.sleep(2)

        await change_proxy(tab)

        return True
    except Exception as e:
        print('configure_proxy function error:', e)
        return False


async def change_proxy(tab):
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
        time.sleep(2)
        # edit = await tab.select('#editProxyList > small > b')
        # await edit.mouse_click()
        # time.sleep(1)
        # ok_button = await tab.select('#addProxyOK')
        # await ok_button.mouse_click()
        # time.sleep(2)
        select_button = await tab.select('#proxySelectDiv > div > button')
        await select_button.mouse_click()
        time.sleep(2)
        proxy_switch_list = await tab.find_all('#proxySelectDiv > div > div > ul > li')
        if len(proxy_switch_list) == 3:
            await proxy_switch_list[2].scroll_into_view()
            await proxy_switch_list[2].mouse_click()
        else:
            certain_proxy = proxy_switch_list[random.randint(2, len(proxy_switch_list)-1)]
            await certain_proxy.scroll_into_view()
            await certain_proxy.mouse_click()
        time.sleep(5)

        return True
    except Exception as e:
        print('change_proxy function error:', e)
        return False


def process_audio_challenge(audio_url: str) -> str:
    """Process the audio challenge and return the recognized text.

    Args:
        audio_url: URL of the audio file to process

    Returns:
        str: Recognized text from the audio file
    """
    wav_path = os.path.join(os.getcwd(), f"{random.randrange(1,1000)}.wav")

    try:
        urllib.request.urlretrieve(audio_url, wav_path)
        sound = pydub.AudioSegment.from_wav(wav_path)
        sound.export(wav_path, format="wav")
        recognizer = speech_recognition.Recognizer()

        with speech_recognition.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        return recognizer.recognize_google(audio)

    finally:
        for path in (wav_path,):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


async def wait_for_captcha(page, driver):
    try:
        print('in wait for captcha')
        for i in range(1, 4):

            iframe = await page.select("iframe")
            # Get required tab. Not safe in case when tab not found
            iframe_tab: uc.Tab = next(
                filter(
                    lambda x: str(x.target.target_id) == str(iframe.frame_id), driver.targets
                )
            )
            # Fixing websocket url
            iframe_tab.websocket_url = iframe_tab.websocket_url.replace("iframe", "page")
            button = await iframe_tab.select(
                'button[id="captcha__audio__button"]'
            )
            await button.click()
            audio = await iframe_tab.select('audio[src]')
            audio_attrs = audio.attrs
            audio_src = audio_attrs['src']
            
            text_response = process_audio_challenge(audio_src)
            print(text_response)
            play_button = await iframe_tab.select('button[class="audio-captcha-play-button push-button"]')
            await play_button.click()
            time.sleep(6)

            numbers = extract_numbers(text_response)
            print(numbers, 'extracted_numbers')
            
            time.sleep(15)
            await solve_audio_captcha(iframe_tab, numbers)
            time.sleep(20)
    except Exception as e:
        print('wait for captcha', e)


def extract_numbers(text):
    # 1) Define mapping of number-words → digit-strings
    number_map = {
        "zero": "0", "one": "1", "on": "1",
        "two": "2",  "to": "2",
        "three": "3", "tree": "3",
        "four": "4",
        "five": "5", "fi": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9"
    }

    # Sort keys by length descending to avoid partial‐match collisions (e.g. "one" vs "on")
    sorted_words = sorted(number_map.keys(), key=len, reverse=True)
    # Build a regex that matches any of the keys as whole words
    word_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, sorted_words)) + r')\b', re.IGNORECASE)

    # 2) Replace every matched word with its digit
    def _replace(match):
        word = match.group(0).lower()
        return number_map[word]
    
    transformed = word_pattern.sub(_replace, text)

    # 3) Now find all standalone digits in the transformed text
    digit_chars = re.findall(r'\d', transformed)

    # 4) Convert to ints and return
    return [int(d) for d in digit_chars]


def send_slack_message(data):
    try:
        json_data = json.dumps({"data": data})
        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post("http://localhost:8080/book", data=json_data, headers=headers)
            if response.status_code == 200:
                print("POST request successful!")
            else:
                raise Exception("POST request failed with status code: " + str(response.status_code))
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)


async def authorization(page, login, password):
    try:
        if await check_for_element(page, 'iframe[src^="https://geo.captcha-delivery.com"]'):
            return False
        await check_for_element(page, '.menu-item-container > a[menuitemtype="SIGN_IN"]', click=True)

        if await check_for_element(page, 'div[menuitemtype="MY_ACCOUNT"]'):
            return True
        # if not sign_in_button:
        #     print('Не вдалось знайти кнопку для авторизації') 
        #     return False
        time.sleep(5)
        auth_form = await check_for_element(page, '.fft-card')
        if not auth_form:
            print('Не вдалось знайти форму авторизації')
            return False
        login_input = await check_for_element(page, '#username-input > fieldset > input[type=text]')
        password_input = await check_for_element(page, '#password-input > fieldset > input[type=password]')
        await login_input.send_keys(login)
        await password_input.send_keys(password)
        time.sleep(2)
        await check_for_element(page, '.fft-card-button > button#RG', click=True)
        time.sleep(10)
        error = await check_for_element(page, '.fft-alert.error > span')
        if error:
            print('Не вдалось авторизуватись на сайті. Помилка:', error.text)
            return False

        return True
    except Exception as e:
        print('authorization function error:', e)
        return False
    
async def parse_cart_data(page):

    seats_info = ""
    try:
        general_info = ""
        category = await check_for_element(page, '#category-label')
        general_info += category.text.strip() + '\n'
        date = await check_for_element(page, '#offer-dates')
        session = await check_for_element(page, '#offer-sessions')
        court = await check_for_element(page, '#offer-court')
        general_info += f"{date.text.strip()} {session.text.strip()} {court.text.strip()}"
        seats_info += general_info + '\n'

        seat_details = await check_for_elements(page, '#seat-details > div')
        for seat in seat_details:
            access = await check_for_element(seat, '.access.tag-position.color-adapt')
            stairs = await check_for_element(seat, '.stairs.tag-position.color-adapt')
            row = await check_for_element(seat, '.row.tag-position.color-adapt')
            seat_number = await check_for_element(seat, '.seat-number.tag-position.color-adapt')
            price = await check_for_element(seat, '.tag-position-2.cc.prix')
            seats_info += f"{access.text.strip()} {stairs.text.strip()} {row.text.strip()} {seat_number.text.strip()} {price.text.strip()}" + '\n'

    except Exception as e:
        print('parse_cart_data function error:', e)
        # return False
    return seats_info


async def get_seat(page, amount, adspower_id, browser_id):
    try:
        print('in get_seat')
        print(amount, 'amount in get seat funciton')
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
                    cart_data = await parse_cart_data(page)
                    user_part    = f"User: {os.getlogin()}."
                    browser_part = f"Browser: {adspower_id if adspower_id else browser_id}"
                    tickets_part = f"*Found Tickets:*\n\n{cart_data}"
                    message = "\n".join([user_part + " " + browser_part, tickets_part])
                    send_slack_message(message)
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
                print(polygon_ids, 'polygon_ids')
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
                        time.sleep(.2)
                        await seat.mouse_click()
                        add_button = await custom_wait(page, "a[class='bt-main orange-aa w-inline-block']", timeout=3)
                        if add_button: await add_button.click()
                        # await get_stadion_ticket(page)
                        print('after click')

                if await custom_wait(page, 'div[class="ConfirmationSelectionPanel"]', timeout=5):
                    cart_data = await parse_cart_data(page)
                    user_part    = f"User: {os.getlogin()}."
                    browser_part = f"Browser: {adspower_id if adspower_id else browser_id}"
                    tickets_part = f"*Found Tickets:*\n\n{cart_data}"
                    message = "\n".join([user_part + " " + browser_part, tickets_part])
                    send_slack_message(message)
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
    

async def check_for_elements(page, selector, debug=False):
    try:
        elements = await page.query_selector_all(selector)
        return elements
    except Exception as e: 
        if debug: print('selector', selector, '\n', e)
        return False


async def main(browser_id, browsers_amount, proxy_list=None,
    adspower=None, adspower_id=None, google_sheets_data_link=None,
    google_sheets_accounts_link=None):
    global accounts, TIME_FROM_START, TIME_TO_WAIT
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
            if proxy_list:
                await driver.get(link)
                tab = driver.main_tab
                await configure_proxy(tab, proxy_list)
        
        page = await driver.get(link)
        # page = await driver.get('file:///C:/Users/vladk/OneDrive/%D0%A0%D0%B0%D0%B1%D0%BE%D1%87%D0%B8%D0%B9%20%D1%81%D1%82%D0%BE%D0%BB/order-roland-garros-html/cart.mhtml')
        # cart_data = await parse_cart_data(page)
        # print(cart_data, 'cart data!!')
        # user_part    = f"User: {os.getlogin()}."
        # browser_part = f"Browser: {adspower_id if adspower_id else browser_id}"
        # tickets_part = f"*Found Tickets:*\n\n{cart_data}"
        # message = "\n".join([user_part + " " + browser_part, tickets_part])
        # send_slack_message(message)
        # input('continue?')
        if adspower_id:
            print(Fore.GREEN + f"Browser {adspower_id if adspower_id else browser_id}: Successfully started!\n")

        
        while True:
            await check_for_element(page, '#calendarSection > div.calendarGrid > div:nth-child(1) > div > div.buttonWrapper > div > a', click=True)
            if await check_for_element(page, 'iframe[src^="https://geo.captcha-delivery.com"]'):
                user_part    = f"User: {os.getlogin()}."
                browser_part = f"Browser: {adspower_id if adspower_id else browser_id}"
                text = f"CAPTCHA"
                message = "\n".join([user_part + " " + browser_part, text])
                if datetime.now() > TIME_TO_WAIT:
                    send_slack_message(message)
                # print('trying to delete cookies')
                # delete_cookies('datadome')
                print(Fore.YELLOW + f"Browser {adspower_id if adspower_id else browser_id}: 403!\n")
                # await wait_for_captcha(page, driver)
                # time.sleep(120)
                # if proxy_list: await change_proxy(page)
                time.sleep(120)
                await page.get(link)
                time.sleep(5)
                continue
            
            if len(accounts) > 0:
                random_account = random.choice(accounts)
                login = random_account[0]
                password = random_account[1]
                auth_result = await authorization(page, login, password)
                if not auth_result:
                    print(f'Не вдалось авторизуватись. Browser {adspower_id if adspower_id else browser_id}. Наступна спроба через 60 сек.')
                    time.sleep(60)
                    continue
            
            if await check_for_element(page, '#__layout > div > div.custom-body > div > div > div.calendar.container-main > div.tunnel-popin > div.m01 > div.tunnel-popin-content > div.tunnel-popin-check > input[type=checkbox]', click=True):
                time.sleep(2)
                await check_for_element(page, '#__layout > div > div.custom-body > div > div > div.calendar.container-main > div.tunnel-popin > div.m01 > div.tunnel-popin-content > div.tunnel-popin-button-row > button', click=True)
            try:
                ticket_bot_settings = await get_indexeddb_data(page, 'TicketBotDB', 'settings')
                input_date = ticket_bot_settings.get('date')
                categories = ticket_bot_settings.get('categories')
                input_time = ticket_bot_settings.get('sessions')
                amount = int(ticket_bot_settings.get('amount')) if ticket_bot_settings.get('amount') != None else None
                desired_courts = ticket_bot_settings.get('courts')
                stop_execution_flag = ticket_bot_settings.get('stopExecutionFlag')
                advanced_settings = ticket_bot_settings.get('advancedSettings')

                if stop_execution_flag:
                    time.sleep(5)
                    continue
            except Exception as e:
                print(f"Неможливо дістати дані з IndexedDB, дані з вбудованого інтерфейсу не були знайдені на сайті.\nError: {e}")
                ticket_bot_settings = None
                if google_sheets_accounts_link:
                    try:
                        await check_for_element(page, 'body > a.integrated-settings-button', click=True)
                        google_sheets_data_input = await check_for_element(page, '#settingsFormContainer > div > div > input[name="settings"]')
                        if google_sheets_data_input and not google_sheets_data_input.text: await google_sheets_data_input.send_keys(google_sheets_data_link)
                        await check_for_element(page, '#settingsFormContainer #tickets_start', click=True)
                    except Exception as e:
                        print("can't pass google sheets accounts link into interface")
                time.sleep(60)
                continue
            try:
                if await check_for_element(page, '.stadium-image', debug=True): await check_for_element(page, 'div.nav-web > div > div > button', click=True, debug=True)
                if await check_for_element(page, 'div[class="EmptyCart container-main py-40"]', debug=True): await check_for_element(page, 'div.nav-web > div > div > button', click=True, debug=True)
                dates = await page.query_selector_all('.cal-card.lb1.w-inline-block.w-tab-link > div')

                random_advanced_setting = random.choice(advanced_settings) if advanced_settings else None
                desired_date = random_advanced_setting.get('date') if advanced_settings else input_date
                # desired_time = random_advanced_setting.get('session') if advanced_settings else input_time

                date_for_click = ''
                for date in dates:
                    if date.text == desired_date:
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
                        court = None
                        if advanced_settings:
                            date_filtered_settings = [
                                s for s in advanced_settings 
                                if desired_date == s.get("date")
                            ]

                            while date_filtered_settings:
                                # pick-and-remove in one step
                                idx = random.randrange(len(date_filtered_settings))
                                setting = date_filtered_settings.pop(idx)

                                court = await get_court(
                                    page,
                                    [setting.get("session")],
                                    [setting.get("court")],
                                )

                                if not court:
                                    # setting already removed, retry
                                    continue

                                # ─── you got a valid court ───
                                break
                        else:
                            court = await get_court(
                                page, 
                                input_time,
                                desired_courts
                            )

                        
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
                                        desired_categories = []
                                        result_categories = desired_categories if advanced_settings else categories
                                        if advanced_settings:
                                            for category_item in random_advanced_setting.get('categories'):
                                                for category, value in category_item.items():
                                                    desired_categories.append(category) if value and value >= 0 else None
                                                
                                        found_category = await get_ticket(page, result_categories)
                                        
                                        print('found category from get_ticket function', found_category)
                                        desired_category_amount = {}
                                        desired_category_to_amount = None
                                        if advanced_settings:
                                            for category_item in random_advanced_setting.get('categories'):
                                                print(category_item, 'category item')
                                                for category, value in category_item.items():
                                                    print(category, category == found_category, )
                                                    if category == found_category: desired_category_amount = category_item
                                        if desired_category_amount:
                                            print(desired_category_amount, 'desired_category_amount')
                                            desired_category_to_amount = desired_category_amount[found_category]
                                        result_amount = desired_category_to_amount if advanced_settings else amount
                                        print(result_amount, 'result_amount')
                                        if found_category:
                                            print(found_category)
                                            if await get_polygon(page):
                                                if await get_seat(page, result_amount, adspower_id, browser_id):
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


def poll_sheet_every(interval: float, sheet_range: str, sheet_url: str):
    """
    Poll the Google Sheet every `interval` seconds.
    """
    global accounts
    while True:
        try:
            response = get_data_from_google_sheets(sheet_range, sheet_url.split('/d/')[1].split('/')[0])
            if not response: 
                time.sleep(interval)
                continue
            
            accounts = response
        except Exception as e:
            print(f"Error fetching sheet data: {e!r}")
        time.sleep(interval)


@eel.expose
def start_workers(browsersAmount, proxyInput, adspowerApi,
    adspowerIds, googleSheetsDataLink=None, googleSheetsAccountsLink="https://docs.google.com/spreadsheets/d/1wP-xaf0NUIppb0hgVnhPUiihP-FfaT_WM82UQDEv4ms/edit?gid=0#gid=0"
):
    if googleSheetsAccountsLink:
        polling_thread = threading.Thread(
            target=poll_sheet_every,
            args=(60.0, "A1:B", googleSheetsAccountsLink),
            daemon=True 
        )
        polling_thread.start()
    
    threads = []
    print('start_workers', browsersAmount, proxyInput, adspowerApi,
     adspowerIds, googleSheetsDataLink, googleSheetsAccountsLink)

    # Case: using adspower API + IDs
    if not browsersAmount and all([adspowerApi, adspowerIds]):
        total = len(adspowerIds)
        for i in range(1, total + 1):
            ads_id = adspowerIds[i - 1]
            # bind i, total, ads_id into lambda defaults
            thread = threading.Thread(
                target=lambda idx=i, tot=total, aid=ads_id:
                    uc.loop().run_until_complete(
                        main(idx, tot, proxyInput, adspowerApi, aid, googleSheetsDataLink, googleSheetsAccountsLink)
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
                        main(idx, tot, proxyInput, None, None, googleSheetsDataLink, googleSheetsAccountsLink)
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


async def solve_audio_captcha(driver, digits):
    script = f"""
    (function fillCaptchaAndSubmit(digits) {{
        const inputs = Array.from(document.querySelectorAll('.audio-captcha-inputs'));
        if (inputs.length !== 6) {{
            console.warn(`Expected 6 inputs, but found ${{inputs.length}}`);
        }}

        inputs.forEach((input, i) => {{
            // small stagger so that your site's focus-handling has time to run
            setTimeout(() => {{
            // get the digit from the passed array (stringify in case it's a number)
            const digit = String(digits[i] ?? '');
            input.focus();
            input.value = digit;

            // fire the events your site is probably listening for
            input.dispatchEvent(new Event('input',   {{ bubbles: true }}));
            input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true, key: digit }}));
            input.dispatchEvent(new KeyboardEvent('keyup',   {{ bubbles: true, key: digit }}));

            // once we’ve filled the last field, submit
            if (i === inputs.length - 1) {{
                setTimeout(() => {{
                const form = input.closest('form');
                if (form) form.submit();
                }}, 100); // give any final handlers a moment
            }}
            }}, i * 150);
        }});
    }}({json.dumps(digits)}))
    """

    await driver.evaluate(
        script,
        await_promise=True,
        return_by_value=True
    )


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
