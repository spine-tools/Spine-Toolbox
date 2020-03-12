######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
A small widget to set up a database export in Gdx Export settings.

:author: A. Soininen (VTT)
:date:   10.9.2019
"""

from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QWidget
from ..settings_state import SettingsState


class ExportListItem(QWidget):
    """A widget with few controls to select the output file name and open a settings window."""

    open_settings_clicked = Signal(str)
    """signal that is triggered when settings window should be opened"""
    file_name_changed = Signal(str, str)
    """signal that is fired when the file name field is changed"""

    def __init__(self, url, file_name, settings_state, parent=None):
        """
        Args:
            url (str): database's identifier to be shown on a label
            file_name (str): relative path to the exported file name
            parent (QWidget): a parent widget
        """
        from ..ui.export_list_item import Ui_Form

        super().__init__(parent)
        self._ui = Ui_Form()
        self._url = url
        self._file_name = file_name
        self._ui.setupUi(self)
        self._ui.url_field.setText(url)
        self._ui.url_field.setToolTip(url)
        self._ui.out_file_name_edit.setText(file_name)
        self._ui.out_file_name_edit.editingFinished.connect(self._emit_file_name_changed)
        self._ui.settings_button.clicked.connect(self._emit_open_settings_clicked)
        self.handle_settings_state_changed(settings_state)

    @property
    def out_file_name_edit(self):
        """export file name QLineEdit"""
        return self._ui.out_file_name_edit

    @property
    def url_field(self):
        """Text in the database URL field."""
        return self._ui.url_field

    @Slot("QVariant")
    def handle_settings_state_changed(self, state):
        self._ui.notification_label.setText("")
        if state == SettingsState.FETCHING:
            self._ui.settings_button.setEnabled(False)
            self._ui.settings_button.setToolTip("Database is being read...")
        elif state == SettingsState.ERROR:
            self._ui.settings_button.setEnabled(False)
            self._ui.settings_button.setToolTip("Cannot open settings window.")
            self._ui.notification_label.setText(
                "<span style='color:#ff3333;white-space: pre-wrap;'>"
                + "Failed to initialize settings for the database.</span>"
            )
        else:
            self._ui.settings_button.setEnabled(True)
            self._ui.settings_button.setToolTip("Open Gdx Export Settings.")
            if state == SettingsState.INDEXING_PROBLEM:
                self._ui.notification_label.setText(
                    "<span style='color:#ff3333;white-space: pre-wrap;'>"
                    + "Open settings to set up parameter indexing.</span>"
                )

    @Slot()
    def _emit_file_name_changed(self):
        """Emits file_name_changed signal."""
        file_name = self._ui.out_file_name_edit.text()
        if self._file_name == file_name:
            return
        self._file_name = file_name
        self.file_name_changed.emit(file_name, self._url)

    @Slot(bool)
    def _emit_open_settings_clicked(self, _):
        """Emits open_settings_clicked signal."""
        self.open_settings_clicked.emit(self._url)
