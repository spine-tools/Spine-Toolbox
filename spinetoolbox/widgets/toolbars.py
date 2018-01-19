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
Functions to make and handle QToolBars.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.1.2018
"""

from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QToolBar, QLabel, QComboBox, QAction
from PySide2.QtCore import Qt, QSize
from config import ICON_TOOLBAR_SS


# noinspection PyUnresolvedReferences
def make_item_toolbar(ui):
    """Initialize item toolbar.

    Args:
        ui (ToolboxUI): Application QMainWindow
    """
    toolbar = QToolBar("Add Item Toolbar", ui)
    add_data_store_icon = QIcon()
    add_data_store_icon.addPixmap(QPixmap(":/icons/ds_icon.png"), QIcon.Normal, QIcon.On)
    add_data_connection_icon = QIcon()
    add_data_connection_icon.addPixmap(QPixmap(":/icons/dc_icon.png"), QIcon.Normal, QIcon.On)
    add_tool_icon = QIcon()
    add_tool_icon.addPixmap(QPixmap(":/icons/tool_icon.png"), QIcon.Normal, QIcon.On)
    add_view_icon = QIcon()
    add_view_icon.addPixmap(QPixmap(":/icons/view_icon.png"), QIcon.Normal, QIcon.On)
    remove_all_icon = QIcon()
    remove_all_icon.addPixmap(QPixmap(":/icons/remove_all.png"), QIcon.Normal, QIcon.On)

    label = QLabel("Add Item")
    add_data_store = QAction(add_data_store_icon, "Data Store", ui)
    add_data_connection = QAction(add_data_connection_icon, "Data Connection", ui)
    add_tool = QAction(add_tool_icon, "Tool", ui)
    add_view = QAction(add_view_icon, "View", ui)
    remove_all = QAction(remove_all_icon, "Remove All", ui)
    # Set tooltips
    add_data_store.setToolTip("Add Data Store to project")
    add_data_connection.setToolTip("Add Data Connection to project")
    add_tool.setToolTip("Add Tool to project")
    add_view.setToolTip("Add View to project")
    remove_all.setToolTip("Remove all items from project")
    # Add actions to toolbar
    toolbar.addWidget(label)
    toolbar.addAction(add_data_store)
    toolbar.addAction(add_data_connection)
    toolbar.addAction(add_tool)
    toolbar.addAction(add_view)
    toolbar.addSeparator()
    toolbar.addAction(remove_all)
    toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
    toolbar.setIconSize(QSize(20, 20))
    # Connect signals
    add_data_store.triggered.connect(ui.show_add_data_store_form)
    add_data_connection.triggered.connect(ui.show_add_data_connection_form)
    add_tool.triggered.connect(ui.show_add_tool_form)
    add_view.triggered.connect(ui.show_add_view_form)
    remove_all.triggered.connect(ui.clear_ui)
    # Set stylesheet
    toolbar.setStyleSheet(ICON_TOOLBAR_SS)
    toolbar.setObjectName("ItemToolbar")
    return toolbar
