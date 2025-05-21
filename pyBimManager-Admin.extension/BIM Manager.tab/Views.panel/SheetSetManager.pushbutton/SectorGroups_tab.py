from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ
from Autodesk.Revit.DB.ExtensibleStorage import Entity
from math import ceil
import json


class SectorGroupsTab(object):
    '''
    Class to manage the Sector Groups tab in the Sheet Set Manager.
    '''

    def __init__(self, main_window, schema):
        '''
        Initialize the Sector Groups tab.
        '''
        # Register parent window and schema
        self.main = main_window
        self.schema = schema
        self.field = schema.GetField('sector_groups')

        # Initialize Sector Groups Entity
        self.entity = self.get_or_create_sector_groups_entity()

        # Register UI Event Handlers
        self.main.NewSectorGroup.Click += self.new_sector_group
        self.main.RenameSectorGroup.Click += self.rename_sector_group
        self.main.DeleteSectorGroup.Click += self.delete_sector_group
        self.main.SectorGroupsListBox.SelectionChanged += self.display_sector_group_details

        # Initialize lists
        self.refresh_sector_groups_list()

        return


    def get_or_create_sector_groups_entity(self):
        '''
        Try to retrieve the Sector Groups entity from the Project Information element.
        If it does not exist, create it and set its initial value to an empty list.
        Return the entity.
        '''
        # Try to get the Sector Groups entity from the Project Information element
        entity = self.main.doc.ProjectInformation.GetEntity(self.schema)
        # If the sector groups entity is not valid, create a new one
        if not entity.IsValid():
            self.main.sector_groups = []
            entity = Entity(self.schema)
            entity.Set[str](self.field, json.dumps(self.main.sector_groups))
            with revit.Transaction('Create Sector Groups Entity on Project Information element'):
                self.main.doc.ProjectInformation.SetEntity(entity)

        return entity


    def refresh_sector_groups_list(self):
        '''
        Deserialize the Sector Groups JSON from the Project Information element into a variable on the main window class.
        Populate the Sector Groups ListBox from the variable.
        '''
        self.main.sector_groups = json.loads(self.entity.Get[str](self.field))
        self.main.SectorGroupsListBox.ItemsSource = [sg['name'] for sg in self.main.sector_groups]


    def new_sector_group(self, sender, args):
        '''
        Create a new sector group.
        '''
        # Spawn the New Sector Group dialog
        dlg = forms.WPFWindow('NewSectorGroupWindow.xaml')

        # Populate the Titleblock and Scope Box dropdown lists
        dlg.TitleblockComboBox.ItemsSource = ['{} : {}'.format(tb.Symbol.FamilyName, tb.Name) for tb in self.main.configured_titleblocks]
        dlg.ScopeBoxComboBox.ItemsSource = [sb.Name for sb in self.main.scope_boxes]

        # Set default values for the dropdowns
        if len(self.main.configured_titleblocks) > 0:
            dlg.TitleblockComboBox.SelectedIndex = 0
        else:
            raise forms.RevitException('No configured titleblocks found.')

        if len(self.main.scope_boxes) > 0:
            dlg.ScopeBoxComboBox.SelectedIndex = 0
        else:
            raise forms.RevitException('No scope boxes found.')


        def ok_handler(sender, args):
            '''
            Handle the OK button click event.
            '''
            # Get the entered Sector Group name
            new_sector_group_name = dlg.NameTextBox.Text.strip()
            if not new_sector_group_name:
                forms.alert('Sector Group name is required.')
                return

            # Check if the name already exists
            existing_sector_groups = self.main._load_sector_groups()
            if any(sg['name'] == new_sector_group_name for sg in existing_sector_groups):
                forms.alert('A sector group with this name already exists.')
                return

            # Check if the titleblock and scope box are selected
            tb_i = dlg.TitleblockComboBox.SelectedIndex
            sb_i = dlg.ScopeBoxComboBox.SelectedIndex
            if tb_i < 0 or sb_i < 0:
                forms.alert('Please select all fields.')
                return

            # Get the selected titleblock and scope box
            tb = self.main.configured_titleblocks[tb_i]
            sb = self.main._get_scope_boxes()[sb_i]

            # Get and validate the entered View Scale
            try:
                view_scale = int(dlg.ViewScaleTextBox.Text)
                if view_scale <= 0:
                    raise ValueError
            except:
                forms.alert('Please enter a valid positive integer for View Scale.')
                return

            # Get and validate the selected titleblock entity
            titleblock_entity = tb.GetEntity(self.main.schemas['Titleblocks'])
            if not titleblock_entity:
                forms.alert('Selected titleblock is not configured.')
                return

            # Get and validate the titleblock drawing area dimensions
            try:
                paper_space_vp_width = float(titleblock_entity.Get[str]('drawing_area_width'))
                paper_space_vp_height = float(titleblock_entity.Get[str]('drawing_area_height'))
            except Exception as e:
                forms.alert('Could not read drawing area dimensions from titleblock: {}'.format(e))
                return

            # Calculate the number of rows and columns for the reference planes
            # based on the overall scope box dimensions and the view scale
            model_space_vp_width = paper_space_vp_width * view_scale
            model_space_vp_height = paper_space_vp_height * view_scale

            overall_scope_box_bb = sb.get_BoundingBox(None)

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
            
            # Create reference planes at the boundaries of the sectors
            new_reference_planes = []
            with revit.Transaction('Tile Reference Planes for Sector Group'):

                for col in range(n_cols + 1):
                    x = overall_x + col * model_space_vp_width
                    p0 = XYZ(x, overall_y, overall_z)
                    p1 = XYZ(x, overall_y + overall_height, overall_z)
                    col_name = '{}-Col{}'.format(new_sector_group_name, col + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = col_name
                    new_reference_planes.append({
                        'name': col_name,
                        'id': ref_plane.Id.IntegerValue,
                        'type': 'vertical'
                    })

                for row in range(n_rows + 1):
                    y = overall_y + row * model_space_vp_height
                    p0 = XYZ(overall_x, y, overall_z)
                    p1 = XYZ(overall_x + overall_width, y, overall_z)
                    row_name = '{}-Row{}'.format(new_sector_group_name, row + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = row_name
                    new_reference_planes.append({
                        'name': row_name,
                        'id': ref_plane.Id.IntegerValue,
                        'type': 'horizontal'
                    })

            # Collect the Sector Group data
            new_sector_group_data = {
                'name': new_sector_group_name,
                'titleblock': tb.Name,
                'titleblock_id': tb.Id.IntegerValue,
                'scope_box': sb.Name,
                'scope_box_id': sb.Id.IntegerValue,
                'view_scale': view_scale,
                'tiled_reference_planes': new_reference_planes
            }

            # Append the new Sector Group data dict to the existing Sector Groups array
            self.main.sector_groups.append(new_sector_group_data)

            # Save the updated Sector Groups array to the Project Information element
            self.entity.Set[str](self.field, json.dumps(self.main.sector_groups))

            # Update the UI
            self.refresh_sector_groups_list()

            # Close the dialog
            dlg.Close()

            return


        def cancel_handler(sender, args):
            dlg.Close()

        dlg.OkButton.Click += ok_handler
        dlg.CancelButton.Click += cancel_handler
        dlg.show_dialog()








    def rename_sector_group(self, sender, args):
        i = self.main.SectorGroupsListBox.SelectedIndex
        if i < 0 or i >= len(self.main.sector_groups):
            forms.alert('Please select a sector group to rename.')
            return
        group = self.main.sector_groups[i]
        new_name = forms.ask_for_string(default=group.get('name', ''), prompt='Enter a new name for the sector group:', title='Rename Sector Group')
        if not new_name:
            forms.alert('Name cannot be empty.')
            return
        if any(g['name'] == new_name for i, g in enumerate(self.main.sector_groups) if i != i):
            forms.alert('A sector group with this name already exists.')
            return
        self.main.sector_groups[i]['name'] = new_name
        self.main._save_sector_groups(self.main.sector_groups)
        self.refresh_list()
        self.main.SectorGroupsListBox.SelectedIndex = i


    def delete_sector_group(self, sender, args):
        i = self.main.SectorGroupsListBox.SelectedIndex
        if i < 0 or i >= len(self.main.sector_groups):
            forms.alert('Please select a sector group to delete.')
            return
        group = self.main.sector_groups[i]
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
        del self.main.sector_groups[i]
        self.main._save_sector_groups(self.main.sector_groups)
        self.refresh_list()


    def display_sector_group_details(self, sender, args):

        i = self.main.SectorGroupsListBox.SelectedIndex

        if i < 0 or i >= len(self.main.sector_groups):
            if hasattr(self.main, 'SectorGroupDetails_Name'):           self.main.SectorGroupDetails_Name.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_TitleblockName'): self.main.SectorGroupDetails_TitleblockName.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_TitleblockId'):   self.main.SectorGroupDetails_TitleblockId.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_ScopeBoxName'):   self.main.SectorGroupDetails_ScopeBoxName.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_ScopeBoxId'):     self.main.SectorGroupDetails_ScopeBoxId.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_ViewScale'):      self.main.SectorGroupDetails_ViewScale.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_RefPlaneIds'):    self.main.SectorGroupDetails_RefPlaneIds.Text = ''
            if hasattr(self.main, 'SectorGroupDetails_RefPlaneIds'):    self.main.SectorGroupDetails_RefPlaneIds.Text = ''
            return

        sg = self.main.sector_groups[i]

        if hasattr(self.main, 'SectorGroupNameValue'):
            self.main.SectorGroupNameValue.Text = sg.get('name', '')
        if hasattr(self.main, 'SectorGroupTitleblockValue'):
            self.main.SectorGroupTitleblockValue.Text = sg.get('titleblock', '')
        if hasattr(self.main, 'SectorGroupTitleblockIdValue'):
            self.main.SectorGroupTitleblockIdValue.Text = str(sg.get('titleblock_id', ''))
        if hasattr(self.main, 'SectorGroupScopeBoxValue'):
            self.main.SectorGroupScopeBoxValue.Text = sg.get('scope_box', '')
        if hasattr(self.main, 'SectorGroupScopeBoxIdValue'):
            self.main.SectorGroupScopeBoxIdValue.Text = str(sg.get('scope_box_id', ''))
        if hasattr(self.main, 'SectorGroupViewScaleValue'):
            self.main.SectorGroupViewScaleValue.Text = str(sg.get('view_scale', ''))
        if hasattr(self.main, 'SectorGroupRefPlanesValue'):
            ref_planes = sg.get('tiled_reference_planes', [])
            if ref_planes:
                lines = []
                for rp in ref_planes:
                    lines.append(u"{} ({}): {}".format(rp.get('name',''), rp.get('type',''), rp.get('id','')))
                self.main.SectorGroupRefPlanesValue.Text = '\n'.join(lines)
            else:
                self.main.SectorGroupRefPlanesValue.Text = ''
