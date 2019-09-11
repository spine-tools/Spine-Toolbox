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
Widget shown to user when a new Gdx Export item is created.

:author: A. Soininen (VTT)
:date:   6.9.2019
"""

from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QWidget, QStatusBar
from config import STATUSBAR_SS, INVALID_CHARS
from ui.add_gdx_export import Ui_Form


class AddGdxExportWidget(QWidget):
    """A widget to query user's preferences for a new item.

    Attributes:
        toolbox (ToolboxUI): Parent widget
        x (int): X coordinate of new item
        y (int): Y coordinate of new item
    """

    def __init__(self, toolbox, x, y):
        """Initialize class."""
        super().__init__(parent=toolbox, f=Qt.Window)  # Setting parent inherits stylesheet
        self._toolbox = toolbox
        self._x = x
        self._y = y
        self._project = self._toolbox.project()
        #  Set up the user interface from Designer.
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        # Add status bar to form
        self._statusbar = QStatusBar(self)
        self._statusbar.setFixedHeight(20)
        self._statusbar.setSizeGripEnabled(False)
        self._statusbar.setStyleSheet(STATUSBAR_SS)
        self._ui.horizontalLayout_statusbar_placeholder.addWidget(self._statusbar)
        # Class attributes
        self._name = ''
        self._description = ''
        self.__connect_signals()
        self._ui.lineEdit_name.setFocus()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def __connect_signals(self):
        """Connect signals to slots."""
        self._ui.lineEdit_name.textChanged.connect(self.__name_changed)  # Name -> folder name connection
        self._ui.pushButton_ok.clicked.connect(self.__ok_clicked)
        self._ui.pushButton_cancel.clicked.connect(self.close)

    @Slot(name='__name_changed')
    def __name_changed(self):
        """Update label to show upcoming folder name."""
        name = self._ui.lineEdit_name.text()
        default = "Folder:"
        if name == '':
            self._ui.label_folder.setText(default)
        else:
            folder_name = name.lower().replace(' ', '_')
            msg = default + " " + folder_name
            self._ui.label_folder.setText(msg)

    @Slot(name='__ok_clicked')
    def __ok_clicked(self):
        """Check that given item name is valid and add it to project."""
        self._name = self._ui.lineEdit_name.text()
        self._description = self._ui.lineEdit_description.text()
        if not self._name:  # No name given
            self._statusbar.showMessage("Name missing", 3000)
            return
        # Check for invalid characters for a folder name
        if any((True for x in self._name if x in INVALID_CHARS)):
            self._statusbar.showMessage("Name not valid for a folder name", 3000)
            return
        # Check that name is not reserved
        if self._toolbox.project_item_model.find_item(self._name):
            msg = "Item '{0}' already exists".format(self._name)
            self._statusbar.showMessage(msg, 3000)
            return
        # Check that short name (folder) is not reserved
        short_name = self._name.lower().replace(' ', '_')
        if self._toolbox.project_item_model.short_name_reserved(short_name):
            msg = "Item using folder '{0}' already exists".format(short_name)
            self._statusbar.showMessage(msg, 3000)
            return
        # Create new Item
        self.__call_add_item()
        self.close()

    def __call_add_item(self):
        """Creates new Item according to user's selections."""
        self._project.add_gdx_export(self._name, self._description, self._x, self._y, set_selected=True)

    def keyPressEvent(self, e):
        """
        Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.__ok_clicked()

    def closeEvent(self, event=None):
        """
        Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
            scene = self._toolbox.ui.graphicsView.scene()
            item_shadow = scene.item_shadow
            if item_shadow:
                scene.removeItem(item_shadow)
                scene.item_shadow = None
