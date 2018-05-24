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
QWidget that is used to display information contained in a View.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi
:date:   25.4.2018
"""

import logging
from PySide2.QtWidgets import QWidget
from ui.subwindow_view import Ui_Form


class ViewWidget(QWidget):
    """Class constructor.

    Attributes:
        owner (str): Name of the item that owns this widget
        item_type (str): Internal widget object type (should always be 'View')
    """
    def __init__(self, owner, item_type):
        """ Initialize class."""
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setObjectName(item_type)  # This is set also in setupUi(). Maybe do this only in Qt Designer.
        self._owner = owner  # Name of object that owns this object (e.g. 'View 1')
        self.ui.label_name.setFocus()

    def set_owner(self, owner):
        """Set owner of this widget.

        Args:
            owner (str): New owner
        """
        self._owner = owner

    def owner(self):
        """Returns owner of this widget."""
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

    def set_type_label(self, txt):
        """Set new text for the type label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.ui.label_type.setText(txt)

    def type_label(self):
        """Return type label text."""
        return self.ui.label_type.text()

    def set_data_label(self, txt):
        """Set new text for the data label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.ui.label_data.setText(txt)

    def data_label(self):
        """Return data label text."""
        return self.ui.label_data.text()

    def closeEvent(self, event):
        """Hide widget and is proxy instead of closing them.

        Args:
            event (QCloseEvent): Event initiated when user clicks 'X'
        """
        event.ignore()
        self.hide()  # Hide widget and its proxy hides as well
