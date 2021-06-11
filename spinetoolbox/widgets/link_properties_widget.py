######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from ..project_commands import SetConnectionOptionsCommand


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
        self._link = None
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Link properties")
        self.ui.checkBox_use_datapackage.stateChanged.connect(self._handle_use_datapackage_state_changed)

    def set_link(self, link):
        """Hooks the widget to given link, so that user actions are reflected in the link's filter configuration.

        Args:
            link (Link)
        """
        self._link = link
        link.refresh_resource_filter_model()
        self.ui.treeView_filters.setModel(link.resource_filter_model)
        self.ui.treeView_filters.expandAll()
        self.ui.label_link_name.setText(link.name)
        self.load_connection_options()

    def unset_link(self):
        """Releases the widget from any links."""
        self.ui.treeView_filters.setModel(None)

    @Slot(int)
    def _handle_use_datapackage_state_changed(self, _state):
        checked = self.ui.checkBox_use_datapackage.isChecked()
        if self._link.connection.use_datapackage == checked:
            return
        options = {"use_datapackage": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._link, options))

    def load_connection_options(self):
        self.ui.checkBox_use_datapackage.setChecked(self._link.connection.use_datapackage)
