from pyrevit import forms
from safe_eval import safe_eval


class NewSheetGroupWindow(forms.WPFWindow):

    def __init__(self, xaml_file, parent):

        # Initialize the window
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main

        self.default_view_name_template_str = 'view_type_name.upper()+" - "+level_name.upper()+" - "+scope_box_name.upper()'
        self.default_sheet_number_template_str = 'sheet_group_name[0:2]+"-"+level_name[0:3]+scope_box_name[-1]'
        self.default_sheet_name_template_str = 'view_type_name.upper()+" - "+level_name.upper()+" - "+scope_box_name.upper()'

        self.ViewNameTemplateTextBox.Text = self.default_view_name_template_str
        self.SheetNumberTemplateTextBox.Text = self.default_sheet_number_template_str
        self.SheetNameTemplateTextBox.Text = self.default_sheet_name_template_str

        self.NameTextBox.TextChanged += self.update_view_name_template_example
        self.NameTextBox.TextChanged += self.update_sheet_number_template_example
        self.NameTextBox.TextChanged += self.update_sheet_name_template_example

        self.SectorGroupComboBox.ItemsSource = sorted(self.main.sector_groups.keys())
        self.SectorGroupComboBox.SelectedItem = None
        self.SectorGroupComboBox.SelectionChanged += self.update_view_name_template_example
        self.SectorGroupComboBox.SelectionChanged += self.update_sheet_number_template_example
        self.SectorGroupComboBox.SelectionChanged += self.update_sheet_name_template_example

        self.ViewFamilyComboBox.ItemsSource = sorted(list(filter( lambda x: 'Plan' in x, self.main.view_family_types.keys() )))
        self.ViewFamilyComboBox.SelectionChanged += self.update_view_family_types_list
        self.ViewFamilyComboBox.SelectionChanged += self.update_view_name_template_example
        self.ViewFamilyComboBox.SelectionChanged += self.update_sheet_number_template_example
        self.ViewFamilyComboBox.SelectionChanged += self.update_sheet_name_template_example

        self.ViewTypeComboBox.SelectionChanged += self.update_view_name_template_example
        self.ViewTypeComboBox.SelectionChanged += self.update_sheet_number_template_example
        self.ViewTypeComboBox.SelectionChanged += self.update_sheet_name_template_example
        
        self.ViewNameTemplateTextBox.TextChanged += self.update_view_name_template_example
        self.ViewNameTemplateResetButton.Click += self.reset_view_name_template_str

        self.SheetNumberTemplateTextBox.TextChanged += self.update_sheet_number_template_example
        self.SheetNumberTemplateResetButton.Click += self.reset_sheet_number_template_str

        self.SheetNameTemplateTextBox.TextChanged += self.update_sheet_name_template_example
        self.SheetNameTemplateResetButton.Click += self.reset_sheet_name_template_str

        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.CancelButton.Click += self.cancel_clicked

        return None







    
    def update_view_family_types_list(self, sender, args):
        view_family = self.ViewFamilyComboBox.SelectedItem
        if view_family in self.main.view_family_types:
            self.ViewTypeComboBox.ItemsSource = sorted(self.main.view_family_types[view_family].keys())


    def update_example_text(self, template_text_box, example_text_block):
        levels = self.get_levels()
        if not levels:
            level_name = 'LEVEL NAME'
        else:
            level_name = levels[0].Name

        scope_boxes = self.get_sector_scope_boxes()
        if not scope_boxes:
            scope_box_name = 'SCOPE BOX NAME'
        else:
            scope_box_name = scope_boxes[0].Name
        
        template_str = template_text_box.Text.strip()

        context = {
            'sheet_group_name': self.get_name(),
            'level_name': level_name,
            'level_counter': '1',
            'scope_box_name': scope_box_name,
            'scope_box_counter': '1',
            'sheet_counter': '1',
            'view_family_name': self.get_view_family_name(),
            'view_type_name': self.get_view_type_name(),
            }

        try:
            example_text = safe_eval(template_str, context)
        except Exception as e:
            example_text = '{}'.format(e)

        example_text_block.Text = example_text
    

    def update_view_name_template_example(self, sender, args):
        self.update_example_text(self.ViewNameTemplateTextBox, self.ViewNameTemplateExampleTextBlock)


    def update_sheet_number_template_example(self, sender, args):
        self.update_example_text(self.SheetNumberTemplateTextBox, self.SheetNumberTemplateExampleTextBlock)


    def update_sheet_name_template_example(self, sender, args):
        self.update_example_text(self.SheetNameTemplateTextBox, self.SheetNameTemplateExampleTextBlock)


    def reset_view_name_template_str(self, sender, args):
        self.ViewNameTemplateTextBox.Text = self.default_view_name_template_str
        self.update_view_name_template_example(sender, args)


    def reset_sheet_number_template_str(self, sender, args):
        self.SheetNumberTemplateTextBox.Text = self.default_sheet_number_template_str
        self.update_sheet_number_template_example(sender, args)


    def reset_sheet_name_template_str(self, sender, args):
        self.SheetNameTemplateTextBox.Text = self.default_sheet_name_template_str
        self.update_sheet_name_template_example(sender, args)








    def get_name(self):
        try:
            name = self.NameTextBox.Text.strip()
        except:
            name = ""

        return name


    def get_sector_group_name(self):
        try:
            sector_group_name = self.SectorGroupComboBox.SelectedItem
        except:
            sector_group_name = ""

        return sector_group_name
    
    
    def get_view_family_name(self):
        try:
            view_family_name = self.ViewFamilyComboBox.SelectedItem
        except:
            view_family_name = ""

        return view_family_name
    

    def get_view_type_name(self):
        try:
            view_type_name = self.ViewTypeComboBox.SelectedItem
        except:
            view_type_name = ""
        
        return view_type_name
    

    def get_view_family_type(self):
        try:
            view_family_name = self.get_view_family_name()
            view_type_name = self.get_view_type_name()
            view_family_type = self.main.view_family_types[view_family_name][view_type_name]
        except:
            view_family_type = None

        return view_family_type


    def get_levels(self):
        try:
            sector_group_name = self.get_sector_group_name()
            sg_data = self.main.sector_groups[sector_group_name]
            levels = [ self.main.get_element(level_id) for level_id in sg_data['level_ids'] ]
        except:
            levels = []

        return levels
    

    def get_sector_scope_boxes(self):
        try:
            sector_group_name = self.get_sector_group_name()
            sg_data = self.main.sector_groups[sector_group_name]
            sector_scope_boxes = [ self.main.get_element(sector_scope_box_id) for sector_scope_box_id in sg_data['sector_scope_box_ids'] ]
        except:
            sector_scope_boxes = []

        return sector_scope_boxes


    def get_view_name_template_str(self):
        try:
            view_name_template_str = self.ViewNameTemplateTextBox.Text.strip()
        except:
            view_name_template_str = ""

        return view_name_template_str
    

    def get_sheet_number_template_str(self):
        try:
            sheet_number_template_str = self.SheetNumberTemplateTextBox.Text.strip()
        except:
            sheet_number_template_str = ""

        return sheet_number_template_str
    

    def get_sheet_name_template_str(self):
        try:
            sheet_name_template_str = self.SheetNameTemplateTextBox.Text.strip()
        except:
            sheet_name_template_str = ""

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