import os.path as op
import json


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




with open(USERS_FILE,'r') as json_file:
    USERS = json.load(json_file)

with open(ADMINS_FILE,'r') as json_file:
    ADMINS = json.load(json_file)

with open(COMMANDS_FILE,'r') as json_file:
    COMMANDS = json.load(json_file)

with open(EXTENSIONS_FILE,'r') as json_file:
    EXTENSIONS = json.load(json_file)