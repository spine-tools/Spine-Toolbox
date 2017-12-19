#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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
QWidget that is used as an internal widget for a QMdiSubWindow.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   15.12.2017
"""

from PySide2.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide2.QtCore import Qt


class SubWindowWidget(QWidget):
    """Class constructor.

    Attributes:
        parent (QWidget): Parent widget.
        name (str): Internal widget object name
    """
    def __init__(self, parent, name):
        """ Initialize class."""
        super().__init__(parent)
        self.setObjectName(name)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setMaximumHeight(23)
        self.edit_button.setMaximumWidth(65)
        self.name_label = QLabel(name)
        self.data_label = QLabel("data")
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.name_label)
        vertical_layout.addWidget(self.data_label)
        vertical_layout.addWidget(self.edit_button)
        self.setLayout(vertical_layout)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def update_name_label(self, txt):
        """Set new text for the name label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.name_label.setText(txt)

    def update_data_label(self, txt):
        """Set new text for the data label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.data_label.setText(txt)

    def name_label_txt(self):
        """Return name label text."""
        return self.name_label.text()

    def data_label_txt(self):
        """Return data label text."""
        return self.data_label.text()
