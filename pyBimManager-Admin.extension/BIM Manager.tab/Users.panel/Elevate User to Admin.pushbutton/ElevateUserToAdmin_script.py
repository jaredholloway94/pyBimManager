from pyrevit.forms import SelectFromList, ask_for_string
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
        "  |  ".join( (u, USERS[u]['name'], USERS[u]['email'], USERS[u]['username']) )
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

    if selection:
        
        updates = 0

        for i in selection:
            autodesk_id, name, email, username = i.split('  |  ')

            # check that we have a username registered...
            if username == '':
                # ...if not, skip this user, and report the error...
                print("ERROR: Cannot elevate the following user to Admin, because their username has not been registered:\n" + 
                      "       {}\n\n".format(i) +
                      "       Have the user open a new instance of Revit. This will register their username.\n" +
                      "       Then you can return here to elevate the user to Admin.\n\n" +
                      "       Any other users selected in the previous window will not be affected - they will still be elevated to Admin.\n"
                )
            else:
                # ...else, update in-memory copy of ADMINS registry
                ADMINS[autodesk_id] = {
                    'name':name,
                    'email':email,
                    'username':username
                }
                updates += 1

        # check if any changes were made to the ADMINS registry
        if updates > 0:
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
                    EXTENSIONS['extensions'][i]['authusers'] = [ ADMINS[a]['username'] for a in ADMINS ]

            try:
                with open(EXTENSIONS_FILE,'w') as json_file:
                    json.dump(EXTENSIONS, json_file)
            except:
                raise Exception("Could not update extensions.json.")
            else:    
                print("Updated: {}".format(EXTENSIONS_FILE))

        
    else:
        # user closed the window
        pass
