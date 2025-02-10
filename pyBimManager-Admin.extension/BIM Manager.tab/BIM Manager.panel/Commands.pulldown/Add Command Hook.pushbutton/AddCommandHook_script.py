from pyrevit.forms import SelectFromList
from pyBimManager import load_commands, HOOKS_DIR, COMMAND_HOOK_TEMPLATE
import os.path as op
from os import listdir


COMMANDS = load_commands()

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
    
if selection:
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
else:
    # user closed the selection window
    pass


# lite icon: https://img.icons8.com/?size=100&id=85479&format=png&color=000000
# dark icon: https://img.icons8.com/?size=100&id=85479&format=png&color=ffffff
