from pyrevit import revit, forms
from NewSectorGroupWindow import NewSectorGroupWindow


class SectorGroupsWindow(forms.WPFWindow):

    def __init__(self, xml_path, main):
        super().__init__(xml_path)
        self.xml_path = xml_path
        
        self.main = main
        self.schema = self.main.get_schema('SectorGroups')

        # Register UI Event Handlers
        self.NewSectorGroup.Click += self.new_sector_group
        self.RenameSectorGroup.Click += self.rename_sector_group
        self.DeleteSectorGroup.Click += self.delete_sector_group
        self.SectorGroupsListBox.SelectionChanged += self.update_details

        # Initialize lists
        self.update_lists()

        return None


    def get_entity(self):
        entity = self.main.get_entity(
            schema=self.schema,
            element=self.main.doc.ProjectInformation,
            create=True
            )

        return entity
    

    def get_data(self):
        # read data from storage (does not copy to main.sector_groups)
        entity = self.get_entity()
        data = self.main.get_data(entity=entity)

        return data


    def set_data(self):
        # write main.sector_groups to storage
        self.main.set_data(
            schema=self.schema,
            element=self.main.doc.ProjectInformation,
            data=self.main.sector_groups
            )
        
        return None


    def update_lists(self):
        sector_groups = self.get_data()
        if sector_groups == None:
            self.main.sector_groups = {}
            self.SectorGroupsListBox.ItemsSource = []
        else:
            self.main.sector_groups = sector_groups
            self.SectorGroupsListBox.ItemsSource = sorted(self.main.sector_groups.keys())
        self.SectorGroupsListBox.SelectedIndex = -1

        return None


    def update_details(self, sender, args):
        sg_name = self.main.SectorGroupsListBox.SelectedItem
        if not sg_name:
            self.SectorGroupDetails_TitleBlockFamily.Text =    ''
            self.SectorGroupDetails_TitleBlockType.Text =      ''
            self.SectorGroupDetails_OverallScopeBox.Text =     ''
            self.SectorGroupDetails_ViewScale.Text =           ''
            self.SectorGroupDetails_ReferencePlaneIds =        ''
        else:
            sg_data = self.main.sector_groups[sg_name]
            self.SectorGroupDetails_TitleBlockFamily.Text =    sg_data['title_block_family']
            self.SectorGroupDetails_TitleBlockType.Text =      sg_data['title_block_type']
            self.SectorGroupDetails_OverallScopeBox.Text =     sg_data['scope_box']
            self.SectorGroupDetails_ViewScale.Text =           '1 : {}'.format(sg_data['view_scale'])
            self.SectorGroupDetails_ReferencePlaneIds =        ', '.join(str(rp_id) for rp_id in sg_data['reference_plane_ids'])

        return None
    

    def add_sector_group(self, name, data):
        self.main.sector_groups[name] = data
        self.set_data()
        self.update_lists()


    def remove_sector_group(self, name):
        _ = self.main.sector_groups.pop(name)
        self.set_data()
        self.update_lists()

        return None


    def rename_sector_group(self, old_name, new_name):
        self.main.sector_groups[new_name] = self.main.sector_groups.pop(old_name)
        self.set_data()
        self.update_lists()


    def new_sector_group(self, sender, args):
        '''
        Create a new sector group.
        '''
        # Verify that the user has configured at least one title block
        if not self.main.configured_title_blocks:
            forms.alert('You must configure at least one title block before creating a Sector Group.')
            return None
        
        # Verify that the user has created at least one scope box
        if not self.main.scope_boxes:
            forms.alert('You must create at least one Scope Box before creating a Sector Group.')
            return None


        # Spawn the New Sector Group dialog
        dlg = NewSectorGroupWindow('NewSectorGroup_window.xaml', self)
        dlg.show_dialog()


    def rename_sector_group(self, sender, args): pass
    #     i = self.main.SectorGroupsListBox.SelectedIndex
    #     if i < 0 or i >= len(self.main.sector_groups):
    #         forms.alert('Please select a sector group to rename.')
    #         return
    #     group = self.main.sector_groups[i]
    #     new_name = forms.ask_for_string(default=group.get('name', ''), prompt='Enter a new name for the sector group:', title='Rename Sector Group')
    #     if not new_name:
    #         forms.alert('Name cannot be empty.')
    #         return
    #     if any(g['name'] == new_name for i, g in enumerate(self.main.sector_groups) if i != i):
    #         forms.alert('A sector group with this name already exists.')
    #         return
    #     self.main.sector_groups[i]['name'] = new_name
    #     self.main._save_sector_groups(self.main.sector_groups)
    #     self.refresh_list()
    #     self.main.SectorGroupsListBox.SelectedIndex = i


    def delete_sector_group(self, sender, args): pass
    #     i = self.main.SectorGroupsListBox.SelectedIndex
    #     if i < 0 or i >= len(self.main.sector_groups):
    #         forms.alert('Please select a sector group to delete.')
    #         return
    #     group = self.main.sector_groups[i]
    #     confirm = forms.alert('Are you sure you want to delete the sector group "{}"?'.format(group.get('name', '')), options=['Yes', 'No'])
    #     if confirm != 'Yes':
    #         return
    #     ref_plane_ids = group.get('reference_plane_ids', [])
    #     doc = self.main.doc
    #     revit = __import__('pyrevit').revit
    #     if ref_plane_ids:
    #         with revit.Transaction('Delete Reference Planes for Sector Group'):
    #             for ref_id in ref_plane_ids:
    #                 try:
    #                     ref_elem = doc.GetElement(ref_id)
    #                     if ref_elem:
    #                         doc.Delete(ref_elem.Id)
    #                 except:
    #                     pass

    #     del self.main.sector_groups[i]
    #     self.main._save_sector_groups(self.main.sector_groups)
    #     self.refresh_list()
