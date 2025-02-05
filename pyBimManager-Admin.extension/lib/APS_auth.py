import base64, json, requests, sys, os.path
from pyBimManager import SECRETS



def get_2legged_access_token(scope):

    encoded_auth_string = base64.b64encode(
        bytes(
            "{}:{}".format(
                SECRETS['aps_client_id'],
                SECRETS['aps_client_secret']
                ),
            'utf-8'
            )
        ).decode('utf-8')
    
    r = requests.post(
        url = 'https://developer.api.autodesk.com/authentication/v2/token',
        data = 'grant_type=client_credentials&scope={}'.format(scope),
        headers = {
            'Content-Type':'application/x-www-form-urlencoded',
            'Authorization':'Basic {}'.format(encoded_auth_string)
            }
        )

    token = json.loads(r.content)['access_token']

    return token
