from typing import Tuple

import requests

from env import wowaudit_token

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
    'Authorization': wowaudit_token
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

    response = requests.post(url, json=wishlist_json, headers=wowaudit_auth_header)
    response_json = response.json()

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

    print(f'ERROR - wowaudit responded with status code: {str(response.status_code)} and error: {error_msg}')
    return False, error_msg
