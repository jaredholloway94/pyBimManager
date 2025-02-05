from pyrevit.forms import SelectFromList
from APS_auth import get_2legged_access_token
from APS_b360 import get_accounts, get_account_users
from pyBimManager import USERS, register_user

# get users list from acc
acc_users = get_account_users()

# pick user from list
formatted_list = [
    "  |  ".join( (u['uid'], u['name'], u['email']) )
    for u in acc_users
    ]

selection = SelectFromList.show(
    formatted_list,
    button_name="Register User(s)",
    multiselect=True
    )

if selection:
    # register user(s)
    for u in selection:
        autodesk_id, name, email = u.split("  |  ")
        register_user(autodesk_id, name, email, username='')
else:
    # user closed the selection window
    pass
