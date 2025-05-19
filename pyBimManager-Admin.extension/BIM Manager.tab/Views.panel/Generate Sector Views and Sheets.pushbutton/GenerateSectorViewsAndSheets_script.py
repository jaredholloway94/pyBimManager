from Autodesk.Revit.DB import *
from pyrevit import revit
from pyrevit.forms import SelectFromList, ask_for_string
from pprint import pprint


doc = revit.doc
uidoc = revit.uidoc


def pick_levels():

    level_collector = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()

    selected_levels = SelectFromList.show(
        sorted(level_collector, key=lambda x: x.Name),
        title='Select Levels',
        multiselect=True,
        name_attr='Name'
    )

    # try:
    #     assert selected_levels != None
    # except AssertionError:
    #     raise AssertionError("You must select at least one Level to create Views for.")
    # else:
    return selected_levels


def pick_scope_boxes():

    scope_box_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType()
    
    selected_scope_boxes = SelectFromList.show(
        sorted(scope_box_collector, key=lambda x: x.Name),
        title='Select Scope Boxes',
        multiselect=True,
        name_attr='Name'
    )

    # try:
    #     assert selected_scope_boxes != None
    # except AssertionError:
    #     raise AssertionError("You must select at least one Scope Box to create Views for.")
    # else:
    return selected_scope_boxes


def pick_view_type():

    view_type_collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)

    selected_view_type = SelectFromList.show(
        sorted([v for v in view_type_collector if v.FamilyName == 'Floor Plan'], key=lambda x: x.Name),
        title='Select View Type',
        name_attr='Name',
        multiselect=False,
    )

    # try:
    #     assert selected_view_type != None
    # except AssertionError:
    #     raise AssertionError("You must select a View type for the new Views.")
    # else:
    return selected_view_type


def pick_titleblock_type():

    titleblock_type_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    
    selected_titleblock_type = SelectFromList.show(
        sorted(titleblock_type_collector, key=lambda x: x.Name),
        title='Select Titleblock Type',
        name_attr='Name',
        multiselect=False,
    )

    # try:
    #     assert selected_titleblock_type != None
    # except AssertionError:
    #     raise AssertionError("You must select a Titleblock type for the new Sheets.")
    # else:
    return selected_titleblock_type


def get_titleblock_center(sheet):

    titleblock = FilteredElementCollector(doc,sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().FirstElement()

    bb = titleblock.get_BoundingBox(sheet)
    center = (bb.Min + bb.Max) / 2
    return center


def main():

    selected_levels = pick_levels()
    selected_scope_boxes = pick_scope_boxes()
    selected_view_type = pick_view_type()
    selected_titleblock_type = pick_titleblock_type()
    
    view_name_template = ask_for_string(
        default='level.Name+" - "+scope_box.Name',
        prompt='Enter string to use as View Name template: ',
        title='View Name Template'
    )

    sheet_number_template = ask_for_string(
        default='"A1-"+level.Name[0:3]+scope_box.Name[-1]',
        prompt='Enter string to use as Sheet Number template: ',
        title='Sheet Number Template'
    )

    sheet_name_template = ask_for_string(
        default='"FLOOR PLAN - "+level.Name+" - "+scope_box.Name',
        prompt='Enter string to use as Sheet Name template: ',
        title='Sheet Name Template'
    )


    t = Transaction(doc, 'Generate Views, Sheets, and Viewports')
    t.Start()

    created_views = []
    created_sheets = []

    for level in selected_levels:
        for scope_box in selected_scope_boxes:

            new_view = ViewPlan.Create(doc, selected_view_type.Id, level.Id)
            new_view.Name = eval(view_name_template)
            new_view.LookupParameter('Scope Box').Set(scope_box.Id)
            created_views.append(new_view)
            
            new_sheet = ViewSheet.Create(doc, selected_titleblock_type.Id)
            new_sheet.SheetNumber = eval(sheet_number_template)
            new_sheet.Name = eval(sheet_name_template)
            created_sheets.append(new_sheet)

            tb_center = get_titleblock_center(new_sheet)
            new_viewport = Viewport.Create(doc, new_sheet.Id, new_view.Id, tb_center)

    t.Commit()

    print("Created Views:\n")
    for view in created_views: print(f"  {view.Name}")

    print("\n\n")

    print("Created Sheets:\n")
    for sheet in created_sheets: print(f"  {sheet.SheetNumber} - {sheet.Name}")


if __name__ == '__main__':
    main()