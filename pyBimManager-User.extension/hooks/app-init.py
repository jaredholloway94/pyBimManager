from pyrevit import HOST_APP
from pyBimManager import ADMINS, USERS, COMMANDS


# Register new user
if HOST_APP.username not in USERS:
    from pyBimManager import USERS_FILE
    from pyrevit.forms import ask_for_string
    import json
    name = ask_for_string(
        default="",
        prompt="Enter your First and Last name:",
        title="Register User"
    )
    email = ask_for_string(
        default="",
        prompt="Enter your company email address:",
        title="Register User"
    )
    autodesk_id = HOST_APP.app.LoginUserId
    USERS[HOST_APP.username] = {
        "name": name,
        "email": email,
        "autodesk_id": autodesk_id
    }
    try:
        with open(USERS_FILE,'w') as json_file:
            json.dump(USERS,json_file)
    except:
        raise Exception("Unable to update central USERS file.")
