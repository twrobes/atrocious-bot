import requests

from src import env

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
    'Authorization': env.wowaudit_token
}


async def post_wishlist(report_id: str, character_id: str) -> bool:
    url = 'https://wowaudit.com/v1/wishlists'
    wishlist_json = {
        'report_id': report_id,
        'character_id': character_id,
        'configuration_name': 'Single Target',
        'replace_manual_edits': True,
        'clear_conduits': True
    }

    response = requests.post(url, json=wishlist_json, headers=wowaudit_auth_header)

    if response.ok:
        response_json = response.json()

        if response_json['created']:
            return True

        error_msg = response_json['error']
        print(f'ERROR - wowaudit failed to update player wishlist: {error_msg}')
        return False

    print(f'ERROR - wowaudit responded with a status code of {str(response.status_code)}')
    return False
