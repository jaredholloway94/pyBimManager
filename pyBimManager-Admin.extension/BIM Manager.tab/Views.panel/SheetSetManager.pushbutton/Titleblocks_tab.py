from pyrevit import revit, forms
from Autodesk.Revit.DB import ViewSheet


class TitleBlocksTab(object):
    '''
    Class to manage the Title Blocks tab of the Sheet Set Manager window.
    '''

    def __init__(self, main_window):
        '''
        Initialize the Title Blocks tab.
        '''
        # Register parent window and schema
        self.main = main_window
        self.schema = self.main.get_schema('TitleBlocks')

        # Register UI Event Handlers
        self.main.Configure.Click += self.configure_title_block
        self.main.ConfiguredTitleBlocksListBox.SelectionChanged += self.display_title_block_details

        # Initialize lists
        self.update_title_block_lists()

        return None


    def get_title_block_entity(self, title_block):
        '''
        Get the TitleBlock schema Entity for the given Element.
        '''
        return self.main.get_entity(schema=self.schema, element=title_block)
    

    def get_title_block_data(self, title_block):
        '''
        Get the TitleBlock schema Data from the given Element.
        '''
        entity = self.get_title_block_entity(title_block)
        
        if entity and entity.IsValid():
            return self.main.get_data(entity)
        else:
            return None
        

    def set_title_block_data(self, title_block, data):
        self.main.set_data(schema=self.schema, element=title_block, data=data)
        
        return None
    

    def get_title_block_display_name(self, tb):
        display_name = '{} : {}'.format(
            tb.FamilyName,
            tb.LookupParameter('Type Name').AsString()
            )

        return display_name


    def update_title_block_lists(self):
        '''
        Refresh the lists of 'Configured' and 'Not Configured' Title Blocks.
        '''
        self.main.configured_title_blocks = []
        self.main.not_configured_title_blocks = []

        # Sort Title Blocks into 'Configured' and 'Not Configured' lists
        # by checking if they have an entity in the Extensible Storage
        for tb in self.main.title_blocks:
            if self.get_entity(tb):
                self.main.configured_title_blocks.append(tb)
            else:
                self.main.not_configured_title_blocks.append(tb)

        # Populate the UI lists
        if len(self.main.configured_title_blocks) == 0:
            self.main.ConfiguredTitleBlocksListBox.ItemsSource = []
        else:
            self.main.ConfiguredTitleBlocksListBox.ItemsSource = [self.get_title_block_display_name(tb) for tb in self.main.configured_title_blocks]

        if len(self.main.not_configured_title_blocks) == 0:
            self.main.NotConfiguredTitleBlocksListBox.ItemsSource = []
        else:
            self.main.NotConfiguredTitleBlocksListBox.ItemsSource = [self.get_title_block_display_name(tb) for tb in self.main.not_configured_title_blocks]

        return


    def update_title_block_details(self):
        '''
        In the Details pane, display the configuration details of the Title Block that's selected in the 'Configured' list.
        '''
        # Get the selected Title Block from the UI
        i = self.main.ConfiguredTitleBlocksListBox.SelectedIndex

        # If no Title Block is selected, clear the details
        if i < 0:
            width = height = center_x = center_y = ''

        # Otherwise, get the details from the selected Title Block's entity
        else:
            tb = self.main.configured_title_blocks[i]
            data = self.get_title_block_data(tb)

            width = data['drawing_area_width']
            height = data['drawing_area_height']
            center_x = data['drawing_area_center_x']
            center_y = data['drawing_area_center_y']

        # Set the details in the UI
        self.main.TitleBlockDetails_Width.Text = width
        self.main.TitleBlockDetails_Height.Text = height
        self.main.TitleBlockDetails_CenterX.Text = center_x
        self.main.TitleBlockDetails_CenterY.Text = center_y

        return None


    def configure_title_block(self, sender, args):
        '''
        Configure the Title Block selected in the 'Not Configured' list.
        '''
        # Get the selected Title Block from the UI
        i = self.main.NotConfiguredTitleBlocksListBox.SelectedIndex
        
        if i < 0:
            forms.alert("Please select a Title Block to configure.")
            return
        else:
            tb = self.main.not_configured_title_blocks[i]

        # Close the main window so we can prompt the user
        self.main.Close()

        # Prompt the user to select the corners of the drawing area;
        # calculate the width/height/center;
        # store the values in Extensible Storage;
        self._configure_title_block_workflow(tb)
        
        # Respawn the main window
        new_main_window = self.main.__class__('SheetSetManager_window.xaml')
        new_main_window.show_dialog()

        return None


    def _configure_title_block_workflow(self, title_block):
        '''
        Workflow to configure the Title Block.
        '''
        # Create a temporary sheet to get the drawing area dimensions
        with revit.Transaction("Create Temp Sheet"):
            temp_sheet = ViewSheet.Create(self.main.doc, title_block.Id)
            temp_sheet.SheetNumber = "temp"
            temp_sheet.Name = "temp"
        
        # Store the current view for later
        old_view = self.main.uidoc.ActiveView

        # Set the new sheet as the active view
        self.main.uidoc.ActiveView = temp_sheet

        # Prompt the user to select the drawing area dimensions
        forms.alert("Select the bottom-left corner of the drawing area.")
        bottom_left_corner = self.main.uidoc.Selection.PickPoint("Select the bottom-left corner of the drawing area")

        forms.alert("Select the top-right corner of the drawing area.")
        top_right_corner = self.main.uidoc.Selection.PickPoint("Select the top-right corner of the drawing area")

        # Return to the original view
        self.main.uidoc.ActiveView = old_view

        # Delete the temporary sheet
        if temp_sheet and temp_sheet.Id and temp_sheet.Id.IntegerValue > 0:
            with revit.Transaction("Delete Temp Sheet"):
                self.main.doc.Delete(temp_sheet.Id)


        data = {}

        # Calculate the width, height, and center of the drawing area
        data['width'] = abs(top_right_corner.X - bottom_left_corner.X)
        data['height'] = abs(top_right_corner.Y - bottom_left_corner.Y)
        data['center_x'] = ((bottom_left_corner.X + top_right_corner.X) / 2.0)
        data['center_y'] = ((bottom_left_corner.Y + top_right_corner.Y) / 2.0)

        
        # Store the title_block configuration in the Extensible Storage
        self.set_title_block_data(title_block, data)

        return None