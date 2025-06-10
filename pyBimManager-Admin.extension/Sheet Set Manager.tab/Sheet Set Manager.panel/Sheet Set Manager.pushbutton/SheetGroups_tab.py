from pyrevit import revit, forms
from Autodesk.Revit.DB import ElementId, ViewPlan, ViewSheet, Viewport, XYZ
from NewSheetGroup_window import NewSheetGroupWindow
from datetime import datetime
from safe_eval import safe_eval


class SheetGroupsTab(object):

    def __init__(self, main_window):

        # Register parent window and schema
        self.main = main_window
        self.schema = self.main.get_schema('SheetGroups')

        # Register UI Event Handlers
        self.main.NewSheetGroup.Click += self.new_sheet_group
        self.main.RenameSheetGroup.Click += self.rename_sheet_group
        self.main.EditSheetGroup.Click += self.edit_sheet_group
        self.main.DeleteSheetGroup.Click += self.delete_sheet_group
        self.main.CreateViewsSheets.Click += self.create_views_sheets

        self.main.SheetGroupsListBox.SelectionChanged += self.update_details

        # Initialize lists
        self.update_lists()

        self.ui_fields = {

            self.main.SheetGroupDetails_SectorGroup:
                lambda sheet_group_data: str(
                    sheet_group_data['sector_group_name']
                    ),

            self.main.SheetGroupDetails_TitleBlockFamily:
                lambda sheet_group_data: str(
                    self.main.get_element(
                        self.main.sector_groups[sheet_group_data['sector_group_name']]['title_block_id']
                        ).FamilyName
                    ),

            self.main.SheetGroupDetails_TitleBlockType:
                lambda sheet_group_data: str(
                    self.main.get_element(
                        self.main.sector_groups[sheet_group_data['sector_group_name']]['title_block_id']
                        ).LookupParameter('Type Name').AsString()
                    ),

            self.main.SheetGroupDetails_OverallScopeBox:
                lambda sheet_group_data: str(
                    self.main.get_element(
                        self.main.sector_groups[sheet_group_data['sector_group_name']]['overall_scope_box_id']
                    ).Name
                ),

            self.main.SheetGroupDetails_OverallViewScale:
                lambda sheet_group_data: str(
                    self.main.sector_groups[sheet_group_data['sector_group_name']]['overall_view_scale']
                    ),

            self.main.SheetGroupDetails_SectorScopeBoxes:
                lambda sheet_group_data: str(
                    ', '.join([
                            self.main.get_element(sb_id).Name
                            for sb_id in self.main.sector_groups[sheet_group_data['sector_group_name']]['sector_scope_box_ids']
                        ])
                    ),

            self.main.SheetGroupDetails_SectorViewScale:
                lambda sheet_group_data: str(
                    self.main.sector_groups[sheet_group_data['sector_group_name']]['sector_view_scale']
                    ),

            self.main.SheetGroupDetails_Levels:
                lambda sheet_group_data: str(
                    ', '.join([
                            self.main.get_element(lvl_id).Name
                            for lvl_id in self.main.sector_groups[sheet_group_data['sector_group_name']]['level_ids']
                        ])
                    ),

            self.main.SheetGroupDetails_ViewFamily:
                lambda sheet_group_data: str(
                    self.main.get_element(sheet_group_data['view_type_id']).ViewFamily
                    ),

            self.main.SheetGroupDetails_ViewType:
                lambda sheet_group_data: str(
                    self.main.get_element(sheet_group_data['view_type_id']).Name
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
            try:
                field.Text = value(sg_data)
            except:
                field.Text = 'Error!'
            
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

        self.main.SheetGroupsListBox.SelectedItem = None
        self.update_lists()
        self.update_details(sender, args)






    def create_views_sheets(self, sender, args):
        
        # Get data
        name = self.main.SheetGroupsListBox.SelectedItem
        data = self.main.sheet_groups[name]

        sector_group_name = data['sector_group_name']
        sector_group_data = self.main.sector_groups[sector_group_name]

        overall_scope_box = self.main.get_element(sector_group_data['overall_scope_box_id'])
        overall_view_scale = sector_group_data['overall_view_scale']

        sector_scope_boxes = [ self.main.get_element(sb_id) for sb_id in sector_group_data['sector_scope_box_ids'] ]
        sector_view_scale = sector_group_data['sector_view_scale']

        levels = [ self.main.get_element(lvl_id) for lvl_id in sector_group_data['level_ids'] ]

        title_block = self.main.get_element(sector_group_data['title_block_id'])
        tb_data = self.main.title_blocks_tab.get_data(title_block)
        tb_center = XYZ(tb_data['center_x'], tb_data['center_y'], 0)

        view_family_type = self.main.get_element(data['view_type_id'])
        view_name_template_str = data['view_name_template_str']
        sheet_number_template_str = data['sheet_number_template_str']
        sheet_name_template_str = data['sheet_name_template_str']
        

        # Create Views, Sheets, and Viewports
        with revit.Transaction('Sheet Set Manager - Create Views, Sheets, and Viewports'):

            created_views = []
            created_sheets = []

            for level_counter, level in enumerate(levels):
                for scope_box_counter, scope_box in enumerate(sector_scope_boxes):

                    sheet_counter = (len(sector_scope_boxes) * level_counter) + scope_box_counter + 1
                    total_sheets = (len(levels) * len(sector_scope_boxes))

                    context = {
                        'sheet_group_name': name,
                        'level_name': level.Name,
                        'level_counter': str(level_counter + 1),
                        'scope_box_name': scope_box.Name,
                        'scope_box_counter': str(scope_box_counter + 1),
                        'sheet_counter': str(sheet_counter),
                        'view_family_name': view_family_type.FamilyName,
                        'view_type_name': view_family_type.Name,
                        }

                    # Create View
                    new_view = ViewPlan.Create(self.main.doc, view_family_type.Id, level.Id)
                    new_view.Name = safe_eval(view_name_template_str, context)
                    new_view.LookupParameter('Scope Box').Set(scope_box.Id)
                    new_view.Scale = sector_view_scale
                    new_view.LookupParameter('Annotation Crop').Set(True)
                    new_view.CropBoxVisible = False
                    new_view.AreAnnotationCategoriesHidden = True
                    created_views.append(new_view)

                    print('Created View: {} [{}/{}]'.format(new_view.Name, sheet_counter, total_sheets))

                    # Create Sheet
                    new_sheet = ViewSheet.Create(self.main.doc, title_block.Id)
                    new_sheet.SheetNumber = safe_eval(sheet_number_template_str, context)
                    new_sheet.Name = safe_eval(sheet_name_template_str, context)
                    created_sheets.append(new_sheet)

                    print('Created Sheet: {} [{}/{}]'.format(new_sheet.Name, sheet_counter, total_sheets))
                    
                    # Create Viewport
                    new_viewport = Viewport.Create(self.main.doc, new_sheet.Id, new_view.Id, tb_center)

                    print('Created Viewport: {} [{}/{}]'.format(new_sheet.Name, sheet_counter, total_sheets))

        # Align Viewports to Title Blocks
        with revit.Transaction('Sheet Set Manager - Align Viewports to Title Blocks'):

            for k,sheet in enumerate(created_sheets):

                # Get the first viewport of the sheet
                vp = self.main.doc.GetElement(sheet.GetAllViewports()[0])
                # Get the View associated with the Viewport
                vp_view = self.main.doc.GetElement(vp.ViewId)
                # Set the Viewport box center to the Title Block center
                vp.SetBoxCenter(tb_center)
                # Restore annotation visibility
                vp_view.AreAnnotationCategoriesHidden = False

                print('Aligned Viewport to Title Block for Sheet: {} [{}/{}]'.format(sheet.Name, k+1, len(created_sheets)))

        # Set data
        self.main.sheet_groups[name]['view_ids'] = [ v.Id.IntegerValue for v in created_views ]
        self.main.sheet_groups[name]['sheet_ids'] = [ s.Id.IntegerValue for s in created_sheets ]

        self.set_data()
        self.update_lists()
        self.update_details(sender, args)
        forms.alert('Views, Sheets, and Viewports created successfully.')
