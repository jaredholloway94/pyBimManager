from pyrevit import revit, forms
from Autodesk.Revit.DB import XYZ, SubTransaction
from math import ceil

class NewSectorGroupWindow(forms.WPFWindow):

    def __init__(self, xaml_file, parent):
        super().__init__(xaml_file)
        self.parent = parent
        self.main = parent.main
        self.doc = self.main.doc
        self.uidoc = self.main.uidoc

        self.TitleBlockComboBox.ItemsSource = sorted(self.main.configured_title_blocks.keys())
        self.ScopeBoxComboBox.ItemsSource = sorted(self.main.scope_boxes.keys())


        self.OkButton.Click += self.ok
        self.CancelButton.Click += self.cancel

        return


    def get_name(self):
        name = self.NameTextBox.Text.strip()

        existing_sector_groups = self.main.sector_groups
        if any(sg['name'] == name for sg in existing_sector_groups):
            forms.alert('A sector group with this name already exists.')
            return None

        return name

    
    def get_title_block(self):
        tb_name = self.TitleBlockComboBox.SelectedItem
        tb = self.main.configured_title_blocks[tb_name]
        return tb


    def get_scope_box(self):
        sb_name = self.ScopeBoxComboBox.SelectedItem
        sb = self.main.scope_boxes[sb_name]

        return sb


    def get_view_scale(self):
        view_scale = int(self.ViewScaleTextBox.Text)

        return view_scale


    def process_inputs(self):

        name = self.get_name()

        tb = self.get_title_block()
        tb_data = self.main.title_blocks_tab.get_data(tb)
        paper_space_vp_width = tb_data['width']
        paper_space_vp_height = tb_data['height']

        sb = self.get_scope_box()
        overall_bb = sb.get_BoundingBox(None)

        view_scale = self.get_view_scale()

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

        # Create reference planes at the boundaries of the sectors
        new_reference_planes = []
        # with revit.Transaction('Sheet Set Manager - Draw Sector Grid Ref Planes'):

        st = SubTransaction(self.main.doc)
        st.Start()

        for col in range(n_cols + 1):
            x = overall_x + col * model_space_vp_width
            p0 = XYZ(x, overall_y, overall_z)
            p1 = XYZ(x, overall_y + overall_height, overall_z)
            col_name = '{}-Col{}'.format(name, col + 1)
            ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
            ref_plane.Name = col_name
            new_reference_planes.append(ref_plane.Id.IntegerValue)

        for row in range(n_rows + 1):
            y = overall_y + row * model_space_vp_height
            p0 = XYZ(overall_x, y, overall_z)
            p1 = XYZ(overall_x + overall_width, y, overall_z)
            row_name = '{}-Row{}'.format(name, row + 1)
            ref_plane = self.main.doc.Create.NewReferencePlane(p0, p1, XYZ(0, 0, 1), self.main.doc.ActiveView)
            ref_plane.Name = row_name
            new_reference_planes.append(ref_plane.Id.IntegerValue)

        st.Commit()

        # Collect the Sector Group data
        data = {
            'title_block_family': tb.FamilyName,
            'title_block_type': tb.LookupParameter('Type Name').AsString(),
            'title_block_id': tb.Id.IntegerValue,
            'scope_box': sb.Name,
            'scope_box_id': sb.Id.IntegerValue,
            'view_scale': view_scale,
            'reference_plane_ids': new_reference_planes
        }

        return name, data


    def ok(self, sender, args):
        name, data = self.process_inputs()
        self.parent.add_sector_group(name, data)
        self.Close()


    def cancel(self, sender, args):
        self.Close()

