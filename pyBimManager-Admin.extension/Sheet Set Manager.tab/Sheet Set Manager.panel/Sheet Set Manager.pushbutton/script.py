from pyrevit import revit
from Autodesk.Revit.DB import TransactionGroup
from SheetSetManager_window import SheetSetManagerWindow

# Main
if __name__ == "__main__":
    
    transaction_group = TransactionGroup(revit.doc)
    transaction_group.Start()
    transaction_group.SetName("Sheet Set Manager")

    window = SheetSetManagerWindow('SheetSetManager_window.xaml', transaction_group)
    result = window.show_dialog()

    # handle case when the user closes the window via the 'X' button
    if transaction_group.HasStarted():
        transaction_group.RollBack()


# icon: https://icons8.com/icon/LoJeUoSeKwC0/project-setup