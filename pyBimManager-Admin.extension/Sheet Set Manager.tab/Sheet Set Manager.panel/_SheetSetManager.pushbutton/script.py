from pyrevit import revit
from Autodesk.Revit.DB import TransactionGroup
from SheetSetManager_window import SheetSetManagerWindow

# Main
if __name__ == "__main__":
    tg = TransactionGroup(revit.doc)
    tg.Start()
    window = SheetSetManagerWindow('SheetSetManager_window.xaml')
    if window.show_dialog() == True:
        print('True')
        tg.Commit()
    else:
        print('False')
        tg.RollBack()