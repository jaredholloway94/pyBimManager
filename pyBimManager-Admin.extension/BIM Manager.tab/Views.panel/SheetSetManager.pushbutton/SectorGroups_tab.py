from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ
from Autodesk.Revit.DB.ExtensibleStorage import Entity
from math import ceil
import json


class SectorGroupsTab(object):
    '''
    Class to manage the Sector Groups tab in the Sheet Set Manager.
    '''

    def __init__(self, main_window):
        '''
        Initialize the Sector Groups tab.
        '''
        # Register parent window and schema
        self.main = main_window
        self.schema = self.main.get_schema('SectorGroups')

        # Register UI Event Handlers
        self.main.NewSectorGroup.Click += self.new_sector_group
        self.main.RenameSectorGroup.Click += self.rename_sector_group
        self.main.DeleteSectorGroup.Click += self.delete_sector_group
        self.main.SectorGroupsListBox.SelectionChanged += self.display_sector_group_details

        # Initialize lists
        self.main.sector_groups = {}
        self.update_sector_groups_dict()

        return None


    def get_sector_groups_entity(self):
        '''
        Get the TitleBlock schema Entity for the given Element.
        '''
        entity = self.main.get_entity(schema=self.schema, element=self.main.doc.ProjectInformation)

        if entity and entity.IsValid():
            return entity
        
        else:
            entity = Entity(self.schema)

            with revit.Transaction('Create Sector Groups Entity'):
                self.main.doc.ProjectInformation.SetEntity(entity)

            return entity
    

    def get_sector_groups_data(self):
        entity = self.get_sector_groups_entity()
        
        if entity and entity.IsValid():
            return self.main.get_data(entity)
        else:
            return None
        

    def set_sector_groups_data(self):
        self.main.set_data(schema=self.schema, element=self.main.doc.ProjectInformation, data=self.main.sector_groups)
        
        return None


    def get_sector_group_data(self, name):
        '''
        Get the TitleBlock schema Data from the given Element.
        '''
        entity = self.get_sector_groups _entity()
        
        if entity and entity.IsValid():
            return self.main.get_data(entity)
        else:
            return None
        

    def add_sector_group(self, data):

        return None
    

    def remove_sector_group(self, index):
        '''
        Remove the Sector Group at the given index from the list.
        '''
        if index < 0 or index >= len(self.main.sector_groups):
            return

        del self.main.sector_groups[index]

        # Save the updated Sector Groups array to the Project Information element
        self.entity.Set[str](self.field, json.dumps(self.main.sector_groups))

        # Update the UI
        self.update_sector_groups_list()

        return None


    def update_sector_groups_dict(self):
        '''
        Deserialize the Sector Groups JSON from the Project Information element into a variable on the main window class.
        Populate the Sector Groups ListBox from the variable.
        '''
        self.main.sector_groups = self.get_sector_groups_dict()
        self.main.SectorGroupsListBox.ItemsSource = self.main.sector_groups.keys()


    def new_sector_group(self, sender, args):
        '''
        Create a new sector group.
        '''
        # Verify that the user has configured at least one titleblock
        if len(self.main.configured_titleblocks) == 0:
            forms.alert('You must configure at least one titleblock before creating a Sector Group.')
            return
        
        # Verify that the user has created at least one scope box
        if len(self.main.scope_boxes) == 0:
            forms.alert('You must create at least one Scope Box before creating a Sector Group.')
            return


        # Spawn the New Sector Group dialog
        dlg = forms.WPFWindow('NewSectorGroup_window.xaml')

        # Populate the Titleblock and Scope Box dropdown lists
        dlg.TitleblockComboBox.ItemsSource = [self.main.get_tb_display_name(tb) for tb in self.main.configured_titleblocks]
        dlg.ScopeBoxComboBox.ItemsSource = [sb.Name for sb in self.main.scope_boxes]

        dlg.TitleblockComboBox.SelectedIndex = 0
        dlg.ScopeBoxComboBox.SelectedIndex = 0


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
            existing_sector_groups = self.main.sector_groups
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
            sb = self.main.scope_boxes[sb_i]

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

            n_cols = int(ceil(overall_width / model_space_vp_width))
            n_rows = int(ceil(overall_height / model_space_vp_height))

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
                    new_reference_planes.append(ref_plane.Id.IntegerValue)

                for row in range(n_rows + 1):
                    y = overall_y + row * model_space_vp_height
                    p0 = XYZ(overall_x, y, overall_z)
                    p1 = XYZ(overall_x + overall_width, y, overall_z)
                    row_name = '{}-Row{}'.format(new_sector_group_name, row + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = row_name
                    new_reference_planes.append(ref_plane.Id.IntegerValue)

            # Collect the Sector Group data
            new_sector_group_data = {
                'name': new_sector_group_name,
                'titleblock_family': tb.FamilyName,
                'titleblock_type': tb.LookupParameter('Type Name').AsString(),
                'titleblock_id': tb.Id.IntegerValue,
                'scope_box': sb.Name,
                'scope_box_id': sb.Id.IntegerValue,
                'view_scale': view_scale,
                'reference_plane_ids': new_reference_planes,
                'matchline_ids': [],
            }

            # Append the new Sector Group data dict to the existing Sector Groups array
            self.main.sector_groups.append(new_sector_group_data)

            # Save the updated Sector Groups array to the Project Information element
            self.entity.Set[str](self.field, json.dumps(self.main.sector_groups))

            # Update the UI
            self.update_sector_groups_list()

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

            self.main.SectorGroupDetails_TitleblockFamily.Text =    ''
            self.main.SectorGroupDetails_TitleblockType.Text =      ''
            self.main.SectorGroupDetails_OverallScopeBox.Text =     ''
            self.main.SectorGroupDetails_ViewScale.Text =           ''
            self.main.SectorGroupDetails_ReferencePlaneIds =        ''
            self.main.SectorGroupDetails_MatchlineIds =             ''
        
        else:

            sg = self.main.sector_groups[i]

            self.main.SectorGroupDetails_TitleblockFamily.Text =    sg['titleblock_family']
            self.main.SectorGroupDetails_TitleblockType.Text =      sg['titleblock_type']
            self.main.SectorGroupDetails_OverallScopeBox.Text =     sg['scope_box']
            self.main.SectorGroupDetails_ViewScale.Text =           '1 : {}'.format(sg['view_scale'])
            self.main.SectorGroupDetails_ReferencePlaneIds =        ', '.join(sg['reference_plane_ids'])
            self.main.SectorGroupDetails_MatchlineIds =             ', '.join(sg['matchline_ids'])
