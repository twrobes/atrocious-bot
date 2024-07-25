import logging

import aiohttp

from env import BATTLENET_CLIENT_ID, BATTLENET_CLIENT_SECRET, BLIZZARD_API_URL

CONNECTED_REALM_ENDPOINT = '/data/wow/connected-realm/3676?namespace=dynamic-us&locale=en_US'


async def update_area_52_server_status() -> str:
    token_response = await fetch_access_token()
    access_token = token_response.get('access_token')
    auth_header = {
        'Authorization': f'Bearer {access_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BLIZZARD_API_URL + CONNECTED_REALM_ENDPOINT, headers=auth_header) as response:
            response_json = await response.json()

    if response.ok:
        return response_json.get('status').get('type')
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
