from pyrevit import forms
from math import ceil
from Autodesk.Revit.DB import XYZ

import json
from pyrevit import revit
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, Entity, AccessLevel
from System import Guid

SECTOR_GROUPS_SCHEMA_GUID = Guid('b1e2c3d4-5f6a-7b8c-9d0e-1f2a3b4c5d6e')
SECTOR_GROUPS_SCHEMA_NAME = 'SheetSetManager_SectorGroups'

class SectorGroupsTab(object):
    def __init__(self, main_window):
        self.main = main_window
        self.main.NewSectorGroup.Click += self.new_sector_group
        self.main.RenameSectorGroup.Click += self.rename_sector_group
        self.main.DeleteSectorGroup.Click += self.delete_sector_group
        self.main.SectorGroupsListBox.SelectionChanged += self._sector_group_selected
        self.refresh_list()

    def get_project_info(self, doc):
        return doc.ProjectInformation

    def get_or_create_sector_groups_schema(self):
        from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, AccessLevel
        from System import Guid
        SECTOR_GROUPS_SCHEMA_GUID = Guid('b1e2c3d4-5f6a-7b8c-9d0e-1f2a3b4c5d6e')
        SECTOR_GROUPS_SCHEMA_NAME = 'SheetSetManager_SectorGroups'
        schema = Schema.Lookup(SECTOR_GROUPS_SCHEMA_GUID)
        if not schema:
            schema_builder = SchemaBuilder(SECTOR_GROUPS_SCHEMA_GUID)
            schema_builder.SetSchemaName(SECTOR_GROUPS_SCHEMA_NAME)
            schema_builder.AddSimpleField('sector_groups_json', str)
            schema_builder.SetReadAccessLevel(AccessLevel.Public)
            schema_builder.SetWriteAccessLevel(AccessLevel.Public)
            schema = schema_builder.Finish()
        return schema

    def get_sector_groups_from_project_info(self, doc):
        import json
        pi = self.get_project_info(doc)
        schema = self.get_or_create_sector_groups_schema()
        entity = pi.GetEntity(schema)
        if entity.IsValid():
            json_str = entity.Get[str]('sector_groups_json')
            if json_str:
                try:
                    return json.loads(json_str)
                except:
                    return []
        return []

    def save_sector_groups_to_project_info(self, doc, groups):
        import json
        from Autodesk.Revit.DB.ExtensibleStorage import Entity
        from pyrevit import revit
        pi = self.get_project_info(doc)
        schema = self.get_or_create_sector_groups_schema()
        entity = Entity(schema)
        entity.Set('sector_groups_json', json.dumps(groups, indent=2))
        with revit.Transaction('Save Sector Groups to Project Info'):
            pi.SetEntity(entity)

    def refresh_list(self):
        self.main.sector_groups = self.main._load_sector_groups()
        self.main.SectorGroupsListBox.ItemsSource = [g['name'] for g in self.main.sector_groups]
        if hasattr(self.main, 'SectorGroupNameValue'):
            self.main.SectorGroupNameValue.Text = ''
        if hasattr(self.main, 'SectorGroupTitleblockValue'):
            self.main.SectorGroupTitleblockValue.Text = ''
        if hasattr(self.main, 'SectorGroupTitleblockIdValue'):
            self.main.SectorGroupTitleblockIdValue.Text = ''
        if hasattr(self.main, 'SectorGroupScopeBoxValue'):
            self.main.SectorGroupScopeBoxValue.Text = ''
        if hasattr(self.main, 'SectorGroupScopeBoxIdValue'):
            self.main.SectorGroupScopeBoxIdValue.Text = ''
        if hasattr(self.main, 'SectorGroupViewScaleValue'):
            self.main.SectorGroupViewScaleValue.Text = ''

    def new_sector_group(self, sender, args):
        dlg = forms.WPFWindow('NewSectorGroupWindow.xaml')
        titleblocks = self.main._get_configured_titleblocks()
        dlg.TitleblockComboBox.ItemsSource = [n for n, _ in titleblocks]
        dlg.ScopeBoxComboBox.ItemsSource = [n for n, _ in self.main._get_scope_boxes()]
        if titleblocks:
            dlg.TitleblockComboBox.SelectedIndex = 0
        if self.main._get_scope_boxes():
            dlg.ScopeBoxComboBox.SelectedIndex = 0
        def ok_handler(s, a):
            group_name = dlg.NameTextBox.Text.strip()
            if not group_name:
                forms.alert('Sector Group name is required.')
                return
            groups = self.main._load_sector_groups()
            if any(g['name'] == group_name for g in groups):
                forms.alert('A sector group with this name already exists.')
                return
            titleblock_idx = dlg.TitleblockComboBox.SelectedIndex
            scope_box_idx = dlg.ScopeBoxComboBox.SelectedIndex
            if titleblock_idx < 0 or scope_box_idx < 0:
                forms.alert('Please select all fields.')
                return
            titleblock = titleblocks[titleblock_idx][1]
            scope_box = self.main._get_scope_boxes()[scope_box_idx][1]
            try:
                view_scale = int(dlg.ViewScaleTextBox.Text)
                if view_scale <= 0:
                    raise ValueError
            except:
                forms.alert('Please enter a valid positive integer for View Scale.')
                return
            titleblock_entity = get_config_entity(titleblock)
            if not titleblock_entity:
                forms.alert('Selected titleblock is not configured.')
                return
            try:
                paper_space_vp_width = float(titleblock_entity.Get[str]('drawing_area_width'))
                paper_space_vp_height = float(titleblock_entity.Get[str]('drawing_area_height'))
            except Exception as e:
                forms.alert('Could not read drawing area dimensions from titleblock: {}'.format(e))
                return
            model_space_vp_width = paper_space_vp_width * view_scale
            model_space_vp_height = paper_space_vp_height * view_scale
            overall_scope_box_bb = scope_box.get_BoundingBox(None)
            overall_min_pt = overall_scope_box_bb.Min
            overall_max_pt = overall_scope_box_bb.Max
            overall_x = overall_min_pt.X
            overall_y = overall_min_pt.Y
            overall_z = overall_min_pt.Z
            overall_width = overall_max_pt.X - overall_min_pt.X
            overall_height = overall_max_pt.Y - overall_min_pt.Y
            n_cols = ceil(overall_width / model_space_vp_width)
            n_rows = ceil(overall_height / model_space_vp_height)
            if n_cols < 1 or n_rows < 1:
                forms.alert('Viewport is larger than the overall scope box at this scale.')
                return
            new_reference_planes = []
            doc = self.main.doc
            revit = __import__('pyrevit').revit
            with revit.Transaction('Tile Reference Planes for Sector Group'):
                for col in range(n_cols + 1):
                    x = overall_x + col * model_space_vp_width
                    p0 = XYZ(x, overall_y, overall_z)
                    p1 = XYZ(x, overall_y + overall_height, overall_z)
                    col_name = '{}-Col{}'.format(group_name, col + 1)
                    ref_plane = doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), doc.ActiveView)
                    try:
                        ref_plane.Name = col_name
                    except:
                        pass
                    new_reference_planes.append({'name': col_name, 'id': ref_plane.Id.IntegerValue, 'type': 'vertical'})
                for row in range(n_rows + 1):
                    y = overall_y + row * model_space_vp_height
                    p0 = XYZ(overall_x, y, overall_z)
                    p1 = XYZ(overall_x + overall_width, y, overall_z)
                    row_name = '{}-Row{}'.format(group_name, row + 1)
                    ref_plane = doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), doc.ActiveView)
                    try:
                        ref_plane.Name = row_name
                    except:
                        pass
                    new_reference_planes.append({'name': row_name, 'id': ref_plane.Id.IntegerValue, 'type': 'horizontal'})
            group = {
                'name': group_name,
                'titleblock': titleblock.Name,
                'titleblock_id': titleblock.Id.IntegerValue,
                'scope_box': scope_box.Name,
                'scope_box_id': scope_box.Id.IntegerValue,
                'view_scale': view_scale,
                'tiled_reference_planes': new_reference_planes
            }
            groups.append(group)
            self.main._save_sector_groups(groups)
            self.refresh_list()
            pi = self.main.get_sector_project_info(self.main.doc)
            schema = get_or_create_sector_groups_schema()
            entity = pi.GetEntity(schema)
            if not entity.IsValid():
                entity = Entity(schema)
            all_groups = groups
            import json
            entity.Set('sector_groups_json', json.dumps(all_groups, indent=2))
            with revit.Transaction('Update Sector Group Reference Plane Ids'):
                pi.SetEntity(entity)
            dlg.Close()
        def cancel_handler(s, a):
            dlg.Close()
        dlg.OkButton.Click += ok_handler
        dlg.CancelButton.Click += cancel_handler
        dlg.show_dialog()

    def rename_sector_group(self, sender, args):
        idx = self.main.SectorGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sector_groups):
            forms.alert('Please select a sector group to rename.')
            return
        group = self.main.sector_groups[idx]
        new_name = forms.ask_for_string(default=group.get('name', ''), prompt='Enter a new name for the sector group:', title='Rename Sector Group')
        if not new_name:
            forms.alert('Name cannot be empty.')
            return
        if any(g['name'] == new_name for i, g in enumerate(self.main.sector_groups) if i != idx):
            forms.alert('A sector group with this name already exists.')
            return
        self.main.sector_groups[idx]['name'] = new_name
        self.main._save_sector_groups(self.main.sector_groups)
        self.refresh_list()
        self.main.SectorGroupsListBox.SelectedIndex = idx

    def delete_sector_group(self, sender, args):
        idx = self.main.SectorGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sector_groups):
            forms.alert('Please select a sector group to delete.')
            return
        group = self.main.sector_groups[idx]
        confirm = forms.alert('Are you sure you want to delete the sector group "{}"?'.format(group.get('name', '')), options=['Yes', 'No'])
        if confirm != 'Yes':
            return
        ref_plane_ids = group.get('reference_plane_ids', [])
        doc = self.main.doc
        revit = __import__('pyrevit').revit
        if ref_plane_ids:
            with revit.Transaction('Delete Reference Planes for Sector Group'):
                for ref_id in ref_plane_ids:
                    try:
                        ref_elem = doc.GetElement(ref_id)
                        if ref_elem:
                            doc.Delete(ref_elem.Id)
                    except:
                        pass
        del self.main.sector_groups[idx]
        self.main._save_sector_groups(self.main.sector_groups)
        self.refresh_list()

    def _sector_group_selected(self, sender, args):
        idx = self.main.SectorGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sector_groups):
            if hasattr(self.main, 'SectorGroupNameValue'):
                self.main.SectorGroupNameValue.Text = ''
            if hasattr(self.main, 'SectorGroupTitleblockValue'):
                self.main.SectorGroupTitleblockValue.Text = ''
            if hasattr(self.main, 'SectorGroupTitleblockIdValue'):
                self.main.SectorGroupTitleblockIdValue.Text = ''
            if hasattr(self.main, 'SectorGroupScopeBoxValue'):
                self.main.SectorGroupScopeBoxValue.Text = ''
            if hasattr(self.main, 'SectorGroupScopeBoxIdValue'):
                self.main.SectorGroupScopeBoxIdValue.Text = ''
            if hasattr(self.main, 'SectorGroupViewScaleValue'):
                self.main.SectorGroupViewScaleValue.Text = ''
            if hasattr(self.main, 'SectorGroupRefPlanesValue'):
                self.main.SectorGroupRefPlanesValue.Text = ''
            return
        group = self.main.sector_groups[idx]
        if hasattr(self.main, 'SectorGroupNameValue'):
            self.main.SectorGroupNameValue.Text = group.get('name', '')
        if hasattr(self.main, 'SectorGroupTitleblockValue'):
            self.main.SectorGroupTitleblockValue.Text = group.get('titleblock', '')
        if hasattr(self.main, 'SectorGroupTitleblockIdValue'):
            self.main.SectorGroupTitleblockIdValue.Text = str(group.get('titleblock_id', ''))
        if hasattr(self.main, 'SectorGroupScopeBoxValue'):
            self.main.SectorGroupScopeBoxValue.Text = group.get('scope_box', '')
        if hasattr(self.main, 'SectorGroupScopeBoxIdValue'):
            self.main.SectorGroupScopeBoxIdValue.Text = str(group.get('scope_box_id', ''))
        if hasattr(self.main, 'SectorGroupViewScaleValue'):
            self.main.SectorGroupViewScaleValue.Text = str(group.get('view_scale', ''))
        if hasattr(self.main, 'SectorGroupRefPlanesValue'):
            ref_planes = group.get('tiled_reference_planes', [])
            if ref_planes:
                lines = []
                for rp in ref_planes:
                    lines.append(u"{} ({}): {}".format(rp.get('name',''), rp.get('type',''), rp.get('id','')))
                self.main.SectorGroupRefPlanesValue.Text = '\n'.join(lines)
            else:
                self.main.SectorGroupRefPlanesValue.Text = ''
