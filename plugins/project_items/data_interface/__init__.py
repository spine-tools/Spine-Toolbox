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
Data store plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""


from .ui.data_interface_properties import Ui_Form
from .data_interface import DataInterface
from .data_interface_icon import DataInterfaceIcon
from PySide2.QtWidgets import QWidget
from config import TREEVIEW_HEADER_SS

item_category = "Data Interfaces"
item_type = "Data Interface"
item_maker = DataInterface
icon_maker = DataInterfaceIcon


def init_properties_ui(toolbox):
    properties_ui = Ui_Form()
    properties_widget = QWidget()
    properties_ui.setupUi(properties_widget)
    properties_ui.treeView_data_interface_files.setStyleSheet(TREEVIEW_HEADER_SS)
    # Add page to properties tab_widget
    toolbox.ui.tabWidget_item_properties.addTab(properties_widget, item_type)
    return properties_ui
