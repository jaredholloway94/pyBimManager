from pyrevit import revit, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, AccessLevel, Entity
from System import Guid
import json

from TitleBlocks_tab import TitleBlocksTab
from SectorGroups_tab import SectorGroupsTab
from SheetGroups_tab import SheetGroupsTab


# Constants
COMMON_FIELD_NAME = 'json_data'


# Create and show the main Sheet Set Manager window
class SheetSetManagerWindow(forms.WPFWindow):
    '''
    Class to manage the main Sheet Set Manager window.
    '''

    def __init__(self, xaml_file):

        super().__init__(self, xaml_file)
        self.doc = revit.doc
        self.uidoc = revit.uidoc

        # Initialize the schemas
        self.schemas = {}

        # Collect model elements
        # 'Bake' to python lists to ensure consistent ordering
        self.title_blocks = list(
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

        self.view_templates = list(filter(lambda v: v.IsTemplate,
            FilteredElementCollector(self.doc)
                .OfCategory(BuiltInCategory.OST_Views)
                .WhereElementIsNotElementType()
        ))

        # Register UI Tabs
        self.title_blocks_tab = TitleBlocksTab(self)
        self.sector_groups_tab = SectorGroupsTab(self)
        # self.sheet_groups_tab = SheetGroupsTab(self)

        # self._applied = False
        # self._original_sector_groups = self._load_sector_groups()
        # self._original_sheet_groups = self._load_sheet_groups()


    def get_schema(self, schema_suffix):

        # Look for the schema in the main window's schema dictionary
        if schema_suffix in self.schemas:
            schema = self.schemas[schema_suffix]

        else:
            schema_name = 'JH94_SheetSetManager_{}'.format(schema_suffix)

            # Look for the schema in the Revit application memory
            app_schemas = list(filter(lambda s: s.SchemaName == schema_name, Schema.ListSchemas()))
            
            # If multiple schemas are found, raise an exception
            # This should not happen, but it's a good practice to check
            if len(app_schemas) > 1:
                raise Exception('Multiple schemas found with the same name: {}'.format(schema_name))
            
            # If one schema is found, use it
            elif len(app_schemas) == 1:
                schema = app_schemas[0]
            
            # If no schema is found, create a new schema
            elif len(app_schemas) < 1:
                schema_guid = Guid.NewGuid()
                schema_builder = SchemaBuilder(schema_guid)
                schema_builder.SetSchemaName(schema_name)
                schema_builder.AddSimpleField(COMMON_FIELD_NAME, str)
                # schema_builder.SetVendorId('JH94')
                schema_builder.SetReadAccessLevel(AccessLevel.Public)
                schema_builder.SetWriteAccessLevel(AccessLevel.Public)
                schema = schema_builder.Finish()

            # If the schema had to be loaded from the application memory or created,
            # add it to the main window's schema dictionary.
            self.schemas[schema_suffix] = schema

        return schema
    

    def get_entity(self, schema, element):
        '''
        '''

        entity = element.GetEntity(schema)

        if entity:
            return entity
        else:
            return None
        
        
    def get_data(self, entity):
        '''
        '''

        json_str = entity.Get[str](COMMON_FIELD_NAME)
        
        if not json_str:
            # raise Exception('No data found on Field "{}" in Entity for Schema "{}"'.format(COMMON_FIELD_NAME, schema.SchemaName))
            return None
            
        data = json.loads(json_str)

        return data
    
    
    def set_data(self, schema, element, data):
        '''
        Set the data for the given schema and element.
        '''
        entity = Entity(schema)
        json_str = json.dumps(data)
        entity.Set[str](COMMON_FIELD_NAME, json_str)
        
        schema_suffix = schema.SchemaName.split('_')[-1]

        with revit.Transaction('Sheet Set Manager - Update {} Data'.format(schema_suffix)):
            element.SetEntity(entity)
        
        return None


    # def ok_clicked(self, sender, args):
    #     self.title_block_tab._commit_title_block_configs()
    #     self.sector_groups_tab._commit_sector_groups()
    #     self.sheet_groups_tab._commit_sheet_groups()
    #     self._applied = True
    #     self.Close()


    # def apply_clicked(self, sender, args):
    #     self.title_block_tab._commit_title_block_configs()
    #     self.sector_groups_tab._commit_sector_groups()
    #     self.sheet_groups_tab._commit_sheet_groups()
    #     self._applied = True
    #     # Window stays open


    # def cancel_clicked(self, sender, args):
    #     self._pending_sector_groups = list(self._original_sector_groups)
    #     self._pending_sheet_groups = list(self._original_sheet_groups)
    #     self._refresh_sector_groups_list()
    #     self._refresh_sheet_groups_list()
    #     self._applied = False
    #     self.Close()


    # def OnClosed(self, *args):
    #     # If not applied, rollback
    #     if not getattr(self, '_applied', False):
    #         self._pending_sector_groups = list(self._original_sector_groups)
    #         self._pending_sheet_groups = list(self._original_sheet_groups)
    #         self._refresh_sector_groups_list()
    #         self._refresh_sheet_groups_list()
    #     super(SheetSetManagerWindow, self).OnClosed(*args)


# Main
if __name__ == "__main__":
    window = SheetSetManagerWindow('SheetSetManager_window.xaml')
    window.show_dialog()