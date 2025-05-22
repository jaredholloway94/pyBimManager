from pyrevit import revit, forms

class NewSectorGroupWindow(forms.WPFWindow):
    '''
    Class to manage the New Sector Group window.
    '''

    def __init__(self, xaml_file, main_window):
        super().__init__(self, xaml_file)
        self.doc = revit.doc
        self.uidoc = revit.uidoc

        # Initialize the schema
        self.schema = self.init_schema()

        # Register UI Event Handlers
        self.OkButton.Click += self.on_ok_button_click
        self.CancelButton.Click += self.on_cancel_button_click

        return