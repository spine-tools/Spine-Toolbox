#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
QWidget that is used to display information contained in a Data Store.

:author: M. Marin (KTH)
:date:   19.4.2018
"""

from PySide2.QtWidgets import QWidget
from ui.subwindow_data_store import Ui_Form


class DataStoreWidget(QWidget):
    """Data Store subwindow class.

    Attributes:
        item_type (str): Internal widget object type (should always be 'Data Store')
    """
    def __init__(self, owner, item_type):
        """ Initialize class."""
        super().__init__()
        self._owner = owner
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setObjectName(item_type)  # TODO: Remove. item_type is an instance variable of DataStore objects
        self.ui.label_name.setFocus()

    def owner(self):
        """Return owner of this window, ie an instance of DataStore."""
        return self._owner

    def set_name_label(self, txt):
        """Set new text for the name label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.ui.label_name.setText(txt)

    def name_label(self):
        """Return name label text."""
        return self.ui.label_name.text()

    def closeEvent(self, event):
        """Hide widget and is proxy instead of closing them.

        Args:
            event (QCloseEvent): Event initiated when user clicks 'X'
        """
        event.ignore()
        self.hide()  # Hide widget and its proxy hides as well
