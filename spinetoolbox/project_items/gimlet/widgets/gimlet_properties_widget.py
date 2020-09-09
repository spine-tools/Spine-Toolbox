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
Gimlet properties widget.

:author: P. Savolainen (VTT)
:date:   15.4.2020
"""

from PySide2.QtWidgets import QWidget
from spinetoolbox.config import TREEVIEW_HEADER_SS
from ..utils import SHELLS


class GimletPropertiesWidget(QWidget):
    """Widget for the Gimlet Item Properties."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.gimlet_properties import Ui_Form

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.comboBox_shell.addItems(SHELLS)
        self.ui.treeView_files.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Gimlet")
