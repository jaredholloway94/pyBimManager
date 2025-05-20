import os.path as op
import json


#### FILE LOCATIONS ####
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


#### DATA LOAD FUNCTIONS ####
def load_secrets(SECRETS_FILE=SECRETS_FILE):
    with open(SECRETS_FILE,'r') as json_file:
        SECRETS = json.load(json_file)
    return SECRETS


def load_users(USERS_FILE=USERS_FILE):
    with open(USERS_FILE,'r') as json_file:
        USERS = json.load(json_file)
    return USERS


def load_admins(ADMINS_FILE=ADMINS_FILE):
    with open(ADMINS_FILE,'r') as json_file:
        ADMINS = json.load(json_file)
    return ADMINS


def load_commands(COMMANDS_FILE=COMMANDS_FILE):
    with open(COMMANDS_FILE,'r') as json_file:
        COMMANDS = json.load(json_file)
    return COMMANDS


def load_extensions(EXTENSIONS_FILE=EXTENSIONS_FILE):
    with open(EXTENSIONS_FILE,'r') as json_file:
        EXTENSIONS = json.load(json_file)
    return EXTENSIONS


SECRETS = load_secrets()
USERS = load_users()
ADMINS = load_admins()
COMMANDS = load_commands()
EXTENSIONS = load_extensions()


#### OTHER FUNCTIONS ####
def register_user(USERS_FILE=USERS_FILE,autodesk_id=None,name=None,email=None,username=None):

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

    USERS = load_users(USERS_FILE)

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


#### TEMPLATES ####
COMMAND_HOOK_TEMPLATE = '''
from pyrevit import HOST_APP, EXEC_PARAMS
from Autodesk.Revit.UI import TaskDialog
from os.path import basename

COMMAND_ID = basename(__file__)[20:-4]

from pyBimManager import ADMINS
if HOST_APP.app.LoginUserId in ADMINS:
    pass
else:
    from pyBimManager import COMMANDS
    COMMAND = COMMANDS[COMMAND_ID]
    if HOST_APP.app.LoginUserId not in COMMAND['allowed_users']:
        TaskDialog.Show(COMMAND['command_name'],COMMAND['message'])
        EXEC_PARAMS.event_args.Cancel = True

'''
