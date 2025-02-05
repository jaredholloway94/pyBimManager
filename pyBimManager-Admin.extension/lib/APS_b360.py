import json, requests
# from pyrevit.forms import SelectFromList
from APS_auth import get_2legged_access_token


def get_accounts():

    token = get_2legged_access_token('data:read')
    
    r = requests.get(
        url = 'https://developer.api.autodesk.com/project/v1/hubs/',
        headers = {
            'Authorization':'Bearer {}'.format(token)
            }
        )
    
    data = json.loads(r.content)['data']
    
    accounts = []
    
    for i,a in enumerate(data):
        name = data[i]['attributes']['name']
        id = data[i]['id'][2:]
        accounts.append(
            {
                'name':name,
                'id':id
            }
        )

    return accounts


def get_account_users(account_id=None):

    if account_id == None:
        accounts = get_accounts()
        if len(accounts) < 1:
            raise Exception("No ACC accounts available to user.")
        elif len(accounts) == 1:
            account_id = accounts[0]['id']
        else:
            # formatted_list = [
            #     "{}  |  {}".format(a['name'],a['id'])
            #     for a in accounts
            #     ]
            # selection = SelectFromList(
            #     formatted_list,
            #     button_name="Get Users",
            #     multiselect=False
            # )
            # account_id = selection.split("  |  ")[1]
            pass

    token = get_2legged_access_token('account:read')


    def get_batch(users, offset):

        r = requests.get(
            url = 'https://developer.api.autodesk.com/hq/v1/accounts/{}/users?limit=100&offset={}'.format(account_id,offset),
            headers = {'Authorization':'Bearer {}'.format(token)}
            )
        
        data = json.loads(r.content)

        if len(data) > 0:
            offset += 100
            users.extend(data)
            return get_batch(users,offset)
        else:
            return users

    user_list = []
    users = get_batch(user_list,0)
    return users
