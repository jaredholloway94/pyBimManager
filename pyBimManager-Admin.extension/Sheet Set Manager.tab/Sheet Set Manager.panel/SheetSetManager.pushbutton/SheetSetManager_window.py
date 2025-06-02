from pyrevit import revit, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewFamilyType, ElementId
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, AccessLevel, Entity
from collections import OrderedDict
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

    def __init__(self, xaml_file, transaction_group):

        super().__init__(xaml_file)
        self.doc = revit.doc
        self.uidoc = revit.uidoc
        self.transaction_group = transaction_group

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

        self.view_template_collector = list(
            filter(lambda v: v.IsTemplate,
                FilteredElementCollector(self.doc)
                    .OfCategory(BuiltInCategory.OST_Views)
                    .WhereElementIsNotElementType()
                )
            )
        
        # sort view templates by ViewType
        self.view_templates = {}
        for vt in self.view_template_collector:
            view_family = str(vt.ViewType)
            if view_family not in self.view_templates:
                self.view_templates[view_family] = {}
            self.view_templates[view_family][vt.Name] = vt

        
        self.view_family_type_collector = list(
            (
                FilteredElementCollector(self.doc)
                    .OfClass(ViewFamilyType)
                )
            )
        
        # sort view family types by ViewFamily
        self.view_family_types = {}
        for vft in self.view_family_type_collector:
            view_family = str(vft.ViewFamily)
            if view_family not in self.view_family_types:
                self.view_family_types[view_family] = {}
            self.view_family_types[view_family][vft.Name] = vft
        
        # View Scales
        self.view_scales = OrderedDict({
            "12\" = 1\'"     : 1,
            "6\" = 1\'"      : 2,
            "3\" = 1\'"      : 4,
            "1 1/2\" = 1\'"  : 8,
            "1\" = 1\'"      : 12,
            "3/4\" = 1\'"    : 16,
            "1/2\" = 1\'"    : 24,
            "3/8\" = 1\'"    : 32,
            "1/4\" = 1\'"    : 48,
            "3/16\" = 1\'"   : 64,
            "1/8\" = 1\'"    : 96,
            "1\" = 10\'"     : 120,
            "3/32\" = 1\'"   : 128,
            "1/16\" = 1\'"   : 192,
            "1\" = 20\'"     : 240,
            "3/64\" = 1\'"   : 256,
            "1\" = 30\'"     : 360,
            "1/32\" = 1\'"   : 384,
            "1\" = 40\'"     : 480,
            "1\" = 50\'"     : 600,
            "1\" = 60\'"     : 720,
            "1/64\" = 1\'"   : 768,
            "1\" = 80\'"     : 960,
            "1\" = 100\'"    : 1200,
            "1\" = 160\'"    : 1920,
            "1\" = 200\'"    : 2400,
            "1\" = 300\'"    : 3600,
            "1\" = 400\'"    : 4800,
        })

        # View Scales (as a list to preserve order)
        self.view_scales_list = [
            "12\" = 1\'",
            "6\" = 1\'",
            "3\" = 1\'",
            "1 1/2\" = 1\'",
            "1\" = 1\'",
            "3/4\" = 1\'",
            "1/2\" = 1\'",
            "3/8\" = 1\'",
            "1/4\" = 1\'",
            "3/16\" = 1\'",
            "1/8\" = 1\'",
            "1\" = 10\'",
            "3/32\" = 1\'",
            "1/16\" = 1\'",
            "1\" = 20\'",
            "3/64\" = 1\'",
            "1\" = 30\'",
            "1/32\" = 1\'",
            "1\" = 40\'",
            "1\" = 50\'",
            "1\" = 60\'",
            "1/64\" = 1\'",
            "1\" = 80\'",
            "1\" = 100\'",
            "1\" = 160\'",
            "1\" = 200\'",
            "1\" = 300\'",
            "1\" = 400\'",
            'Custom'
        ]

        # Register UI Tabs
        self.title_blocks_tab = TitleBlocksTab(self)
        self.sector_groups_tab = SectorGroupsTab(self)
        self.sheet_groups_tab = SheetGroupsTab(self)

        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.ApplyButton.Click += self.apply_clicked
        self.CancelButton.Click += self.cancel_clicked

        return None


    def display_name(self, title_block):
        display_name = '{} : {}'.format(
            title_block.FamilyName,
            title_block.LookupParameter('Type Name').AsString()
            )

        return display_name


    def get_element(self, elem_id_int):
        return self.doc.GetElement(ElementId(elem_id_int))


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
        
        # st = SubTransaction(self.doc)
        # st.Start()
        # element.SetEntity(entity)
        # st.Commit()

        return entity
        
        
    def get_data(self, entity):
        if not entity:
            return None

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
        
        # st = SubTransaction(self.doc)
        # st.Start()
        # element.SetEntity(entity)
        # st.Commit()

        return None

    
    def ok_clicked(self, sender, args):
        self.transaction_group.Assimilate()
        self.DialogResult = True
        self.Close()


    def apply_clicked(self, sender, args):
        self.transaction_group.Assimilate()
        self.transaction_group.Start()


    # doesn't fire when the main window is closed via the 'X' button
    def cancel_clicked(self, sender, args):
        self.transaction_group.RollBack()
        self.DialogResult = False
        self.Close()