from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ
from math import ceil

class EditSectorGroupWindow(forms.WPFWindow):


    #### Init ####


    def __init__(self, xaml_file, parent):

        # Initialize the window
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main

        # Initialize UI fields with Sector Group data
        self.name = self.main.SectorGroupsListBox.SelectedItem
        self.data = self.main.sector_groups[self.name]

        self.title_block = self.main.get_element(self.data['title_block_id'])
        self.overall_scope_box = self.main.get_element(self.data['overall_scope_box_id'])
        self.overall_view_scale = self.data['overall_view_scale']
        self.sector_scope_boxes = [ self.main.get_element(id) for id in self.data['sector_scope_box_ids'] ]
        self.sector_view_scale = self.data['sector_view_scale']
        self.levels = [ self.main.get_element(id) for id in self.data['level_ids'] ]
        if self.data['reference_plane_ids']:
            self.reference_planes = [ self.main.get_element(id) for id in self.data['reference_plane_ids'] ]
        else:
            self.reference_planes = []


        #   Name
        self.NameTextBox.Text = self.name
        self.NameTextBox.IsEnabled = False

        #   Title Block
        self.TitleBlockComboBox.ItemsSource = sorted(self.main.configured_title_blocks.keys())
        self.TitleBlockComboBox.SelectedItem = self.main.display_name(self.title_block)

        #   Overall Scope Box
        self.OverallScopeBoxComboBox.ItemsSource = sorted(self.main.scope_boxes.keys())
        self.OverallScopeBoxComboBox.SelectedItem = self.overall_scope_box.Name
        self.OverallScopeBoxComboBox.SelectionChanged += self.update_sector_scope_boxes_list

        #   Overall View Scale
        self.OverallViewScaleTextBox.Text = str(self.overall_view_scale)

        #   Sector Scope Boxes
        self.SectorScopeBoxesListBox.ItemsSource = sorted([ sb_name for sb_name in self.main.scope_boxes.keys() if sb_name != self.overall_scope_box.Name ])
        # for i, sb_name in enumerate(self.SectorScopeBoxesListBox.Items):
        #     if sb_name in [ sb.Name for sb in self.sector_scope_boxes ]:
                # self.SectorScopeBoxesListBox.SetSelected(i, True)

        #   Sector View Scale
        self.SectorViewScaleTextBox.Text = str(self.sector_view_scale)

        #   Levels
        self.LevelsListBox.ItemsSource = sorted(self.main.levels.keys())
        # for i, level_name in enumerate(self.LevelsListBox.Items):
        #     if level_name in [ level.Name for level in self.levels ]:
        #         self.LevelsListBox.SetSelected(i, True)


        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.CancelButton.Click += self.cancel_clicked

        return
    

    #### Input Validation ####


    def get_name(self):
        name = self.NameTextBox.Text.strip()

        return name


    def get_title_block(self):
        tb_name = self.TitleBlockComboBox.SelectedItem

        if not tb_name:
            forms.alert('Please select a Title Block.')
            return None

        title_block = self.main.configured_title_blocks.get(tb_name)

        if not title_block:
            forms.alert('Selected Title Block is not valid.')
            return None

        return title_block


    def get_overall_scope_box(self):
        overall_scope_box_name = self.OverallScopeBoxComboBox.SelectedItem

        if not overall_scope_box_name:
            forms.alert('Please select an Overall Scope Box.')
            return None

        overall_scope_box = self.main.scope_boxes.get(overall_scope_box_name)

        if not overall_scope_box:
            forms.alert('Selected Scope Box is not valid.')
            return None

        return overall_scope_box


    def get_overall_view_scale(self):
        overall_view_scale = int(self.OverallViewScaleTextBox.Text)

        if overall_view_scale <= 0:
            forms.alert('View Scale must be a positive integer.')
            return None

        return overall_view_scale
    

    def get_sector_scope_boxes(self):
        scope_box_names = self.SectorScopeBoxesListBox.SelectedItems
        
        if not scope_box_names:
            return []

        sector_scope_boxes = [self.main.scope_boxes[name] for name in scope_box_names]

        return sector_scope_boxes



    def get_sector_view_scale(self):
        sector_view_scale = int(self.SectorViewScaleTextBox.Text)

        if sector_view_scale <= 0:
            forms.alert('View Scale must be a positive integer.')
            return None

        return sector_view_scale


    def get_levels(self):
        level_names = self.LevelsListBox.SelectedItems

        if not level_names:
            return []

        levels = [self.main.levels[name] for name in level_names]

        return levels


    def get_create_ref_planes(self):
        return self.CreateRefPlanesCheckBox.IsChecked


    #### UI Event Handlers ####


    def update_sector_scope_boxes_list(self, sender, args):
        overall_scope_box = self.get_overall_scope_box()
        if overall_scope_box:
            self.SectorScopeBoxesListBox.ItemsSource = sorted(
                [sb_name for sb_name in self.main.scope_boxes.keys() if sb_name != overall_scope_box.Name]
            )
        else:
            self.SectorScopeBoxesListBox.ItemsSource = []

    def ok_clicked(self, sender, args):

        # Get and validate inputs from the UI
        name = self.get_name()
        title_block = self.get_title_block()
        overall_scope_box = self.get_overall_scope_box()
        overall_view_scale = self.get_overall_view_scale()
        sector_scope_boxes = self.get_sector_scope_boxes()
        sector_view_scale = self.get_sector_view_scale()
        levels = self.get_levels()
        create_ref_planes = self.get_create_ref_planes()

        # If user checked 'Create Reference Planes', create the reference planes
        # Otherwise, store an empty list
        reference_planes = self.reference_planes
        if create_ref_planes:
            reference_planes = []
            # Do geometry calculations
            tb_data = self.main.title_blocks_tab.get_data(title_block)
            paper_space_vp_width = tb_data['width']
            paper_space_vp_height = tb_data['height']
            overall_bb = overall_scope_box.get_BoundingBox(None)
            model_space_vp_width = paper_space_vp_width * sector_view_scale
            model_space_vp_height = paper_space_vp_height * sector_view_scale
            overall_min_pt = overall_bb.Min
            overall_max_pt = overall_bb.Max
            overall_x = overall_min_pt.X
            overall_y = overall_min_pt.Y
            overall_z = overall_min_pt.Z
            overall_width = overall_max_pt.X - overall_min_pt.X
            overall_height = overall_max_pt.Y - overall_min_pt.Y
            n_cols = int(ceil(overall_width / model_space_vp_width))
            n_rows = int(ceil(overall_height / model_space_vp_height))
            
            # Wrap document modifications in a transaction
            with revit.Transaction('Sheet Set Manager - Draw Sector Group Ref Planes'):

                # Create the N-S reference planes
                for col in range(n_cols + 1):
                    x = overall_x + col * model_space_vp_width
                    p0 = XYZ(x, overall_y, overall_z)
                    p1 = XYZ(x, overall_y + (n_rows * model_space_vp_height), overall_z)
                    col_name = '{}-Col{}'.format(name, col + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = col_name
                    # Add the reference plane to the list
                    reference_planes.append(ref_plane)

                # Create the E-W reference planes
                for row in range(n_rows + 1):
                    y = overall_y + row * model_space_vp_height
                    p0 = XYZ(overall_x, y, overall_z)
                    p1 = XYZ(overall_x + (n_cols * model_space_vp_width), y, overall_z)
                    row_name = '{}-Row{}'.format(name, row + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = row_name
                    # Add the reference plane to the list
                    reference_planes.append(ref_plane)
                    
        # Cache Sector Group data in main window object. It will be committed to storage from there.
        self.main.sector_groups[name] = {
            'name': name,
            'title_block_id': title_block.Id.IntegerValue,
            'overall_scope_box_id': overall_scope_box.Id.IntegerValue,
            'overall_view_scale': overall_view_scale,
            'sector_scope_box_ids': [ sb.Id.IntegerValue for sb in sector_scope_boxes ],
            'sector_view_scale': sector_view_scale,
            'level_ids': [ level.Id.IntegerValue for level in levels ],
            'reference_plane_ids': [ rp.Id.IntegerValue for rp in reference_planes ],
            }
        
        self.DialogResult = True
        self.Close()


    def cancel_clicked(self, sender, args):
        self.DialogResult = False
        self.Close()
