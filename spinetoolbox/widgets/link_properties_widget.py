######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
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
from .properties_widget import PropertiesWidgetBase
from ..project_commands import SetConnectionOptionsCommand


class LinkPropertiesWidget(PropertiesWidgetBase):
    """Widget for connection link properties."""

    def __init__(self, toolbox, base_color=None):
        """
        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.link_properties import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(toolbox, base_color=base_color)
        self._connection = None
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.checkBox_use_datapackage.stateChanged.connect(self._handle_use_datapackage_state_changed)
        self.ui.checkBox_use_memory_db.stateChanged.connect(self._handle_use_memory_db_state_changed)
        self.ui.spinBox_write_index.valueChanged.connect(self._handle_write_index_value_changed)

    def set_link(self, connection):
        """Hooks the widget to given link, so that user actions are reflected in the link's filter configuration.

        Args:
            connection (LoggingConnection)
        """
        self._connection = connection
        self._connection.refresh_resource_filter_model()
        self.ui.treeView_filters.setModel(self._connection.resource_filter_model)
        self.ui.treeView_filters.expandAll()
        self._toolbox.label_item_name.setText(f"<b>Link {self._connection.link.name}</b>")
        self.load_connection_options()
        source_item_type = self._toolbox.project().get_item(self._connection.source).item_type()
        destination_item_type = self._toolbox.project().get_item(self._connection.destination).item_type()
        self.ui.treeView_filters.setEnabled(bool(self._connection.database_resources))
        self.ui.checkBox_use_memory_db.setEnabled({"Tool", "Data Store"} == {source_item_type, destination_item_type})
        self.ui.checkBox_use_datapackage.setEnabled(source_item_type in {"Exporter", "Data Connection", "Tool"})
        self.ui.spinBox_write_index.setEnabled(destination_item_type == "Data Store")
        self.ui.label_write_index.setEnabled(destination_item_type == "Data Store")

    def unset_link(self):
        """Releases the widget from any links."""
        self.ui.treeView_filters.setModel(None)

    @Slot(int)
    def _handle_use_datapackage_state_changed(self, _state):
        checked = self.ui.checkBox_use_datapackage.isChecked()
        if self._connection.use_datapackage == checked:
            return
        options = {"use_datapackage": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

    @Slot(int)
    def _handle_use_memory_db_state_changed(self, _state):
        checked = self.ui.checkBox_use_memory_db.isChecked()
        if self._connection.use_memory_db == checked:
            return
        options = {"use_memory_db": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

    @Slot(int)
    def _handle_write_index_value_changed(self, value):
        if self._connection.write_index == value:
            return
        options = {"write_index": value}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

    def load_connection_options(self):
        self.ui.checkBox_use_datapackage.setChecked(self._connection.use_datapackage)
        self.ui.checkBox_use_memory_db.setChecked(self._connection.use_memory_db)
        self.ui.spinBox_write_index.setValue(self._connection.write_index)
