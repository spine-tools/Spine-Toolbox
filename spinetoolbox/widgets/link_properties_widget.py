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
from .custom_qwidgets import PurgeSettingsDialog
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
        self._purge_settings_dialog = None
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.spinBox_write_index.valueChanged.connect(self._handle_write_index_value_changed)
        self.ui.checkBox_use_datapackage.stateChanged.connect(self._handle_use_datapackage_state_changed)
        self.ui.checkBox_use_memory_db.stateChanged.connect(self._handle_use_memory_db_state_changed)
        self.ui.checkBox_purge_before_writing.stateChanged.connect(self._handle_purge_before_writing_state_changed)
        self.ui.purge_settings_button.clicked.connect(self._open_purge_settings_dialog)

    def set_link(self, connection):
        """Hooks the widget to given link, so that user actions are reflected in the link's filter configuration.

        Args:
            connection (LoggingConnection)
        """
        self._connection = connection
        model = self.ui.treeView_filters.model()
        if model is not None:
            model.tree_built.disconnect(self.ui.treeView_filters.expandAll)
        self.ui.treeView_filters.setModel(self._connection.resource_filter_model)
        self._connection.resource_filter_model.tree_built.connect(self.ui.treeView_filters.expandAll)
        self._connection.refresh_resource_filter_model()
        self._toolbox.label_item_name.setText(f"<b>Link {self._connection.link.name}</b>")
        self.load_connection_options()
        self.ui.treeView_filters.setEnabled(self._connection.may_have_filters())
        self.ui.spinBox_write_index.setEnabled(self._connection.may_have_write_index())
        self.ui.label_write_index.setEnabled(self._connection.may_have_write_index())
        self.ui.checkBox_use_memory_db.setEnabled(self._connection.may_use_memory_db())
        self.ui.checkBox_use_datapackage.setEnabled(self._connection.may_use_datapackage())
        self.ui.checkBox_purge_before_writing.setEnabled(self._connection.may_purge_before_writing())

    def unset_link(self):
        """Releases the widget from any links."""
        self.ui.treeView_filters.setModel(None)

    @Slot(int)
    def _handle_write_index_value_changed(self, value):
        if self._connection.write_index == value:
            return
        options = {"write_index": value}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

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
    def _handle_purge_before_writing_state_changed(self, _state):
        checked = self.ui.checkBox_purge_before_writing.isChecked()
        if self._connection.purge_before_writing == checked:
            return
        options = {"purge_before_writing": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

    @Slot(bool)
    def _open_purge_settings_dialog(self, _=False):
        """Opens the purge settings dialog."""
        if self._purge_settings_dialog is not None:
            self._purge_settings_dialog.raise_()
            return
        self._purge_settings_dialog = PurgeSettingsDialog(self._connection.purge_settings, self._toolbox)
        self._purge_settings_dialog.accepted.connect(self._handle_purge_settings_changed)
        self._purge_settings_dialog.destroyed.connect(self._clean_up_purge_settings_dialog)
        self._purge_settings_dialog.show()

    @Slot()
    def _handle_purge_settings_changed(self):
        """Pushes a command that sets new purge settings onto undo stack."""
        purge_settings = self._purge_settings_dialog.get_purge_settings()
        if self._connection.purge_settings == purge_settings:
            return
        options = {"purge_settings": purge_settings}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._connection, options))

    @Slot()
    def _clean_up_purge_settings_dialog(self):
        """Cleans things related to purge settings dialog."""
        self._purge_settings_dialog = None

    def load_connection_options(self):
        self.ui.checkBox_use_datapackage.setChecked(self._connection.use_datapackage)
        self.ui.checkBox_use_memory_db.setChecked(self._connection.use_memory_db)
        self.ui.checkBox_purge_before_writing.setChecked(self._connection.purge_before_writing)
        self.ui.purge_settings_button.setEnabled(self._connection.purge_before_writing)
        self.ui.spinBox_write_index.setValue(self._connection.write_index)
