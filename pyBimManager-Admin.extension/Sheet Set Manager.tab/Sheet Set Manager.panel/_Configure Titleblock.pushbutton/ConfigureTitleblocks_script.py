from pyrevit import forms, revit
from Autodesk.Revit.DB import ViewSheet
from SheetSetManager import main
from TitleBlocksWindow import TitleBlocksWindow

main = main()
doc = main.doc
uidoc = main.uidoc
schema = main.get_schema('TitleBlocks')


def get_entity(title_block, create=False):
    entity = main.get_entity(
        schema=schema,
        element=title_block,
        create=create
        )

    return entity


def get_data(title_block):
    entity = get_entity(title_block)
    data = main.get_data(entity=entity)
    
    return data


def set_data(title_block, data):
    main.set_data(
        schema=schema,
        element=title_block,
        data=data
        )
    
    return None


def configure_title_block(title_block):

    # Create a temporary sheet to get the drawing area dimensions
    with revit.Transaction("Sheet Set Manager - Create Temp Sheet"):
        temp_sheet = ViewSheet.Create(doc, title_block.Id)
        temp_sheet.SheetNumber = "temp"
        temp_sheet.Name = "temp"

    # Store the current view for later
    old_view = uidoc.ActiveView

    # Set the new sheet as the active view
    uidoc.ActiveView = temp_sheet

    # Prompt the user to select the drawing area dimensions
    forms.alert("Select the bottom-left corner of the drawing area.")

    bottom_left_corner = uidoc.Selection.PickPoint(
        "Select the bottom-left corner of the drawing area"
        )

    forms.alert("Select the top-right corner of the drawing area.")

    top_right_corner = uidoc.Selection.PickPoint(
        "Select the top-right corner of the drawing area"
        )

    # Return to the original view
    uidoc.ActiveView = old_view

    # Delete the temporary sheet
    if temp_sheet and temp_sheet.Id and temp_sheet.Id.IntegerValue > 0:
        with revit.Transaction("Sheet Set Manager - Delete Temp Sheet"):
            doc.Delete(temp_sheet.Id)

    data = {}

    # Calculate the width, height, and center of the drawing area
    data['width'] = abs(top_right_corner.X - bottom_left_corner.X)
    data['height'] = abs(top_right_corner.Y - bottom_left_corner.Y)
    data['center_x'] = ((bottom_left_corner.X + top_right_corner.X) / 2.0)
    data['center_y'] = ((bottom_left_corner.Y + top_right_corner.Y) / 2.0)


    # Store the title_block configuration in the Extensible Storage
    set_data(title_block, data)


# title_block_name = forms.SelectFromList.show(
#     context=sorted(main.not_configured_title_blocks.keys()),
#     title="Select a Title Block"
#     )



# if title_block_name:
#     title_block = main.not_configured_title_blocks[title_block_name]
#     configure_title_block(title_block)
#     forms.alert(
#         "The Title Block '{}' has been configured successfully.".format(
#             title_block_name
#             ),
#         title="Title Block Configured"
#         )







window = TitleBlocksWindow('TitleBlocksWindow.xaml', main)
window_return_val = window.show_dialog()
print(window_return_val)
