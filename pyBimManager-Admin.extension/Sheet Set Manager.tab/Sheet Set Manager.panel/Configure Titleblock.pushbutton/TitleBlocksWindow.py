from pyrevit import revit, forms
from Autodesk.Revit.DB import ViewSheet


class TitleBlocksWindow(forms.WPFWindow):
    '''
    Class to manage the Title Blocks tab of the Sheet Set Manager window.
    '''

    def __init__(self, xml_path, main):
        '''
        Initialize the Title Blocks tab.
        '''
        super().__init__(xml_path)
        self.xml_path = xml_path
        # Register parent window and schema
        self.main = main
        self.schema = self.main.get_schema('TitleBlocks')

        # Register UI Event Handlers
        self.Configure.Click += self.configure_title_block
        self.ConfiguredTitleBlocksListBox.SelectionChanged += self.update_details

        # Initialize lists
        self.update_lists()

        return None


    def get_entity(self, title_block, create=False):
        entity = self.main.get_entity(
            schema=self.schema,
            element=title_block,
            create=create
            )

        return entity
    

    def get_data(self, title_block):
        entity = self.get_entity(title_block)
        data = self.main.get_data(entity=entity)
        
        return data


    def set_data(self, title_block, data):
        self.main.set_data(
            schema=self.schema,
            element=title_block,
            data=data
            )
        
        return None


    def update_lists(self):
        '''
        Refresh the lists of 'Configured' and 'Not Configured' Title Blocks.
        '''
        self.main.configured_title_blocks = {} # 'Name': Element
        self.main.not_configured_title_blocks = {} # 'Name': Element

        # Sort Title Blocks into 'Configured' and 'Not Configured' lists
        # by checking if they have an entity in the Extensible Storage
        for tb_name, tb in self.main.title_blocks.items():
            if self.get_entity(tb):
                self.main.configured_title_blocks[tb_name] = tb
            else:
                self.main.not_configured_title_blocks[tb_name] = tb

        # Populate the UI lists
        if len(self.main.configured_title_blocks) == 0:
            self.ConfiguredTitleBlocksListBox.ItemsSource = []
        else:
            self.ConfiguredTitleBlocksListBox.ItemsSource = \
                sorted(self.main.configured_title_blocks.keys())

        if len(self.main.not_configured_title_blocks) == 0:
            self.NotConfiguredTitleBlocksListBox.ItemsSource = []
        else:
            self.NotConfiguredTitleBlocksListBox.ItemsSource = \
                sorted(self.main.not_configured_title_blocks.keys())

        return


    def update_details(self, sender, args):
        '''
        In the Details pane, display the configuration details of the Title Block that's selected in the 'Configured' list.
        '''
        # Get the selected Title Block from the UI
        tb_name = self.ConfiguredTitleBlocksListBox.SelectedItem

        # If no Title Block is selected, clear the details
        if not tb_name:
            width = height = center_x = center_y = ''

        # Otherwise, get the details from the selected Title Block's entity
        else:
            tb = self.main.configured_title_blocks[tb_name]
            data = self.get_data(tb)

            width = '{}"'.format(round(data['width']*12, 2))
            height = '{}"'.format(round(data['height']*12, 2))
            center_x = '{}"'.format(round(data['center_x']*12, 2))
            center_y = '{}"'.format(round(data['center_y']*12, 2))

        # Set the details in the UI
        self.TitleBlockDetails_Width.Text = width
        self.TitleBlockDetails_Height.Text = height
        self.TitleBlockDetails_CenterX.Text = center_x
        self.TitleBlockDetails_CenterY.Text = center_y

        return None


    def configure_title_block(self, sender, args):
        '''
        Configure the Title Block that's selected in the 'Not Configured' list.
        '''
        # Get the selected Title Block from the UI
        tb_name = self.NotConfiguredTitleBlocksListBox.SelectedItem

        if not tb_name:
            forms.alert("Please select a Title Block to configure.")
            return
        else:
            tb = self.main.not_configured_title_blocks[tb_name]


        self.DialogResult = True
        self.Close()
        # Prompt the user to select the corners of the drawing area;
        # calculate the width/height/center;
        # store the values in Extensible Storage;
        self._configure_title_block_workflow(tb)
        self.__class__(self.xml_path, self.main).show_dialog()

        return None


    def _configure_title_block_workflow(self, title_block):
        '''
        Workflow to configure the Title Block.
        '''
        # Create a temporary sheet to get the drawing area dimensions
        with revit.Transaction("Sheet Set Manager - Create Temp Sheet"):
            temp_sheet = ViewSheet.Create(self.main.doc, title_block.Id)
            temp_sheet.SheetNumber = "temp"
            temp_sheet.Name = "temp"
        
        # Store the current view for later
        old_view = self.main.uidoc.ActiveView

        # Set the new sheet as the active view
        self.main.uidoc.ActiveView = temp_sheet

        # Prompt the user to select the drawing area dimensions
        forms.alert("Select the bottom-left corner of the drawing area.")

        bottom_left_corner = self.main.uidoc.Selection.PickPoint(
            "Select the bottom-left corner of the drawing area"
            )

        forms.alert("Select the top-right corner of the drawing area.")

        top_right_corner = self.main.uidoc.Selection.PickPoint(
            "Select the top-right corner of the drawing area"
            )

        # Return to the original view
        self.main.uidoc.ActiveView = old_view

        # Delete the temporary sheet
        if temp_sheet and temp_sheet.Id and temp_sheet.Id.IntegerValue > 0:
            with revit.Transaction("Sheet Set Manager - Delete Temp Sheet"):
                self.main.doc.Delete(temp_sheet.Id)

        data = {}

        # Calculate the width, height, and center of the drawing area
        data['width'] = abs(top_right_corner.X - bottom_left_corner.X)
        data['height'] = abs(top_right_corner.Y - bottom_left_corner.Y)
        data['center_x'] = ((bottom_left_corner.X + top_right_corner.X) / 2.0)
        data['center_y'] = ((bottom_left_corner.Y + top_right_corner.Y) / 2.0)

        
        # Store the title_block configuration in the Extensible Storage
        self.set_data(title_block, data)
        # don't need to update the lists here, bc it will happen when the main window is respawned

        return None