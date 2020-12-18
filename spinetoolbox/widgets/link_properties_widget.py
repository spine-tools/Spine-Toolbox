######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Link properties widget.

:author: M. Marin (KTH)
:date:   27.11.2020
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget


class LinkPropertiesWidget(QWidget):
    """Widget for the Data Connection Item Properties."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.link_properties import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Link properties")
        self.ui.treeView_resources.clicked.connect(self._handle_index_clicked)

    def set_link(self, link):
        """Hooks the widget to given link, so that user actions are reflected in the link's filter configuration.

        Args:
            link (Link)
        """
        link.refresh_resource_filter_model()
        self.ui.treeView_resources.setModel(link.resource_filter_model)
        qApp.processEvents()  # pylint: disable=undefined-variable
        self.ui.treeView_resources.expandAll()
        self.ui.label_link_name.setText(link.name)

    def unset_link(self):
        """Releases the widget from any links.

        Args:
            link (Link)
        """
        self.ui.treeView_resources.setModel(None)

    @Slot("QModelIndex")
    def _handle_index_clicked(self, index):
        self.ui.treeView_resources.model().toggle_checked_state(index)
