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
        if adspower_id:
            print(Fore.GREEN + f"Browser {adspower_id if adspower_id else browser_id}: Successfully started!\n")

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
