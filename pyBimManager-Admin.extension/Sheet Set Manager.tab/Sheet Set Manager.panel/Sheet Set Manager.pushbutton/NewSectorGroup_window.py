from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ
from math import ceil

import clr
clr.AddReference('System.Drawing')
from System.Drawing import Color

class NewSectorGroupWindow(forms.WPFWindow):


    #### Init ####


    def __init__(self, xaml_file, parent):

        # Initialize the window
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main

        # Initialize lists
        self.TitleBlockComboBox.ItemsSource = sorted(self.main.configured_title_blocks.keys())
        self.TitleBlockComboBox.SelectionChanged += self.update_overall_view_scale

        self.OverallScopeBoxComboBox.ItemsSource = sorted(self.main.scope_boxes.keys())
        self.OverallScopeBoxComboBox.SelectionChanged += self.update_overall_view_scale
        self.OverallScopeBoxComboBox.SelectionChanged += self.update_sector_scope_boxes_list

        self.OverallViewScaleComboBox.ItemsSource = self.main.view_scales_list
        self.OverallViewScaleComboBox.IsEnabled = False
        
        self.OverallViewScaleTextBox.IsEnabled = False

        self.SectorScopeBoxesListBox.ItemsSource = []

        self.SectorViewScaleComboBox.ItemsSource = self.main.view_scales_list
        self.SectorViewScaleComboBox.SelectedItem = None

        self.SectorViewScaleTextBox.IsEnabled = False
        self.SectorViewScaleComboBox.SelectionChanged += self.update_sector_view_scale_textbox

        self.LevelsListBox.ItemsSource = sorted(self.main.levels.keys())

        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.CancelButton.Click += self.cancel_clicked

        return


    #### Input Validation ####


    def get_name(self):
        name = self.NameTextBox.Text.strip()

        if name in self.main.sector_groups:
            forms.alert('A sector group with this name already exists.')
            return None

        return name


    def get_title_block(self):
        tb_name = self.TitleBlockComboBox.SelectedItem
        title_block = self.main.configured_title_blocks.get(tb_name)

        return title_block


    def get_overall_scope_box(self):
        overall_scope_box_name = self.OverallScopeBoxComboBox.SelectedItem
        overall_scope_box = self.main.scope_boxes.get(overall_scope_box_name)

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

        if not 0 < sector_view_scale < 24000:
            forms.alert('View Scale must be an integer between 1 and 24000.')
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


    def update_overall_view_scale(self, sender, args):
        overall_scope_box = self.get_overall_scope_box()
        title_block = self.get_title_block()

        if overall_scope_box and title_block:
            tb_data = self.main.title_blocks_tab.get_data(title_block)
            paper_space_vp_width = tb_data['width'] - (tb_data['margin'] * 2)
            paper_space_vp_height = tb_data['height'] - (tb_data['margin'] * 2)
            overall_bb = overall_scope_box.get_BoundingBox(None)
            overall_width = overall_bb.Max.X - overall_bb.Min.X
            overall_height = overall_bb.Max.Y - overall_bb.Min.Y

            # Calculate the view scale
            view_scale_calc = min(paper_space_vp_width / overall_width, paper_space_vp_height / overall_height)

            for vs_name in self.main.view_scales_list:
                vs_val = self.main.view_scales[vs_name]
                if 1/vs_val < view_scale_calc:
                    view_scale = vs_val
                    self.OverallViewScaleComboBox.SelectedItem = vs_name
                    self.OverallViewScaleTextBox.Text = str(view_scale)
                    break


    def update_sector_scope_boxes_list(self, sender, args):
        overall_scope_box = self.get_overall_scope_box()
        if overall_scope_box:
            self.SectorScopeBoxesListBox.ItemsSource = sorted(
                [sb_name for sb_name in self.main.scope_boxes.keys() if sb_name != overall_scope_box.Name]
            )
        else:
            self.SectorScopeBoxesListBox.ItemsSource = []


    def update_sector_view_scale_textbox(self, sender, args):
        vs_name = self.SectorViewScaleComboBox.SelectedItem
        if vs_name == 'Custom':
            self.SectorViewScaleTextBox.IsEnabled = True
            self.SectorViewScaleTextBox.Text = None
        else:
            self.SectorViewScaleTextBox.IsEnabled = False
            self.SectorViewScaleTextBox.Text = str(self.main.view_scales[vs_name])


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
        reference_planes = []
        if create_ref_planes:

            # Do geometry calculations
            tb_data = self.main.title_blocks_tab.get_data(title_block)
            paper_space_vp_width = tb_data['width'] - (tb_data['margin'] * 2)
            paper_space_vp_height = tb_data['height'] - (tb_data['margin'] * 2)
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
            'sector_scope_box_ids': [sb.Id.IntegerValue for sb in sector_scope_boxes],
            'sector_view_scale': sector_view_scale,
            'level_ids': [level.Id.IntegerValue for level in levels],
            'reference_plane_ids': [rp.Id.IntegerValue for rp in reference_planes],
            }
        
        self.DialogResult = True
        self.Close()


    def cancel_clicked(self, sender, args):
        self.DialogResult = False
        self.Close()
