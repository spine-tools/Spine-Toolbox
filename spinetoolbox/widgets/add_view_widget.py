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
Widget shown to user when a new View is created.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.1.2017
"""

import logging
from PySide2.QtWidgets import QWidget, QStatusBar
from PySide2.QtCore import Slot, Qt
import ui.add_view
from config import STATUSBAR_SS, INVALID_CHARS
from helpers import short_name_reserved


class AddViewWidget(QWidget):
    """A widget to query user's preferences for a new item.

    Attributes:
        parent (ToolboxUI): Parent widget
        project (SpineToolboxProject): Project for the new item
    """
    def __init__(self, parent, project, x, y):
        """Initialize class."""
        super().__init__(f=Qt.Window)
        self._parent = parent
        self._project = project
        self._x = x
        self._y = y
        #  Set up the user interface from Designer.
        self.ui = ui.add_view.Ui_Form()
        self.ui.setupUi(self)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Class attributes
        self.name = ''
        self.description = ''
        self.connect_signals()
        self.ui.lineEdit_name.setFocus()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.lineEdit_name.textChanged.connect(self.name_changed)  # Name -> folder name connection
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot(name='name_changed')
    def name_changed(self):
        """Update label to show upcoming folder name."""
        name = self.ui.lineEdit_name.text()
        default = "Folder:"
        if name == '':
            self.ui.label_folder.setText(default)
        else:
            folder_name = name.lower().replace(' ', '_')
            msg = default + " " + folder_name
            self.ui.label_folder.setText(msg)

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Check that given item name is valid and add it to project."""
        self.name = self.ui.lineEdit_name.text()
        self.description = self.ui.lineEdit_description.text()
        # Check for invalid characters for a folder name
        if any((True for x in self.name if x in INVALID_CHARS)):
            self.statusbar.showMessage("Name not valid for a folder name", 3000)
            return
        # Check that name is not reserved
        if self._parent.project_item_model.find_item(self.name, Qt.MatchExactly | Qt.MatchRecursive):
            msg = "Item '{0}' already exists".format(self.name)
            self.statusbar.showMessage(msg, 3000)
            logging.error("Item with same name already in project")
            return
        # Check that short name (folder) is not reserved
        short_name = self.name.lower().replace(' ', '_')
        if short_name_reserved(short_name, self._parent.project_item_model):
            msg = "Item using folder '{0}' already exists".format(short_name)
            self.statusbar.showMessage(msg, 3000)
            return
        # Create new Item
        self.call_add_item()
        self.close()

    def call_add_item(self):
        """Creates new Item according to user's selections."""
        self._project.add_view(self.name, self.description, self._x, self._y)

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.ok_clicked()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
            item_shadow = self._parent.ui.graphicsView.item_shadow
            self._parent.ui.graphicsView.scene().removeItem(item_shadow)
