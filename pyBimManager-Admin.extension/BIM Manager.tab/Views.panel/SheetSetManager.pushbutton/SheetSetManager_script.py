from pyrevit import revit, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, AccessLevel
from System import Guid

from Titleblocks_tab import TitleblocksTab
from SectorGroups_tab import SectorGroupsTab
from SheetGroups_tab import SheetGroupsTab


# Create and show the main Sheet Set Manager window
class SheetSetManagerWindow(forms.WPFWindow):
    '''
    Class to manage the main Sheet Set Manager window.
    '''

    def __init__(self, xaml_file):

        forms.WPFWindow.__init__(self, xaml_file)
        self.doc = revit.doc
        self.uidoc = revit.uidoc

        # Initialize the schemas
        self.schemas = self.init_schemas()

        # Collect model elements
        # 'Bake' to python lists to ensure consistent ordering
        self.titleblocks = list(
            FilteredElementCollector(self.doc)
                .OfCategory(BuiltInCategory.OST_TitleBlocks)
                .WhereElementIsElementType()
        )

        self.scope_boxes = list(
            FilteredElementCollector(self.doc)
                .OfCategory(BuiltInCategory.OST_VolumeOfInterest)
                .WhereElementIsNotElementType()
        )

        self.levels = list(
            FilteredElementCollector(self.doc)
                .OfCategory(BuiltInCategory.OST_Levels)
                .WhereElementIsNotElementType()
        )

        self.view_templates = list(filter(
            lambda v: v.IsTemplate,
            FilteredElementCollector(self.doc)
                .OfCategory(BuiltInCategory.OST_Views)
                .WhereElementIsNotElementType()
        ))

        # Register UI Tabs
        self.titleblock_tab = TitleblocksTab(self,self.schemas['Titleblocks'])
        self.sector_groups_tab = SectorGroupsTab(self,self.schemas['SectorGroups'])
        self.sheet_groups_tab = SheetGroupsTab(self,self.schemas['SheetGroups'])

        self._applied = False
        self._original_sector_groups = self._load_sector_groups()
        self._original_sheet_groups = self._load_sheet_groups()


    def init_schemas(self, sender, args):
        # Get or Create schemas
        schemas = {'Titleblocks': None, 'SectorGroups': None, 'SheetGroups': None}

        doc_schemas = Schema.ListSchemas()

        for schema in doc_schemas:
            if schema.SchemaName == 'JH94_SheetSetManager_Titleblocks':
                schemas['Titleblocks'] = schema
            elif schema.SchemaName == 'JH94_SheetSetManager_SectorGroups':
                schemas['SectorGroups'] = schema
            elif schema.SchemaName == 'JH94_SheetSetManager_SheetGroups':
                schemas['SheetGroups'] = schema

        for schema in schemas.keys():
            if schemas[schema] == None:

                schema_guid = Guid.NewGuid()
                schema_builder = SchemaBuilder(schema_guid)
                schema_builder.SetSchemaName('JH94_SheetSetManager_{}'.format(schema))

                if schema == 'Titleblocks':
                    schema_builder.AddSimpleField('drawing_area_width', str)
                    schema_builder.AddSimpleField('drawing_area_height', str)
                    schema_builder.AddSimpleField('drawing_area_center_x', str)
                    schema_builder.AddSimpleField('drawing_area_center_y', str)

                elif schema == 'SectorGroups':
                    schema_builder.AddSimpleField('sector_groups', str)

                elif schema == 'SheetGroups':
                    schema_builder.AddSimpleField('sheet_groups', str)

                schema_builder.SetVendorId('JH94')
                schema_builder.SetVendorDescription('Sheet Set Manager')

                schema_builder.SetReadAccessLevel(AccessLevel.Public)
                schema_builder.SetWriteAccessLevel(AccessLevel.Vendor)

                schemas[schema] = schema_builder.Finish()


    def ok_clicked(self, sender, args):
        self.titleblock_tab._commit_titleblock_configs()
        self.sector_groups_tab._commit_sector_groups()
        self.sheet_groups_tab._commit_sheet_groups()
        self._applied = True
        self.Close()


    def apply_clicked(self, sender, args):
        self.titleblock_tab._commit_titleblock_configs()
        self.sector_groups_tab._commit_sector_groups()
        self.sheet_groups_tab._commit_sheet_groups()
        self._applied = True
        # Window stays open


    def cancel_clicked(self, sender, args):
        self._pending_sector_groups = list(self._original_sector_groups)
        self._pending_sheet_groups = list(self._original_sheet_groups)
        self._refresh_sector_groups_list()
        self._refresh_sheet_groups_list()
        self._applied = False
        self.Close()


    def OnClosed(self, *args):
        # If not applied, rollback
        if not getattr(self, '_applied', False):
            self._pending_sector_groups = list(self._original_sector_groups)
            self._pending_sheet_groups = list(self._original_sheet_groups)
            self._refresh_sector_groups_list()
            self._refresh_sheet_groups_list()
        super(SheetSetManagerWindow, self).OnClosed(*args)


# Main
if __name__ == "__main__":
    window = SheetSetManagerWindow('SheetSetManager_ui.xaml')
    window.show_dialog()