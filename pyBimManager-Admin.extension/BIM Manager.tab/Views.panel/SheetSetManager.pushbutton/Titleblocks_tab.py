from pyrevit import revit, forms
from Autodesk.Revit.DB import ViewSheet
from Autodesk.Revit.DB.ExtensibleStorage import Entity


class TitleblocksTab(object):
    '''
    Class to manage the Titleblocks tab in the Sheet Set Manager.
    '''

    def __init__(self, main_window, schema):
        '''
        Initialize the Titleblocks tab.
        '''
        # Register parent window and schema
        self.main = main_window
        self.schema = schema

        # Register UI Event Handlers
        self.main.Configure.Click += self.configure_titleblock
        self.main.ConfiguredTitleblocksListBox.SelectionChanged += self.display_titleblock_details

        # Initialize lists
        self.refresh_titleblock_lists()

        return


    def refresh_titleblock_lists(self):
        '''
        Refresh the lists of Configured and Not Configured titleblocks.
        '''
        self.main.configured_titleblocks = []
        self.main.not_configured_titleblocks = []

        for tb in self.main.titleblocks:
            entity = self.get_titleblock_entity(tb)
            if entity.IsValid():
                self.main.configured_titleblocks.append(tb)
            else:
                self.main.not_configured_titleblocks.append(tb)

        self.main.ConfiguredTitleblocksListBox.ItemsSource = [tb.Name for tb in self.main.configured_titleblocks]
        self.main.NotConfiguredTitleblocksListBox.ItemsSource = [tb.Name for tb in self.main.not_configured_titleblocks]

        return


    def configure_titleblock(self, sender, args):
        '''
        Configure the titleblock selected in the 'Not Configured' list.
        '''
        # Get the selected titleblock from the UI
        i = self.main.NotConfiguredTitleblocksListBox.SelectedIndex
        if i < 0:
            forms.alert("Please select a titleblock to configure.")
            return
        tb = self.main.not_configured_titleblocks[i]

        # Close the main window so we can prompt the user
        self.main.Close()

        # Prompt the user to select the corners of the drawing area;
        # calculate the width/height/center;
        # store the values in Extensible Storage;
        self._configure_titleblock_workflow(tb)
        
        # Respawn the main window
        new_main_window = self.main.__class__('SheetSetManager_ui.xaml')
        new_main_window.show_dialog()

        return


    def _configure_titleblock_workflow(self, tb):
        '''
        Workflow to configure the titleblock.
        '''
        # Create a temporary sheet to get the drawing area dimensions
        with revit.Transaction("Create Temp Sheet"):
            temp_sheet = ViewSheet.Create(self.main.doc, tb.Id)
            temp_sheet.SheetNumber = "temp"
            temp_sheet.Name = "temp"
        
        # Store the current view for later
        old_view = self.main.uidoc.ActiveView

        # Set the new sheet as the active view
        self.main.uidoc.ActiveView = new_sheet

        # Prompt the user to select the drawing area dimensions
        forms.alert("Select the bottom-left corner of the drawing area.")
        bottom_left_corner = self.main.uidoc.Selection.PickPoint("Select the bottom-left corner of the drawing area")
        forms.alert("Select the top-right corner of the drawing area.")
        top_right_corner = self.main.uidoc.Selection.PickPoint("Select the top-right corner of the drawing area")

        # Calculate the width, height, and center of the drawing area
        width = abs(top_right_corner.X - bottom_left_corner.X)
        height = abs(top_right_corner.Y - bottom_left_corner.Y)
        center_x = ((bottom_left_corner.X + top_right_corner.X) / 2.0)
        center_y = ((bottom_left_corner.Y + top_right_corner.Y) / 2.0)

        # Return to the original view
        self.main.uidoc.ActiveView = old_view

        # Delete the temporary sheet
        if new_sheet and new_sheet.Id and new_sheet.Id.IntegerValue > 0:
            with revit.Transaction("Delete Temp Sheet"):
                self.main.doc.Delete(new_sheet.Id)
        
        # Store the titleblock configuration in the Extensible Storage
        self.set_titleblock_entity(tb, width, height, center_x, center_y)

        return

        
    def display_titleblock_details(self, entity):
        '''
        In the Details pane, display the configuration details of the titleblock selected in the 'Configured' list.
        '''
        # Get the selected titleblock from the UI
        i = self.main.ConfiguredTitleblocksListBox.SelectedIndex

        # If no titleblock is selected, clear the details
        if i < 0:
            width = height = center_x = center_y = ''

        # Otherwise, get the details from the selected titleblock's entity
        else:
            tb = self.main.configured_titleblocks[i]
            entity = self.get_titleblock_entity(tb)
            width = self.get_titleblock_entity(entity).Get[str]('drawing_area_width')
            height = self.get_titleblock_entity(entity).Get[str]('drawing_area_height')
            center_x = self.get_titleblock_entity(entity).Get[str]('drawing_area_center_x')
            center_y = self.get_titleblock_entity(entity).Get[str]('drawing_area_center_y')

        # Set the details in the UI
        self.main.TitleblockDetails_Width.Text = width
        self.main.TitleblockDetails_Height.Text = height
        self.main.TitleblockDetails_CenterX.Text = center_x
        self.main.TitleblockDetails_CenterY.Text = center_y

        return


    def get_titleblock_entity(self, tb):
        '''
        Get the titleblock entity from the Extensible Storage.
        '''
        # Get the titleblock entity from the Extensible Storage.
        entity = tb.GetEntity(self.schema)
        if entity.IsValid():
            return entity
        else:
            return None


    def set_titleblock_entity(self, tb, width, height, center_x, center_y):
        '''
        Set the titleblock entity with the given parameters.
        '''
        # Create a new entity using the Titleblocks schema
        entity = Entity(self.schema)
        
        # Set the drawing area dimensions and center coordinates
        entity.Set[str]('drawing_area_width', str(width))
        entity.Set[str]('drawing_area_height', str(height))
        entity.Set[str]('drawing_area_center_x', str(center_x))
        entity.Set[str]('drawing_area_center_y', str(center_y))

        # Store the entity in the titleblock type
        with revit.Transaction('Set Titleblock Drawing Area Config'):
            tb.SetEntity(entity)
        
        return
