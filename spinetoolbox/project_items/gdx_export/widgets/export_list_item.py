######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from PySide2.QtWidgets import QWidget


class ExportListItem(QWidget):
    """A widget with few controls to select the output file name and open a settings window."""

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
