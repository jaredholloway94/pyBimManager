from pyrevit import forms


class NewSheetGroupWindow(forms.WPFWindow):

    def __init__(self, xaml_file, parent):

        # Initialize the window
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main

        # Initialize lists
        self.NameTextBox.Text = None

        self.SectorGroupComboBox.ItemsSource = sorted(self.main.sector_groups.keys())
        self.SectorGroupComboBox.SelectedItem = None

        self.ViewFamilyComboBox.ItemsSource = sorted(list(filter(
            lambda x: 'Plan' in x,
            self.main.view_family_types.keys()
            )))
        
        self.ViewFamilyComboBox.SelectedItem = None
        self.ViewFamilyComboBox.SelectionChanged += self.update_view_family_types_list

        self.update_view_family_types_list(None, None)
        # self.ViewTypeComboBox.ItemsSource = []
        # self.ViewTypeComboBox.SelectedItem = None

        self.ViewNameTemplateTextBox.Text = 'level_name  +  " - "  +  scope_box_name'
        self.SheetNumberTemplateTextBox.Text = '"A1-"  +  level_name[0:3]  +  scope_box_name[-1]'
        self.SheetNameTemplateTextBox.Text = '"FLOOR PLAN - "  +  level_name  +  " - "  +  scope_box_name'

        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.CancelButton.Click += self.cancel_clicked

        return None

    
    def update_view_family_types_list(self, sender, args):
        view_family = self.ViewFamilyComboBox.SelectedItem
        if view_family in self.main.view_family_types:
            self.ViewTypeComboBox.ItemsSource = sorted(self.main.view_family_types[view_family].keys())


    def get_name(self):
        name = self.NameTextBox.Text.strip()

        if not name:
            forms.alert("Please enter a name for the new Sheet Group.")

        if name in self.main.sheet_groups:
            forms.alert("A Sheet Group with the name '{}' already exists. Please choose a different name.".format(name))

        return name


    def get_sector_group_name(self):
        sector_group_name = self.SectorGroupComboBox.SelectedItem

        if not sector_group_name:
            forms.alert("Please select a Sector Group.")

        return sector_group_name
    
    
    def get_view_family_type(self):
        view_family_name = self.ViewFamilyComboBox.SelectedItem
        view_type_name = self.ViewTypeComboBox.SelectedItem

        if not view_family_name or not view_type_name:
            forms.alert("Please select a View Family and View Type.")

        if view_family_name not in self.main.view_family_types:
            forms.alert(f"View Family '{view_family_name}' not found.")

        view_family_type = self.main.view_family_types[view_family_name][view_type_name]

        return view_family_type


    # def get_levels(self):
    #     level_names = self.LevelsListBox.SelectedItems
    #     levels = [self.main.levels[name] for name in level_names]

    #     if not levels:
    #         forms.alert("Please select at least one level.")

    #     return levels
    

    # def get_scope_boxes(self):
    #     scope_box_names = self.ScopeBoxesListBox.SelectedItems
    #     scope_boxes = [self.main.scope_boxes[name] for name in scope_box_names]

    #     if not scope_boxes:
    #         forms.alert("Please select at least one Scope Box.")

    #     return scope_boxes


    def get_view_name_template_str(self):
        view_name_template_str = self.ViewNameTemplateTextBox.Text.strip()

        if not view_name_template_str:
            forms.alert("Please enter a View Name template.")

        return view_name_template_str
    

    def get_sheet_number_template_str(self):
        sheet_number_template_str = self.SheetNumberTemplateTextBox.Text.strip()

        if not sheet_number_template_str:
            forms.alert("Please enter a Sheet Number template.")

        return sheet_number_template_str
    

    def get_sheet_name_template_str(self):
        sheet_name_template_str = self.SheetNameTemplateTextBox.Text.strip()

        if not sheet_name_template_str:
            forms.alert("Please enter a Sheet Name template.")

        return sheet_name_template_str


    # def get_title_block(self, sector_group_name):
    #     sg_data = self.main.sector_groups[sector_group_name]
    #     title_block = self.main.get_element(sg_data['title_block_id'])

    #     return title_block


    # def get_title_block_center(self, title_block):
    #     tb_data = self.main.title_blocks_tab.get_data(title_block)
    #     tb_center = XYZ(tb_data['center_x'], tb_data['center_y'], 0)

    #     return tb_center


    # def get_view_scale(self, sector_group_name):
    #     sg_data = self.main.sector_groups[sector_group_name]

    #     view_scale = sg_data['view_scale']
    #     if not view_scale:
    #         forms.alert("Please enter a View Scale.")

    #     return view_scale
    

    def ok_clicked(self, sender, args):

        # Get and validate inputs from the UI
        name = self.get_name()
        sector_group_name = self.get_sector_group_name()
        view_family_type = self.get_view_family_type()
        view_name_template_str = self.get_view_name_template_str()
        sheet_number_template_str = self.get_sheet_number_template_str()
        sheet_name_template_str = self.get_sheet_name_template_str()

        # Cache Sheet Group data in main window object. It will be committed to storage from there.
        self.main.sheet_groups[name] = {
            'name': name,
            'sector_group_name': sector_group_name,
            'view_type_id': view_family_type.Id.IntegerValue,
            'view_name_template_str': view_name_template_str,
            'sheet_number_template_str': sheet_number_template_str,
            'sheet_name_template_str': sheet_name_template_str,
            'view_ids': [],
            'sheet_ids': []
            }

        self.DialogResult = True
        self.Close()


    def cancel_clicked(self, sender, args):
        self.DialogResult = False
        self.Close()