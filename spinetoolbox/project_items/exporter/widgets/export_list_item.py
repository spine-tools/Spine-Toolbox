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

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget


class ExportListItem(QWidget):
    """A widget with few controls to select the output file name and open a settings window."""

    refresh_settings_clicked = Signal(str)
    """signal that is triggered when the settings should be refreshed"""
    open_settings_clicked = Signal(str)
    """signal that is triggered when settings window should be opened"""
    file_name_changed = Signal(str, str)
    """signal that is fired when the file name field is changed"""

    def __init__(self, url, file_name, parent=None):
        """
        Args:
            url (str): database's identifier to be shown on a label
            file_name (str): relative path to the exported file name
            parent (QWidget): a parent widget
        """
        from ..ui.export_list_item import Ui_Form

        super().__init__(parent)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.url_field.setText(url)
        self._ui.url_field.setToolTip(url)
        self._ui.out_file_name_edit.setText(file_name)
        self._ui.out_file_name_edit.textChanged.connect(lambda text: self.file_name_changed.emit(text, url))
        self._ui.refresh_button.clicked.connect(lambda checked: self.refresh_settings_clicked.emit(url))
        self._ui.settings_button.clicked.connect(lambda checked: self.open_settings_clicked.emit(url))

    @property
    def refresh_button(self):
        """a QButton to trigger refresh due to changes in the database"""
        return self._ui.refresh_button

    @property
    def settings_button(self):
        """a QButton which should open a settings window"""
        return self._ui.settings_button

    @property
    def out_file_name_edit(self):
        """export file name QLineEdit"""
        return self._ui.out_file_name_edit

    @property
    def url_field(self):
        return self._ui.url_field
