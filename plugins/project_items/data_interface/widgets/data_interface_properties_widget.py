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
Data interface properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from PySide2.QtWidgets import QWidget
from ..ui.data_interface_properties import Ui_Form
from config import TREEVIEW_HEADER_SS


class DataInterfacePropertiesWidget(QWidget):
    """Widget for the Data Interface Item Properties.

    Args:
        toolbox (ToolboxUI): The toolbox instance where this widget should be embeded
    """

    def __init__(self, toolbox):
        """Init class."""
        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_data_interface_files.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Data Interface")
