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
Importer properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.config import TREEVIEW_HEADER_SS
from .custom_menus import FilesContextMenu


class ImporterPropertiesWidget(QWidget):
    """Widget for the Importer Item Properties."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        super().__init__()
        from ..ui.importer_properties import Ui_Form

        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_files.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Importer")
        # Class attributes
        self.files_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_files.customContextMenuRequested.connect(self.show_files_context_menu)

    @Slot("QPoint", name="show_di_files_context_menu")
    def show_files_context_menu(self, pos):
        """Create and show a context-menu in Importer properties source files view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_files.indexAt(pos)  # Index of selected item in references tree view.
        cur_index = self._toolbox.ui.treeView_project.currentIndex()  # Get selected Importer item
        importer = self._toolbox.project_item_model.item(cur_index).project_item
        global_pos = self.ui.treeView_files.viewport().mapToGlobal(pos)
        self.files_context_menu = FilesContextMenu(self, global_pos, ind)
        option = self.files_context_menu.get_action()
        if option == "Open import editor":
            importer.open_import_editor(ind)
        elif option == "Select connector type":
            importer.select_connector_type(ind)
        elif option == "Open directory...":
            importer.open_directory()
