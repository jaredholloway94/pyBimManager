from pyrevit import revit, forms
from Autodesk.Revit.DB import ElementId
from NewSheetGroup_window import NewSheetGroupWindow


class SheetGroupsTab(object):

    def __init__(self, main_window):
        '''
        Initialize the Sheet Groups tab.
        '''
        # Register parent window and schema
        self.main = main_window
        self.schema = self.main.get_schema('SheetGroups')

        # Register UI Event Handlers
        self.main.NewSheetGroup.Click += self.new_sheet_group
        self.main.RenameSheetGroup.Click += self.rename_sheet_group
        self.main.EditSheetGroup.Click += self.edit_sheet_group
        self.main.DeleteSheetGroup.Click += self.delete_sheet_group

        self.main.SheetGroupsListBox.SelectionChanged += self.update_details

        # Initialize lists
        self.update_lists()

        self.ui_fields = {

            self.main.SheetGroupDetails_SectorGroup:
                lambda sheet_group_data: str(
                    sheet_group_data['sector_group_name']
                    ),

            # self.main.SheetGroupDetails_TitleBlockFamily:
            #     lambda sheet_group_data: str(
            #         sheet_group_data['title_block_family']
            #         ),

            # self.main.SheetGroupDetails_TitleBlockType:
            #     lambda sheet_group_data: str(
            #         sheet_group_data['title_block_type']
            #         ),

            # self.main.SheetGroupDetails_ViewScale:
            #     lambda sheet_group_data: str(
            #         sheet_group_data['view_scale']
            #         ),

            self.main.SheetGroupDetails_ViewFamily:
                lambda sheet_group_data: str(
                    self.main.get_element(sheet_group_data['view_type_id']).ViewFamily
                    ),

            self.main.SheetGroupDetails_ViewType:
                lambda sheet_group_data: str(
                    self.main.get_element(sheet_group_data['view_type_id']).Name
                    ),

            self.main.SheetGroupDetails_Levels:
                lambda sheet_group_data: str(
                    ', '.join([ self.main.get_element(lvl_id).Name for lvl_id in sheet_group_data['level_ids'] ])
                    ),

            self.main.SheetGroupDetails_ScopeBoxes:
                lambda sheet_group_data: str(
                    ', '.join([ self.main.get_element(sb_id).Name for sb_id in sheet_group_data['scope_box_ids'] ])
                    ),

            self.main.SheetGroupDetails_ViewNameTemplate:
                lambda sheet_group_data: str(
                    sheet_group_data['view_name_template_str']
                    ),

            self.main.SheetGroupDetails_SheetNumberTemplate:
                lambda sheet_group_data: str(
                    sheet_group_data['sheet_number_template_str']
                    ),

            self.main.SheetGroupDetails_SheetNameTemplate:
                lambda sheet_group_data: str(
                    sheet_group_data['sheet_name_template_str']
                    ),

            self.main.SheetGroupDetails_Views:
                lambda sheet_group_data: str(
                    ', '.join([ self.main.get_element(v_id).Name for v_id in sheet_group_data['view_ids'] ])
                    ),
                
            self.main.SheetGroupDetails_Sheets:
                lambda sheet_group_data: str(
                    ', '.join([ self.main.get_element(s_id).Name for s_id in sheet_group_data['sheet_ids'] ])
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
        # read data from storage (does not copy to main.sheet_groups)
        entity = self.get_entity()
        data = self.main.get_data(entity=entity)

        return data


    def set_data(self):
        # write main.sheet_groups to storage
        self.main.set_data(
            schema=self.schema,
            element=self.main.doc.ProjectInformation,
            data=self.main.sheet_groups
            )
        
        return None




    def update_lists(self):
        sheet_groups = self.get_data()

        if sheet_groups == None:
            self.main.sheet_groups = {}
            self.main.SheetGroupsListBox.ItemsSource = []
        else:
            self.main.sheet_groups = sheet_groups
            self.main.SheetGroupsListBox.ItemsSource = sorted(self.main.sheet_groups.keys())

        return None


    def update_details(self, sender, args):
        sg_name = self.main.SheetGroupsListBox.SelectedItem

        if not sg_name:
            for field,value in self.ui_fields.items():
                field.Text = ''

                return None

        sg_data = self.main.sheet_groups[sg_name]

        for field,value in self.ui_fields.items():
            field.Text = value(sg_data) if value(sg_data) else ''
            
        return None
    

    def update_details(self, sender, args):
        sg_name = self.main.SheetGroupsListBox.SelectedItem

        if not sg_name:
            for field,value in self.ui_fields.items():
                field.Text = ''

                return None

        sg_data = self.main.sheet_groups[sg_name]

        for field,value in self.ui_fields.items():
            field.Text = value(sg_data) if value(sg_data) else ''
            
        return None


    def new_sheet_group(self, sender, args):

        # Verify that the user has configured at least one title block
        if not self.main.configured_title_blocks:
            forms.alert('You must configure at least one title block before creating a Sheet Group.')
            return None
        
        # Verify that the user has created at least one scope box
        if not self.main.scope_boxes:
            forms.alert('You must create at least one Scope Box before creating a Sheet Group.')
            return None
        
        # Verify that the user has created at least one sector group
        if not self.main.sector_groups:
            forms.alert('You must create at least one Sector Group before creating a Sheet Group.')
            return None
        
        # Spawn the New Sheet Group dialog
        dlg = NewSheetGroupWindow('NewSheetGroup_window.xaml', self)
        result = dlg.show_dialog()

        if result:
            self.set_data()
            self.update_lists()
            self.update_details(sender, args)

            forms.alert('Sheet Group created successfully.')

        return None


    def rename_sheet_group(self, sender, args):
        sg_name = self.main.SheetGroupsListBox.SelectedItem
        sg_data = self.main.sheet_groups[sg_name]

        new_name = forms.ask_for_string(
            prompt='Enter a new name for the Sheet Group "{}":'.format(sg_name),
            default=sg_name,
            title='Rename Sheet Group'
            )
        
        if not new_name:
            pass
        elif new_name in self.main.sheet_groups:
            forms.alert('A Sheet Group with the name "{}" already exists.'.format(new_name))
        else:
            self.main.sheet_groups[new_name] = self.main.sheet_groups.pop(sg_name)
            self.set_data()
            self.update_lists()
            self.update_details(sender, args)
            self.main.SheetGroupsListBox.SelectedItem = new_name

        return None


    def edit_sheet_group(self, sender, args):
        pass


    def delete_sheet_group(self, sender, args):
        sg_name = self.main.SheetGroupsListBox.SelectedItem
        sg_data = self.main.sheet_groups[sg_name]

        ask_also_delete = ['Views','Sheets']

        also_delete = forms.SelectFromList.show(
            sorted(ask_also_delete),
            title='Deleting Sheet Group "{}"... Also delete these elements?'.format(sg_name),
            multiselect=True,
            button_name='Delete'
            )  

        with revit.Transaction('Sheet Set Manager - Delete Sheet Group'):

            if also_delete:

                if 'Sheets' in also_delete:
                    for sheet_id in sg_data['sheet_ids']:
                        self.main.doc.Delete(ElementId(sheet_id))

                if 'Views' in also_delete:
                    for view_id in sg_data['view_ids']:
                        self.main.doc.Delete(ElementId(view_id))

            _ = self.main.sheet_groups.pop(sg_name)

            self.set_data()

        self.update_lists()
        self.update_details(sender, args)
