from pyrevit import revit, forms
from Autodesk.Revit.DB import ViewSheet
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, Entity, AccessLevel
from System import Guid






TITLEBLOCK_SCHEMA_GUID = Guid('f3e2b1c4-7d8e-4f2a-9c1b-3e4f5a6b7c8d')
TITLEBLOCK_SCHEMA_NAME = 'SheetSetManager_TitleblockConfig'

def get_or_create_schema():
    schema = Schema.Lookup(TITLEBLOCK_SCHEMA_GUID)
    if not schema:
        schema_builder = SchemaBuilder(TITLEBLOCK_SCHEMA_GUID)
        schema_builder.SetSchemaName(TITLEBLOCK_SCHEMA_NAME)
        schema_builder.AddSimpleField('drawing_area_width', str)
        schema_builder.AddSimpleField('drawing_area_height', str)
        schema_builder.AddSimpleField('drawing_area_center_x', str)
        schema_builder.AddSimpleField('drawing_area_center_y', str)
        schema_builder.SetReadAccessLevel(AccessLevel.Public)
        schema_builder.SetWriteAccessLevel(AccessLevel.Public)
        schema = schema_builder.Finish()
    return schema

def get_config_entity(titleblock_type):
    schema = get_or_create_schema()
    entity = titleblock_type.GetEntity(schema)
    if entity.IsValid():
        return entity
    return None

def set_config_entity(titleblock_type, width, height, center_x, center_y):
    schema = get_or_create_schema()
    entity = Entity(schema)
    entity.Set('drawing_area_width', str(width))
    entity.Set('drawing_area_height', str(height))
    entity.Set('drawing_area_center_x', str(center_x))
    entity.Set('drawing_area_center_y', str(center_y))
    with revit.Transaction('Set Titleblock Drawing Area Config'):
        titleblock_type.SetEntity(entity)






class TitleblocksTab(object):
    def __init__(self, main_window):
        self.main = main_window
        self.main.Configure.Click += self.configure_sheet
        self.main.ConfiguredListBox.SelectionChanged += self.show_details
        self.refresh_lists()

    def refresh_lists(self):
        self.main.configured_names = []
        self.main.not_configured_names = []
        self.main.configured_types = []
        self.main.not_configured_types = []
        for tb in self.main.titleblock_types:
            entity = self.get_config_entity(tb)
            if entity:
                self.main.configured_names.append(tb.Name)
                self.main.configured_types.append(tb)
            else:
                self.main.not_configured_names.append(tb.Name)
                self.main.not_configured_types.append(tb)
        self.main.NotConfiguredListBox.ItemsSource = self.main.not_configured_names
        self.main.ConfiguredListBox.ItemsSource = self.main.configured_names

    def show_details(self, sender, args):
        idx = self.main.ConfiguredListBox.SelectedIndex
        if idx < 0:
            self.main.set_details(None)
            return
        tb = self.main.configured_types[idx]
        entity = self.get_config_entity(tb)
        self.main.set_details(entity)

    def configure_sheet(self, sender, args):
        selected_index = self.main.NotConfiguredListBox.SelectedIndex
        if selected_index < 0:
            forms.alert("Please select a titleblock to configure.")
            return
        selected_titleblock = self.main.not_configured_types[selected_index]
        self.main.Close()
        self._configure_sheet_workflow(selected_titleblock)

    def _configure_sheet_workflow(self, selected_titleblock):
        revit = __import__('pyrevit').revit
        doc = self.main.doc
        uidoc = self.main.uidoc
        with revit.Transaction("Create Sheet"):
            new_sheet = ViewSheet.Create(doc, selected_titleblock.Id)
            new_sheet.SheetNumber = "temp"
            new_sheet.Name = "temp"
        old_view = uidoc.ActiveView
        uidoc.ActiveView = new_sheet
        forms.alert("Select the bottom-left corner of the drawing area.")
        bottom_left_corner = uidoc.Selection.PickPoint("Select the bottom-left corner of the drawing area")
        forms.alert("Select the top-right corner of the drawing area.")
        top_right_corner = uidoc.Selection.PickPoint("Select the top-right corner of the drawing area")
        width = abs(top_right_corner.X - bottom_left_corner.X)
        height = abs(top_right_corner.Y - bottom_left_corner.Y)
        center_x = ((bottom_left_corner.X + top_right_corner.X) / 2.0)
        center_y = ((bottom_left_corner.Y + top_right_corner.Y) / 2.0)
        uidoc.ActiveView = old_view
        if new_sheet and new_sheet.Id and new_sheet.Id.IntegerValue > 0:
            with revit.Transaction("Delete Temp Sheet"):
                doc.Delete(new_sheet.Id)
        self.set_config_entity(selected_titleblock, width, height, center_x, center_y)
        new_window = self.main.__class__('ui.xaml', self.main.titleblock_types)
        new_window.show_dialog()

    def get_or_create_schema(self):
        TITLEBLOCK_SCHEMA_GUID = Guid('f3e2b1c4-7d8e-4f2a-9c1b-3e4f5a6b7c8d')
        TITLEBLOCK_SCHEMA_NAME = 'SheetSetManager_TitleblockConfig'
        schema = Schema.Lookup(TITLEBLOCK_SCHEMA_GUID)
        if not schema:
            schema_builder = SchemaBuilder(TITLEBLOCK_SCHEMA_GUID)
            schema_builder.SetSchemaName(TITLEBLOCK_SCHEMA_NAME)
            schema_builder.AddSimpleField('drawing_area_width', str)
            schema_builder.AddSimpleField('drawing_area_height', str)
            schema_builder.AddSimpleField('drawing_area_center_x', str)
            schema_builder.AddSimpleField('drawing_area_center_y', str)
            schema_builder.SetReadAccessLevel(AccessLevel.Public)
            schema_builder.SetWriteAccessLevel(AccessLevel.Public)
            schema = schema_builder.Finish()
        return schema

    def get_config_entity(self, titleblock_type):
        schema = self.get_or_create_schema()
        entity = titleblock_type.GetEntity(schema)
        if entity.IsValid():
            return entity
        return None

    def set_config_entity(self, titleblock_type, width, height, center_x, center_y):
        schema = self.get_or_create_schema()
        entity = Entity(schema)
        entity.Set('drawing_area_width', str(width))
        entity.Set('drawing_area_height', str(height))
        entity.Set('drawing_area_center_x', str(center_x))
        entity.Set('drawing_area_center_y', str(center_y))
        with revit.Transaction('Set Titleblock Drawing Area Config'):
            titleblock_type.SetEntity(entity)
