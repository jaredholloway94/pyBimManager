import clr
import os
import json
from pyrevit import revit, forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ViewFamilyType, ViewSheet, XYZ, SpecTypeId, UnitTypeId, Transaction, ReferencePlane, XYZ, Plane, SketchPlane
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, Entity, Field, AccessLevel
from System import Guid
from math import ceil
from titleblock_tab import TitleblocksTab
from sector_groups_tab import SectorGroupsTab
from sheet_groups_tab import SheetGroupsTab

# Unique GUID for the ExtensibleStorage schema
TITLEBLOCK_SCHEMA_GUID = Guid('f3e2b1c4-7d8e-4f2a-9c1b-3e4f5a6b7c8d')
TITLEBLOCK_SCHEMA_NAME = 'SheetSetManager_TitleblockConfig'

SECTOR_GROUPS_SCHEMA_GUID = Guid('b1e2c3d4-5f6a-7b8c-9d0e-1f2a3b4c5d6e')
SECTOR_GROUPS_SCHEMA_NAME = 'SheetSetManager_SectorGroups'

SHEET_GROUPS_SCHEMA_GUID = Guid('c2d3e4f5-6a7b-8c9d-0e1f-2a3b4c5d6e7f')
SHEET_GROUPS_SCHEMA_NAME = 'SheetSetManager_SheetGroups'

# Main logic

doc = revit.doc
uidoc = revit.uidoc

titleblock_type_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()

scope_box_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType()

floor_plan_view_type_collector = FilteredElementCollector(doc).OfClass(ViewFamilyType).WhereElementIsElementType()
floor_plan_view_type = sorted([v for v in floor_plan_view_type_collector if v.FamilyName == 'Floor Plan'], key=lambda x: x.Name)

# Create and show the WPF window
class SheetSetManagerWindow(forms.WPFWindow):
    def __init__(self, xaml_file, titleblock_types):
        forms.WPFWindow.__init__(self, xaml_file)
        self.titleblock_types = list(titleblock_types)
        self.doc = doc
        self.uidoc = uidoc
        # Compose tab logic
        self.titleblock_tab = TitleblocksTab(self)
        self.sector_groups_tab = SectorGroupsTab(self)
        self.sheet_groups_tab = SheetGroupsTab(self)
        self._applied = False
        self._original_sector_groups = self._load_sector_groups()
        self._original_sheet_groups = self._load_sheet_groups()

    def set_details(self, entity):
        if entity:
            width = self.titleblock_tab.get_config_entity(entity).Get[str]('drawing_area_width')
            height = self.titleblock_tab.get_config_entity(entity).Get[str]('drawing_area_height')
            center_x = self.titleblock_tab.get_config_entity(entity).Get[str]('drawing_area_center_x')
            center_y = self.titleblock_tab.get_config_entity(entity).Get[str]('drawing_area_center_y')
        else:
            width = height = center_x = center_y = ''
        self.WidthValue.Text = width
        self.HeightValue.Text = height
        self.CenterXValue.Text = center_x
        self.CenterYValue.Text = center_y

    def show_details(self, sender, args):
        idx = self.ConfiguredListBox.SelectedIndex
        if idx < 0:
            self.set_details(None)
            return
        tb = self.configured_types[idx]
        entity = self.titleblock_tab.get_config_entity(tb)
        self.set_details(entity)

    def ok_clicked(self, sender, args):
        self.sector_groups_tab._commit_sector_groups()
        self.sheet_groups_tab._commit_sheet_groups()
        self._applied = True
        self.Close()

    def apply_clicked(self, sender, args):
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

    def _refresh_sector_groups_list(self):
        self.sector_groups = self._load_sector_groups()
        self.sector_groups_tab.SectorGroupsListBox.ItemsSource = [g['name'] for g in self.sector_groups]
        # Only clear details fields that exist in the UI
        if hasattr(self, 'SectorGroupNameValue'):
            self.SectorGroupNameValue.Text = ''
        if hasattr(self, 'SectorGroupTitleblockValue'):
            self.SectorGroupTitleblockValue.Text = ''
        if hasattr(self, 'SectorGroupTitleblockIdValue'):
            self.SectorGroupTitleblockIdValue.Text = ''
        if hasattr(self, 'SectorGroupScopeBoxValue'):
            self.SectorGroupScopeBoxValue.Text = ''
        if hasattr(self, 'SectorGroupScopeBoxIdValue'):
            self.SectorGroupScopeBoxIdValue.Text = ''
        if hasattr(self, 'SectorGroupViewScaleValue'):
            self.SectorGroupViewScaleValue.Text = ''

    def _refresh_sheet_groups_list(self):
        self.sheet_groups = self._load_sheet_groups()
        self.sheet_groups_tab.SheetGroupsListBox.ItemsSource = [g['name'] for g in self.sheet_groups]
        self.sheet_groups_tab.SheetGroupNameValue.Text = ''
        self.sheet_groups_tab.SheetGroupDescriptionValue.Text = ''
        self.sheet_groups_tab.SheetGroupOtherValue.Text = ''

# Launch the window
if __name__ == "__main__":
    window = SheetSetManagerWindow('ui.xaml', titleblock_type_collector)
    window.show_dialog()