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
Widget shown to user when a new Tool is created.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.1.2017
"""

import logging
from PySide2.QtWidgets import QWidget, QStatusBar
from PySide2.QtCore import Slot, Qt
import ui.add_tool
from config import STATUSBAR_SS, INVALID_CHARS
from helpers import short_name_reserved


class AddToolWidget(QWidget):
    """A widget to query user's preferences for a new item.

    Attributes:
        parent: Parent widget.
    """
    def __init__(self, parent):
        """Initialize class."""
        super().__init__(f=Qt.Window)
        self._parent = parent  # QWidget parent
        # self._tool_model = tool_model
        #  Set up the user interface from Designer.
        self.ui = ui.add_tool.Ui_Form()
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
        # Init
        self.ui.comboBox_tool.setModel(self._parent.tool_candidate_model)
        self.ui.lineEdit_name.setFocus()
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.lineEdit_name.textChanged.connect(self.name_changed)  # Name -> folder name connection
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        self.ui.comboBox_tool.currentIndexChanged.connect(self.update_args)

    @Slot(int, name='update_args')
    def update_args(self, row):
        """Show Tool candidate command line arguments in text input.

        Args:
            row (int): Selected row number
        """
        if row == 0:
            # No Tool selected
            self.ui.lineEdit_tool_args.setText("")
            return
        selected_tool = self._parent.tool_candidate_model.tool(row)
        args = selected_tool.cmdline_args
        if not args:
            # Tool cmdline_args is None if the line does not exist in Tool definition file
            args = ''
        self.ui.lineEdit_tool_args.setText("{0}".format(args))
        return

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
        if not self.name:  # No name given
            self.statusbar.showMessage("Name missing", 3000)
            return
        # Check for invalid characters for a folder name
        if any((True for x in self.name if x in INVALID_CHARS)):
            self.statusbar.showMessage("Name not valid for a folder name", 3000)
            return
        # Check that name is not reserved
        if self._parent.find_item(self.name, Qt.MatchExactly | Qt.MatchRecursive):
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
        selected_row = self.ui.comboBox_tool.currentIndex()
        if selected_row == 0:
            logging.debug("Selected row 0 (no tool)")
            selected_tool = None
        else:
            selected_tool = self._parent.tool_candidate_model.tool(selected_row)
            logging.debug("Adding Tool '{0}' with tool {1}".format(self.name, selected_tool.name))
        self._parent.add_tool(self.name, self.description, selected_tool)

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
