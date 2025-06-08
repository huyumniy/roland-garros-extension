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
import logging
import textwrap
from datetime import datetime, timedelta
from utils.sheetsApi import get_data_from_google_sheets
import nodriver as uc
import logging
import asyncio
from nodriver import cdp
import itertools
from asyncio import iscoroutine, iscoroutinefunction

TIME_FROM_START = datetime.now()
TIME_TO_WAIT = TIME_FROM_START + timedelta(minutes=5)

logger = logging.getLogger("uc.connection")

pydub.AudioSegment.converter = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
print(os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"))
init(autoreset=True)
accounts = []


async def listener_loop(self):
    while True:
        try:
            msg = await asyncio.wait_for(
                self.connection.websocket.recv(), self.time_before_considered_idle
            )
        except asyncio.TimeoutError:
            self.idle.set()
            # breathe
            # await asyncio.sleep(self.time_before_considered_idle / 10)
            continue
        except (Exception,) as e:
            # break on any other exception
            # which is mostly socket is closed or does not exist
            # or is not allowed

            logger.debug(
                "connection listener exception while reading websocket:\n%s", e
            )
            break

        if not self.running:
            # if we have been cancelled or otherwise stopped running
            # break this loop
            break

        # since we are at this point, we are not "idle" anymore.
        self.idle.clear()

        message = json.loads(msg)
        if "id" in message:
            # response to our command
            if message["id"] in self.connection.mapper:
                # get the corresponding Transaction
                tx = self.connection.mapper[message["id"]]
                logger.debug("got answer for %s", tx)
                # complete the transaction, which is a Future object
                # and thus will return to anyone awaiting it.
                tx(**message)
                self.connection.mapper.pop(message["id"])
        else:
            # probably an event
            try:
                event = cdp.util.parse_json_event(message)
                event_tx = uc.connection.EventTransaction(event)
                if not self.connection.mapper:
                    self.connection.__count__ = itertools.count(0)
                event_tx.id = next(self.connection.__count__)
                self.connection.mapper[event_tx.id] = event_tx
            except Exception as e:
                logger.info(
                    "%s: %s  during parsing of json from event : %s"
                    % (type(e).__name__, e.args, message),
                    exc_info=True,
                )
                continue
            except KeyError as e:
                logger.info("some lousy KeyError %s" % e, exc_info=True)
                continue
            try:
                if type(event) in self.connection.handlers:
                    callbacks = self.connection.handlers[type(event)]
                else:
                    continue
                if not len(callbacks):
                    continue
                for callback in callbacks:
                    try:
                        if iscoroutinefunction(callback) or iscoroutine(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.warning(
                            "exception in callback %s for event %s => %s",
                            callback,
                            event.__class__.__name__,
                            e,
                            exc_info=True,
                        )
                        raise
            except asyncio.CancelledError:
                break
            except Exception:
                raise
            continue
        
#call this after imported nodriver
#uc_fix(*nodriver module*)
def uc_fix(uc: uc):
    uc.core.connection.Listener.listener_loop = listener_loop

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
            config.add_extension(extension_path="./EditThisCookieChrome.crx")
            config.add_extension(extension_path=interface_extension_path)
            driver = await uc.Browser.create(config=config)
            if proxy_list:
                await driver.get(link)
                tab = driver.main_tab
                await configure_proxy(tab, proxy_list)
        
        page = await driver.get(link)
        if adspower_id:
            print(Fore.GREEN + f"Browser {adspower_id if adspower_id else browser_id}: Successfully started!\n")
        while True:
            await check_for_element(page, '#calendarSection > div.calendarGrid > div:nth-child(1) > div > div.buttonWrapper > div > a', click=True)
            if await check_for_element(page, 'iframe[src^="https://geo.captcha-delivery.com"]'):
                user_part    = f"User: {os.getlogin()}."
                browser_part = f"Browser: {adspower_id if adspower_id else browser_id}"
                text = f"CAPTCHA"
                message = "\n".join([user_part + " " + browser_part, text])
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
                        await check_for_element(page, 'button.integrated-settings-button', click=True)
                        google_sheets_data_input = await check_for_element(page, '#settingsFormContainer > div > div > input[name="settings"]')
                        if google_sheets_data_input and not google_sheets_data_input.text: await google_sheets_data_input.send_keys(google_sheets_data_link)
                        await check_for_element(page, '#settingsFormContainer #tickets_start', click=True)
                    except Exception as e:
                        print("can't pass google sheets accounts link into interface")
                time.sleep(60)
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
    adspowerIds, googleSheetsDataLink=None, googleSheetsAccountsLink=None,
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
    uc_fix(uc)
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
