import json
from pyrevit import revit, forms
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, AccessLevel, Entity
from System import Guid


SHEET_GROUPS_SCHEMA_GUID = Guid('c2d3e4f5-6a7b-8c9d-0e1f-2a3b4c5d6e7f')
SHEET_GROUPS_SCHEMA_NAME = 'SheetSetManager_SheetGroups'


class SheetGroupsTab(object):
    def __init__(self, main_window):
        self.main = main_window
        self.main.NewSheetGroup.Click += self.new_sheet_group
        self.main.RenameSheetGroup.Click += self.rename_sheet_group
        self.main.DeleteSheetGroup.Click += self.delete_sheet_group
        self.main.EditSheetGroup.Click += self.edit_sheet_group
        self.main.SheetGroupsListBox.SelectionChanged += self._sheet_group_selected
        self.refresh_list()

    def get_project_info(self, doc):
        return doc.ProjectInformation

    def get_or_create_sheet_groups_schema(self):
        SHEET_GROUPS_SCHEMA_GUID = Guid('c2d3e4f5-6a7b-8c9d-0e1f-2a3b4c5d6e7f')
        SHEET_GROUPS_SCHEMA_NAME = 'SheetSetManager_SheetGroups'
        schema = Schema.Lookup(SHEET_GROUPS_SCHEMA_GUID)
        if not schema:
            schema_builder = SchemaBuilder(SHEET_GROUPS_SCHEMA_GUID)
            schema_builder.SetSchemaName(SHEET_GROUPS_SCHEMA_NAME)
            schema_builder.AddSimpleField('sheet_groups_json', str)
            schema_builder.SetReadAccessLevel(AccessLevel.Public)
            schema_builder.SetWriteAccessLevel(AccessLevel.Public)
            schema = schema_builder.Finish()
        return schema

    def get_sheet_groups_from_project_info(self, doc):
        pi = self.get_project_info(doc)
        schema = self.get_or_create_sheet_groups_schema()
        entity = pi.GetEntity(schema)
        if entity.IsValid():
            json_str = entity.Get[str]('sheet_groups_json')
            if json_str:
                try:
                    return json.loads(json_str)
                except:
                    return []
        return []

    def save_sheet_groups_to_project_info(self, doc, groups):
        pi = self.get_project_info(doc)
        schema = self.get_or_create_sheet_groups_schema()
        entity = Entity(schema)
        entity.Set('sheet_groups_json', json.dumps(groups, indent=2))
        with revit.Transaction('Save Sheet Groups to Project Info'):
            pi.SetEntity(entity)

    def refresh_list(self):
        self.main.sheet_groups = self.main._load_sheet_groups()
        self.main.SheetGroupsListBox.ItemsSource = [g['name'] for g in self.main.sheet_groups]
        self.main.SheetGroupNameValue.Text = ''
        self.main.SheetGroupDescriptionValue.Text = ''
        self.main.SheetGroupOtherValue.Text = ''

    def new_sheet_group(self, sender, args):
        name = forms.ask_for_string(prompt='Enter a name for the new sheet group:', title='New Sheet Group')
        if not name:
            forms.alert('Sheet Group name is required.')
            return
        groups = self.main._load_sheet_groups()
        if any(g['name'] == name for g in groups):
            forms.alert('A sheet group with this name already exists.')
            return
        description = forms.ask_for_string(prompt='Enter a description (optional):', title='Sheet Group Description') or ''
        other = forms.ask_for_string(prompt='Enter other field (optional):', title='Other Field') or ''
        group = {'name': name, 'description': description, 'other': other}
        groups.append(group)
        self.main._save_sheet_groups(groups)
        self.refresh_list()
        self.main.SheetGroupsListBox.SelectedIndex = len(groups) - 1

    def rename_sheet_group(self, sender, args):
        idx = self.main.SheetGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sheet_groups):
            forms.alert('Please select a sheet group to rename.')
            return
        group = self.main.sheet_groups[idx]
        new_name = forms.ask_for_string(default=group.get('name', ''), prompt='Enter a new name for the sheet group:', title='Rename Sheet Group')
        if not new_name:
            forms.alert('Name cannot be empty.')
            return
        if any(g['name'] == new_name for i, g in enumerate(self.main.sheet_groups) if i != idx):
            forms.alert('A sheet group with this name already exists.')
            return
        self.main.sheet_groups[idx]['name'] = new_name
        self.main._save_sheet_groups(self.main.sheet_groups)
        self.refresh_list()
        self.main.SheetGroupsListBox.SelectedIndex = idx

    def delete_sheet_group(self, sender, args):
        idx = self.main.SheetGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sheet_groups):
            forms.alert('Please select a sheet group to delete.')
            return
        group = self.main.sheet_groups[idx]
        confirm = forms.alert('Are you sure you want to delete the sheet group "{}"?'.format(group.get('name', '')), options=['Yes', 'No'])
        if confirm != 'Yes':
            return
        del self.main.sheet_groups[idx]
        self.main._save_sheet_groups(self.main.sheet_groups)
        self.refresh_list()

    def edit_sheet_group(self, sender, args):
        idx = self.main.SheetGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sheet_groups):
            forms.alert('Please select a sheet group to edit.')
            return
        group = self.main.sheet_groups[idx]
        name = forms.ask_for_string(default=group.get('name', ''), prompt='Edit name:', title='Edit Sheet Group')
        if not name:
            forms.alert('Name cannot be empty.')
            return
        if any(g['name'] == name for i, g in enumerate(self.main.sheet_groups) if i != idx):
            forms.alert('A sheet group with this name already exists.')
            return
        description = forms.ask_for_string(default=group.get('description', ''), prompt='Edit description (optional):', title='Edit Description') or ''
        other = forms.ask_for_string(default=group.get('other', ''), prompt='Edit other field (optional):', title='Edit Other Field') or ''
        self.main.sheet_groups[idx] = {'name': name, 'description': description, 'other': other}
        self.main._save_sheet_groups(self.main.sheet_groups)
        self.refresh_list()
        self.main.SheetGroupsListBox.SelectedIndex = idx

    def _sheet_group_selected(self, sender, args):
        idx = self.main.SheetGroupsListBox.SelectedIndex
        if idx < 0 or idx >= len(self.main.sheet_groups):
            self.main.SheetGroupNameValue.Text = ''
            self.main.SheetGroupDescriptionValue.Text = ''
            self.main.SheetGroupOtherValue.Text = ''
            return
        group = self.main.sheet_groups[idx]
        self.main.SheetGroupNameValue.Text = group.get('name', '')
        self.main.SheetGroupDescriptionValue.Text = group.get('description', '')
        self.main.SheetGroupOtherValue.Text = group.get('other', '')
