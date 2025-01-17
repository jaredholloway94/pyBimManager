from pyrevit.forms import SelectFromList
from pyBimManager import HOOKS_DIR, COMMANDS
import os.path as op
from os import listdir


COMMAND_HOOK_TEMPLATE = '''
from pyrevit.revit import HOST_APP, EXEC_PARAMS
from Autodesk.Revit.UI import TaskDialog
from os.path import basename

COMMAND_ID = basename(__file__)[20:-4]

from pyBimManager import admins
if HOST_APP.username in admins:
    pass
else:
    from pyBimManager import commands
    COMMAND = commands[COMMAND_ID]
    if HOST_APP.username not in COMMAND['allowed_users']:
        TaskDialog.Show(COMMAND['command_name'],COMMAND['message'])
        EXEC_PARAMS.event_args.Cancel = True

'''

existing_hooks = [op.basename(f)[20:-4] for f in listdir(HOOKS_DIR)]
available_hooks = [c for c in COMMANDS if c not in existing_hooks]
hooks_list = ["{}  |  {}".format(COMMANDS[c]['command_name'],c) for c in available_hooks]

if len(hooks_list) > 1:
    hooks_list.sort()

selection = SelectFromList.show(
    hooks_list,
    button_name="Add Command Hook(s)",
    multiselect=True
    )

succeeded = []
failed = []

for i in selection:
    try:
        command_id = i.split('  |  ')[1]
        hook_path = op.join(
            HOOKS_DIR,
            "command-before-exec[{}].py".format(command_id)
            )
        with open(hook_path,'w') as hook_file:
            hook_file.write(COMMAND_HOOK_TEMPLATE)
    except:
        failed.append(i)
    else:
        succeeded.append(i)

if len(succeeded) > 0:
    print("Successfully added hooks for these commands:\n")
    for s in succeeded:
        print("\t{}\n".format(s))

if len(failed) > 0:
    print("Failed to add hooks for these commands:\n")
    for f in failed:
        print("\t{}\n".format(f))
