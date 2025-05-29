from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ
from math import ceil

class NewSectorGroupWindow(forms.WPFWindow):

    def __init__(self, xaml_file, parent):

        # Initialize the window
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main

        # Initialize lists
        self.TitleBlockComboBox.ItemsSource = sorted(self.main.configured_title_blocks.keys())
        self.ScopeBoxComboBox.ItemsSource = sorted(self.main.scope_boxes.keys())

        # Register UI Event Handlers
        self.OkButton.Click += self.ok_clicked
        self.CancelButton.Click += self.cancel_clicked

        return


    def get_valid_name(self):
        name = self.NameTextBox.Text.strip()

        if name in self.main.sector_groups:
            forms.alert('A sector group with this name already exists.')
            return None

        return name


    def ok_clicked(self, sender, args):

        # Get and validate inputs from the UI
        name = self.get_valid_name()
        tb_name = self.TitleBlockComboBox.SelectedItem
        title_block = self.main.configured_title_blocks[tb_name]
        sb_name = self.ScopeBoxComboBox.SelectedItem
        overall_scope_box = self.main.scope_boxes[sb_name]
        view_scale = int(self.ViewScaleTextBox.Text)

        # If user checked 'Create Reference Planes', create the reference planes
        # Otherwise, store an empty list
        reference_planes = []
        if self.CreateRefPlanesCheckBox.IsChecked:

            # Do geometry calculations
            tb_data = self.main.title_blocks_tab.get_data(title_block)
            paper_space_vp_width = tb_data['width']
            paper_space_vp_height = tb_data['height']
            overall_bb = overall_scope_box.get_BoundingBox(None)
            model_space_vp_width = paper_space_vp_width * view_scale
            model_space_vp_height = paper_space_vp_height * view_scale
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
                    p1 = XYZ(x, overall_y + overall_height, overall_z)
                    col_name = '{}-Col{}'.format(name, col + 1)
                    ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
                    ref_plane.Name = col_name
                    # Add the reference plane to the list
                    reference_planes.append(ref_plane)

                # Create the E-W reference planes
                for row in range(n_rows + 1):
                    y = overall_y + row * model_space_vp_height
                    p0 = XYZ(overall_x, y, overall_z)
                    p1 = XYZ(overall_x + overall_width, y, overall_z)
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
            'view_scale': view_scale,
            'reference_plane_ids': [rp.Id.IntegerValue for rp in reference_planes],
            'sector_scope_box_ids': []
            }
        
        self.DialogResult = True
        self.Close()


    def cancel_clicked(self, sender, args):
        self.DialogResult = False
        self.Close()
