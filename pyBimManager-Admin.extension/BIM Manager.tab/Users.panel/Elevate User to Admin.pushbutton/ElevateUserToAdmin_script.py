from pyrevit.forms import SelectFromList
from pyBimManager import ADMINS, ADMINS_FILE, USERS, EXTENSIONS, EXTENSIONS_FILE
import json


# get list of users to elevate to admin, from user
non_admins = [u for u in USERS if u not in ADMINS]

# if list empty, print and exit.
if len(non_admins) < 1:
    print("All registered Users are already Admins.")

else:
    # format list for user selection
    non_admins_list = [
        "{}  |  {}  |  {}  |  {}".format(
            USERS[u]['name'],
            USERS[u]['email'],
            u,
            USERS[u]['autodesk_id']
            )
        for u in non_admins
        ]

    if len(non_admins_list) > 1:
        non_admins_list.sort()

    # get selection from user
    selection = SelectFromList.show(
        non_admins_list,
        button_name="Make Admin",
        multiselect=True
        )

    # user election is empty, print and exit.
    if selection == None or []:
        print("No Users selected.")

    else:
        # update in-memory copy of ADMINS registry
        for i in selection:
            i = i.split('  |  ')[2]
            ADMINS[i] = USERS[i]

        # update stored copy of ADMINS registry
        try:
            with open(ADMINS_FILE,'w') as json_file:
                json.dump(ADMINS, json_file)
        except:
            raise Exception("Could not update admins.json.")
        else:
            print("Updated: {}".format(ADMINS_FILE))

        # update extensions.json (pyRevitCore and pyBimManager-Admin "authusers" fields)
        for i,e in enumerate(EXTENSIONS['extensions']):
            if 'authusers' in e:
                EXTENSIONS['extensions'][i]['authusers']=ADMINS.keys()

        try:
            with open(EXTENSIONS_FILE,'w') as json_file:
                json.dump(EXTENSIONS, json_file)
        except:
            raise Exception("Could not update extensions.json.")
        else:    
            print("Updated: {}".format(EXTENSIONS_FILE))
