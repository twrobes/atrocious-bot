import asyncio
import logging
import os

import aiohttp
import selenium.common
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from env import BATTLENET_CLIENT_ID, BATTLENET_CLIENT_SECRET, BLIZZARD_API_URL

CONNECTED_REALM_ENDPOINT = '/data/wow/connected-realm/3676?namespace=dynamic-us&locale=en_US'
GAME_STATUS_URL = 'https://worldofwarcraft.blizzard.com/en-us/game/status/us'
UP = 'UP'


async def get_area_52_server_status_via_api() -> bool:
    token_response = await fetch_access_token()
    access_token = token_response.get('access_token')
    auth_header = {
        'Authorization': f'Bearer {access_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BLIZZARD_API_URL + CONNECTED_REALM_ENDPOINT, headers=auth_header) as response:
            response_json = await response.json()

    if response.ok:
        if response_json.get('status').get('type') == UP:
            return True
        else:
            return False
    else:
        logging.error(f'Response returned bad status code posting to the blizzard connected realm endpoint: {response}')


async def fetch_access_token():
    async with aiohttp.ClientSession() as session:
        async with session.request(
                method="POST",
                url="https://oauth.battle.net/token",
                data={'grant_type': 'client_credentials'},
                auth=aiohttp.BasicAuth(BATTLENET_CLIENT_ID, BATTLENET_CLIENT_SECRET)

        ) as response:
            return await response.json()


async def get_area_52_server_status_via_webpage() -> int | bool:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")

    if os.name == 'nt':
        chrome_install = ChromeDriverManager().install()
        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")
        chrome_service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    else:
        chrome_service = Service(executable_path='/usr/bin/chromedriver', options=chrome_options)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    try:
        driver.get(GAME_STATUS_URL)
    except (BaseException, selenium.common.NoSuchElementException):
        logging.error('Unable to get the WoW Realm Status page.')
        return 0

    await asyncio.sleep(2)

    try:
        sibling = driver.find_element(By.XPATH, '//*[contains(text(), "Area 52")]')
    except (BaseException, selenium.common.NoSuchElementException):
        logging.error('Could not find the Area 52 realm name div.')
        return 0

    try:
        parent = sibling.find_element(By.XPATH, '..')
    except (BaseException, selenium.common.NoSuchElementException):
        logging.error('Could not find the parent div of the Area 52 realm name div.')
        return 0

    try:
        parent.find_element(By.XPATH, '//*[1]').find_element(By.CLASS_NAME, 'Icon--checkCircleGreen')
        return True
    except (BaseException, selenium.common.NoSuchElementException):
        logging.warning('Could not find a checkCircleGreen class name for the server status column of the WoW Realm Status website.')
        return False
