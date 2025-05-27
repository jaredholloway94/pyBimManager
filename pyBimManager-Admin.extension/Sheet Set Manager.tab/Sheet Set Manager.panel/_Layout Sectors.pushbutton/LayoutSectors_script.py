from pyrevit import forms, revit
from Autodesk.Revit.DB import ViewSheet
from SheetSetManager import main
from SectorGroupsWindow import SectorGroupsWindow
from NewSectorGroupWindow import NewSectorGroupWindow

main = main()
doc = main.doc
uidoc = main.uidoc
schema = main.get_schema('SectorGroups')


window = SectorGroupsWindow('SectorGroupsWindow.xaml', main)
window.show_dialog()