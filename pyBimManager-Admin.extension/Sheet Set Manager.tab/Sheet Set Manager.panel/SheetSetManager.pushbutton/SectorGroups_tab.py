from pyrevit import revit, forms
from Autodesk.Revit.DB import ElementId
from NewSectorGroup_window import NewSectorGroupWindow


class SectorGroupsTab(object):

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
        self.main.AssociateScopeBoxes.Click += self.associate_scope_boxes
        self.main.DeleteSectorGroup.Click += self.delete_sector_group
        
        self.main.SectorGroupsListBox.SelectionChanged += self.update_details

        # Initialize lists
        self.update_lists()

        self.ui_fields = {

            self.main.SectorGroupDetails_TitleBlockFamily:
                lambda sector_group_data: str(
                    self.main.get_element(sector_group_data['title_block_id']).FamilyName
                    ),

            self.main.SectorGroupDetails_TitleBlockType:
                lambda sector_group_data: str(
                    self.main.get_element(sector_group_data['title_block_id']).LookupParameter('Type Name').AsString()
                    ),

            self.main.SectorGroupDetails_OverallScopeBox:
                lambda sector_group_data: str(
                    self.main.get_element(sector_group_data['overall_scope_box_id']).Name
                    ),

            self.main.SectorGroupDetails_ViewScale:
                lambda sector_group_data: str(
                    '1 : {}'.format(sector_group_data['view_scale'])
                    ),

            self.main.SectorGroupDetails_ReferencePlaneIds:
                lambda sector_group_data: str(
                    ', '.join([ str(rp_id) for rp_id in sector_group_data['reference_plane_ids'] ])
                    ),

            self.main.SectorGroupDetails_SectorScopeBoxes:
                lambda sector_group_data: str(
                    ', '.join([ self.main.get_element(sb_id).Name for sb_id in sector_group_data['sector_scope_box_ids'] ])
                    ),
            
            }
        
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
            self.main.SectorGroupsListBox.ItemsSource = []
        else:
            self.main.sector_groups = sector_groups
            self.main.SectorGroupsListBox.ItemsSource = sorted(self.main.sector_groups.keys())

        return None


    def update_details(self, sender, args):
        sg_name = self.main.SectorGroupsListBox.SelectedItem

        if not sg_name:
            for field,value in self.ui_fields.items():
                field.Text = ''

                return None

        sg_data = self.main.sector_groups[sg_name]

        for field,value in self.ui_fields.items():
            field.Text = value(sg_data) if value(sg_data) else ''
            
        return None


    def new_sector_group(self, sender, args):

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
        result = dlg.show_dialog()

        if result:
            self.set_data()
            self.update_lists()
            self.update_details(sender, args)

            forms.alert(
                title='Sector Group Created',
                msg='Sector Group "{}" created successfully.\n'.format(dlg.NameTextBox.Text.strip()),
                sub_msg =
                    'Due to limitations in the Revit API, this tool cannot create Scope Boxes for you.\n\n' +
                    'After leaving this dialog, please click OK in the main window to save your changes and close the main window, then manually create and name Scope Boxes for this Sector group.\n\n' +
                    'If you chose to create Reference Planes in the last window, you can use them as guides for the Scope Box boundaries.\n\n' +
                    'When you are done, retun to this window to Associate the Scope Boxes with this new Sector Group.\n\n'
                )

        return None
    

    def rename_sector_group(self, sender, args): 

        sg_name = self.main.SectorGroupsListBox.SelectedItem
        sg_data = self.main.sector_groups[sg_name]

        new_name = forms.ask_for_string(
            prompt='Enter a new name for the Sector Group "{}":'.format(sg_name),
            default=sg_name,
            title='Rename Sector Group'
            )
        
        if not new_name:
            forms.alert('You must enter a name for the Sector Group.')
            return None
        
        if new_name in self.main.sector_groups:
            forms.alert('A Sector Group with the name "{}" already exists.'.format(new_name))
            return None
        
        self.main.sector_groups[new_name] = self.main.sector_groups.pop(sg_name)

        self.set_data()
        self.update_lists()
        self.update_details(sender, args)

        self.main.SectorGroupsListBox.SelectedItem = new_name


    def associate_scope_boxes(self, sender, args):

        # Get the selected Sector Group and its data
        sg_name = self.main.SectorGroupsListBox.SelectedItem
        sg_data = self.main.sector_groups[sg_name]

        # Filter out the Sector Group's overall scope box from the list of available scope boxes
        overall_scope_box = self.main.get_element(sg_data['overall_scope_box_id'])
        available_scope_boxes = [ sb_name for sb_name in self.main.scope_boxes if sb_name != overall_scope_box.Name ]

        # Show a dialog to select Scope Boxes to associate with the Sector Group
        selected_scope_boxes = forms.SelectFromList.show(
            sorted(available_scope_boxes),
            title='Select Scope Boxes',
            multiselect=True,
        )

        if not selected_scope_boxes:
            forms.alert('No Scope Boxes selected.')
            return None
        
        sg_data['sector_scope_box_ids'] = [ self.main.scope_boxes[sb_name].Id.IntegerValue for sb_name in selected_scope_boxes ]

        self.set_data()
        self.update_lists()
        self.update_details(sender, args)

        return None


    def delete_sector_group(self, sender, args):
    
        sg_name = self.main.SectorGroupsListBox.SelectedItem
        sg_data = self.main.sector_groups[sg_name]

        ask_also_delete = ['Scope Boxes','Reference Planes']

        also_delete = forms.SelectFromList.show(
            sorted(ask_also_delete),
            title='Deleting Sector Group "{}"... Also delete these elements?'.format(sg_name),
            multiselect=True,
            button_name='Delete'
        )

        with revit.Transaction('Sheet Set Manager - Delete Sector Group'):

            if also_delete:

                if 'Scope Boxes' in also_delete:
                    for sb_id in sg_data['sector_scope_box_ids']:
                        self.main.doc.Delete(ElementId(sb_id))

                if 'Reference Planes' in also_delete:
                    for rp_id in sg_data['reference_plane_ids']:
                        self.main.doc.Delete(ElementId(rp_id))

            _ = self.main.sector_groups.pop(sg_name)

            self.set_data()

        self.update_lists()
        self.update_details(sender, args)

