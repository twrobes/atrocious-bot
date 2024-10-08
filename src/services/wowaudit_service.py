import logging
from typing import Tuple

import aiohttp

from env import WOWAUDIT_TOKEN

''' json example
    {
      "report_id": "84ywk9eay1akcwS1dfY31j",
      "character_id": 123,
      "character_name": "Sheday",
      "configuration_name": "Single Target",
      "replace_manual_edits": true,
      "clear_conduits": true
    }
'''

wowaudit_auth_header = {
    'Authorization': WOWAUDIT_TOKEN
}


async def post_wishlist(character_name: str, report_id: str) -> Tuple[bool, str]:
    url = 'https://wowaudit.com/v1/wishlists'
    wishlist_json = {
        'report_id': report_id,
        'character_name': character_name,
        'configuration_name': 'Single Target',
        'replace_manual_edits': True,
        'clear_conduits': True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=wishlist_json, headers=wowaudit_auth_header) as response:
            response_json = await response.json()

    if response.ok:
        if response_json['created']:
            return True, ''

        # The geniuses at wowaudit have a bug where some responses have 'error:' as the key which is what the
        # documentation says, but they have 'error' on other types of responses, so try both and see which one works
        try:
            error_msg = response_json['error:']
        except KeyError:
            error_msg = response_json['error']

        print(f'ERROR - wowaudit failed to update player wishlist: {error_msg}')
        return False, error_msg

    try:
        error_msg = response_json['error:']
    except KeyError:
        error_msg = response_json['error']

    print(f'ERROR - wowaudit responded with status code: {str(response.status)} and error: {error_msg}')
    return False, error_msg


async def get_character_list() -> Tuple[bool, list]:
    url = 'https://wowaudit.com/v1/characters'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=wowaudit_auth_header) as response:
            response_json = await response.json()

    if response.ok:
        if len(response_json) == 0:
            logging.error(f'The character list was empty: {response_json}')
            return False, []
        elif len(response_json) == 1:
            if len(response_json[0]) < 0:
                logging.error(f'The character list had one dict and it was empty: {response_json}')
                return False, []
            else:
                return True, response_json
        else:
            return True, response_json
    else:
        logging.error(f'Response returned a bad status code: {response.status}')
        return False, []
