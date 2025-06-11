from pyrevit import forms


class CreateViewsSheetsWarning(forms.WPFWindow):

    def __init__(self, parent):

        # Initialize the window
        super().__init__('CreateViewsSheetsWarning_window.xaml')
        self.parent = parent
        self.main = parent.main

        self.ContinueButton.Click += self.continue_clicked
        self.CancelButton.Click += self.cancel_clicked

    def continue_clicked(self, sender, args):
        if self.DoNotShowAgainCheckBox.IsChecked:
            self.main.config.create_views_sheets_hide_warning = True
        self.DialogResult = True
        self.Close()

    def cancel_clicked(self, sender, args):
        self.DialogResult = False
        self.Close()
