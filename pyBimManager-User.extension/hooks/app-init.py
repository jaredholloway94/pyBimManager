from pyrevit import HOST_APP
from pyBimManager import USERS, USERS_FILE, register_user


#### USER REGISTRATION ####
autodesk_id = HOST_APP.app.LoginUserId

# register new users
if autodesk_id not in USERS:
    register_user()

# if autodesk_id IS in USERS, but username is missing (because ADMIN added user from ACC), update username
# see "../../pyBimManager-Admin.extension/BIM Manager.tab/Users.panel/Add User From ACC.pushbutton/AddUserFromAcc_script.py"
elif USERS[autodesk_id]['username'] == '':
    USERS[autodesk_id]['username'] = HOST_APP.username
    import json
    try:
        with open(USERS_FILE,'w') as json_file:
            json.dump(USERS,json_file)
    except:
        raise Exception("Unable to update central USERS file.")