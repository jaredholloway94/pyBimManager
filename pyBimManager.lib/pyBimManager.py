import os.path as op
import json


SECRETS_FILE = op.join(
    op.dirname(__file__),
    'secrets.json'
    )

ADMINS_FILE = op.join(
    op.dirname(__file__),
    'admins.json'
    )

USERS_FILE = op.join(
    op.dirname(__file__),
    'users.json'
    )

COMMANDS_FILE = op.join(
    op.dirname(__file__),
    'commands.json'
    )

EXTENSIONS_FILE = op.join(
    op.dirname(op.dirname(__file__)),
    'extensions.json'
    )

HOOKS_DIR = op.join(
    op.dirname(op.dirname(__file__)),
    'pyBimManager-User.extension',
    'hooks'
    )


with open(SECRETS_FILE,'r') as json_file:
    SECRETS = json.load(json_file)

with open(USERS_FILE,'r') as json_file:
    USERS = json.load(json_file)

with open(ADMINS_FILE,'r') as json_file:
    ADMINS = json.load(json_file)

with open(COMMANDS_FILE,'r') as json_file:
    COMMANDS = json.load(json_file)

with open(EXTENSIONS_FILE,'r') as json_file:
    EXTENSIONS = json.load(json_file)


def register_user(autodesk_id=None,name=None,email=None,username=None):

    from pyrevit import HOST_APP
    from pyrevit.forms import ask_for_string
    import json

    if autodesk_id == None:
        autodesk_id = HOST_APP.app.LoginUserId
        
    if name == None:
        name = ask_for_string(
            default="",
            prompt="Enter your First and Last name:",
            title="Register User"
        )

    if email == None:
        email = ask_for_string(
            default="",
            prompt="Enter your company email address:",
            title="Register User"
        )
    
    if username == None:
        username = HOST_APP.username

    USERS[autodesk_id] = {
        "name": name,
        "email": email,
        "username": username
    }

    try:
        with open(USERS_FILE,'w') as json_file:
            json.dump(USERS,json_file)
    except:
        raise Exception("Unable to update central USERS file.")