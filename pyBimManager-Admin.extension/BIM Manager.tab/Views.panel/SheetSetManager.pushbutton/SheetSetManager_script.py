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

        super().__init__(xaml_file)
        self.doc = revit.doc
        self.uidoc = revit.uidoc

        # Initialize the schemas
        self.schemas = {}

        # Collect model elements
        self.title_blocks = {self.display_name(tb): tb
            for tb in list(
                FilteredElementCollector(self.doc)
                    .OfCategory(BuiltInCategory.OST_TitleBlocks)
                    .WhereElementIsElementType()
            )
        }

        self.scope_boxes = {sb.Name: sb
            for sb in list(
                FilteredElementCollector(self.doc)
                    .OfCategory(BuiltInCategory.OST_VolumeOfInterest)
                    .WhereElementIsNotElementType()
                )
            }

        self.levels = {lvl.Name: lvl
            for lvl in list(
                FilteredElementCollector(self.doc)
                    .OfCategory(BuiltInCategory.OST_Levels)
                    .WhereElementIsNotElementType()
                )
            }

        self.view_templates = {vt.Name: vt
            for vt in list(
                filter(
                    lambda v: v.IsTemplate,
                    FilteredElementCollector(self.doc)
                        .OfCategory(BuiltInCategory.OST_Views)
                        .WhereElementIsNotElementType()
                    )
                )
            }

        # Register UI Tabs
        self.title_blocks_tab = TitleBlocksTab(self)
        self.sector_groups_tab = SectorGroupsTab(self)
        # self.sheet_groups_tab = SheetGroupsTab(self)

        return None


    def display_name(self, title_block):
        display_name = '{} : {}'.format(
            title_block.FamilyName,
            title_block.LookupParameter('Type Name').AsString()
            )

        return display_name


    def get_schema(self, schema_suffix, create=True):
        # Look for the schema in the main window's schema dictionary
        if schema_suffix in self.schemas.keys():
            schema = self.schemas[schema_suffix]
        
        elif self.lookup_schema(schema_suffix):
            schema = self.lookup_schema(schema_suffix)
            self.schemas[schema_suffix] = schema

        elif create:
            schema = self.create_schema(schema_suffix)
            self.schemas[schema_suffix] = schema
        else:
            schema = None

        return schema

    
    def lookup_schema(self, schema_suffix):
        schema_name = 'JH94_SheetSetManager_{}'.format(schema_suffix)
        app_schemas = list(filter(lambda s: s.SchemaName == schema_name, Schema.ListSchemas()))
        if app_schemas:
            schema = app_schemas[0]
            self.schemas[schema_suffix] = schema
        else:
            schema = None

        return schema


    def create_schema(self, schema_suffix):
        schema_name = 'JH94_SheetSetManager_{}'.format(schema_suffix)
        schema_guid = Guid.NewGuid()
        schema_builder = SchemaBuilder(schema_guid)
        schema_builder.SetSchemaName(schema_name)
        schema_builder.AddSimpleField(COMMON_FIELD_NAME, str)
        schema_builder.SetReadAccessLevel(AccessLevel.Public)
        schema_builder.SetWriteAccessLevel(AccessLevel.Public)
        schema = schema_builder.Finish()
        self.schemas[schema_suffix] = schema

        return schema
    

    def get_entity(self, schema, element, create=True):
        entity = element.GetEntity(schema)
        
        if not entity:
            if create:
                entity = self.create_entity(schema, element)
            else:
                entity = None

        if not entity.IsValid():
            if create:
                entity = self.create_entity(schema, element)
            else:
                entity = None

        return entity


    def create_entity(self, schema, element):
        entity = Entity(schema)
        schema_suffix = schema.SchemaName.split('_')[-1]
        with revit.Transaction('Sheet Set Manager - Create {} Entity'.format(schema_suffix)):
            element.SetEntity(entity)

        return entity
        
        
    def get_data(self, entity):
        if not entity.IsValid():

            return None
        json_str = entity.Get[str](COMMON_FIELD_NAME)

        if not json_str:
            return None

        data = json.loads(json_str)
        
        if not data:
            return None

        return data
    
    
    def set_data(self, schema, element, data):
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