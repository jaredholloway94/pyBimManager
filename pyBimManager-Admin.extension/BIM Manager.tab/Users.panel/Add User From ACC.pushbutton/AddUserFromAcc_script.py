from pyrevit.forms import SelectFromList
from APS_auth import get_2legged_access_token
from APS_b360 import get_accounts, get_account_users
from pyBimManager import load_users, register_user


USERS = load_users()

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

    succeeded = []
    failed = []

    # register user(s)
    for u in selection:
        try:
            autodesk_id, name, email = u.split("  |  ")
            register_user(autodesk_id, name, email, username='')
        except:
            failed.append(u)
        else:
            succeeded.append(u)

    if len(succeeded) > 0:
        print("Successfully added hooks for these commands:\n")
        for s in succeeded:
            print("\t{}\n".format(s))

    if len(failed) > 0:
        print("Failed to add hooks for these commands:\n")
        for f in failed:
            print("\t{}\n".format(f))

else:
    # user closed the selection window
    pass
