######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Widget shown to user when a new Project Item is created."""
from PySide6.QtWidgets import QWidget, QStatusBar
from PySide6.QtCore import Slot, Qt
from spine_engine.utils.helpers import shorten
from ..config import STATUSBAR_SS
from ..helpers import unique_name
from ..project import ItemNameStatus


class AddProjectItemWidget(QWidget):
    """A widget to query user's preferences for a new item.

    Attributes:
        toolbox (ToolboxUI): Parent widget
        x (int): X coordinate of new item
        y (int): Y coordinate of new item
    """

    def __init__(self, toolbox, x, y, class_, spec=""):
        """Initialize class."""
        from ..ui.add_project_item import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolbox, f=Qt.Window)  # Setting parent inherits stylesheet
        self._toolbox = toolbox
        self._x = x
        self._y = y
        #  Set up the user interface from Designer.
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Init
        if toolbox.supports_specifications(class_.item_type()):
            self.ui.comboBox_specification.setModel(toolbox.filtered_spec_factory_models[class_.item_type()])
            if spec:
                self.ui.comboBox_specification.hide()
                prefix = spec
            else:
                prefix = class_.item_type()
                self.ui.comboBox_specification.setCurrentIndex(-1)
        else:
            prefix = class_.item_type()
            self.ui.comboBox_specification.hide()
        existing_item_names = toolbox.project().all_item_names
        self.name = unique_name(prefix, existing_item_names) if prefix in existing_item_names else prefix
        self.description = ""
        self.connect_signals()
        self.ui.lineEdit_name.setText(self.name)
        self.ui.lineEdit_name.selectAll()
        self.ui.lineEdit_name.setFocus()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(f"Add {class_.item_type()}")

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.lineEdit_name.textChanged.connect(self.handle_name_changed)  # Name -> folder name connection
        self.ui.pushButton_ok.clicked.connect(self.handle_ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot()
    def handle_name_changed(self):
        """Update label to show upcoming folder name."""
        name = self.ui.lineEdit_name.text()
        default = "Folder:"
        if name == "":
            self.ui.label_folder.setText(default)
        else:
            folder_name = name.lower().replace(" ", "_")
            msg = default + " " + folder_name
            self.ui.label_folder.setText(msg)

    @Slot()
    def handle_ok_clicked(self):
        """Check that given item name is valid and add it to project."""
        self.name = self.ui.lineEdit_name.text()
        self.description = self.ui.lineEdit_description.text()
        if not self.name:
            self.statusbar.showMessage("Name missing", 3000)
            return
        name_status = self._toolbox.project().validate_project_item_name(self.name)
        if name_status == ItemNameStatus.INVALID:
            self.statusbar.showMessage("Name not valid for a folder name", 3000)
            return
        if name_status == ItemNameStatus.EXISTS:
            msg = f"Item '{self.name}' already exists"
            self.statusbar.showMessage(msg, 3000)
            return
        if name_status == ItemNameStatus.SHORT_NAME_EXISTS:
            msg = f"Item using folder '{shorten(self.name)}' already exists"
            self.statusbar.showMessage(msg, 3000)
            return
        self.call_add_item()
        self._toolbox.ui.graphicsView.scene().clearSelection()
        for icon in self._toolbox.ui.graphicsView.scene().project_item_icons():
            if icon.name() == self.name:
                icon.setSelected(True)
        self.close()

    def call_add_item(self):
        """Creates new Item according to user's selections.

        Must be reimplemented by subclasses.
        """
        raise NotImplementedError()

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.handle_ok_clicked()

    def closeEvent(self, event=None):
        """Handle close window.

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
