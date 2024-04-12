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

"""Link properties widget."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMenu
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from .properties_widget import PropertiesWidgetBase
from .custom_qwidgets import PurgeSettingsDialog
from ..mvcmodels.resource_filter_model import ResourceFilterModel
from ..project_commands import (
    SetConnectionFilterTypeEnabled,
    SetConnectionOptionsCommand,
    SetConnectionDefaultFilterOnlineStatus,
)


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
        self.ui.filter_type_combo_box.addItems(sorted(ResourceFilterModel.FILTER_TYPES))
        self.ui.filter_type_combo_box.setCurrentText(ResourceFilterModel.FILTER_TYPE_TO_TEXT[SCENARIO_FILTER_TYPE])
        self.ui.filter_type_combo_box.currentTextChanged.connect(self._select_mutually_exclusive_filter)
        self._filter_validation_menu = QMenu(self)
        self._filter_validation_actions = self._populate_filter_validation_menu()
        self.ui.auto_check_filters_check_box.clicked.connect(self._handle_auto_check_filters_state_changed)
        self.ui.open_filter_validation_menu_button.setMenu(self._filter_validation_menu)
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
        may_have_filters = self._connection.may_have_filters()
        self.ui.filter_type_combo_box.setEnabled(may_have_filters)
        self.ui.treeView_filters.setEnabled(may_have_filters)
        if may_have_filters:
            for filter_type, filter_text in ResourceFilterModel.FILTER_TYPE_TO_TEXT.items():
                filter_type_enabled = self._connection.is_filter_type_enabled(filter_type)
                self._set_filter_type_expanded(filter_type, filter_type_enabled)
                if filter_type_enabled:
                    self.ui.filter_type_combo_box.blockSignals(True)
                    self.ui.filter_type_combo_box.setCurrentText(filter_text)
                    self.ui.filter_type_combo_box.blockSignals(False)
        self.ui.auto_check_filters_check_box.setChecked(self._connection.is_filter_online_by_default)
        self.ui.auto_check_filters_check_box.setEnabled(may_have_filters)
        self.ui.open_filter_validation_menu_button.setEnabled(may_have_filters)
        self.ui.spinBox_write_index.setEnabled(self._connection.may_have_write_index())
        self.ui.label_write_index.setEnabled(self._connection.may_have_write_index())
        self.ui.checkBox_use_memory_db.setEnabled(self._connection.may_use_memory_db())
        self.ui.checkBox_use_datapackage.setEnabled(self._connection.may_use_datapackage())
        self.ui.checkBox_purge_before_writing.setEnabled(self._connection.may_purge_before_writing())

    def unset_link(self):
        """Releases the widget from any links."""
        self.ui.treeView_filters.setModel(None)

    @Slot(bool)
    def _handle_auto_check_filters_state_changed(self, checked):
        """Updates filters' auto enabled setting.

        Args:
            checked (bool): True if the checkbox is checked, False otherwise
        """
        if checked == self._connection.is_filter_online_by_default:
            return
        self._toolbox.undo_stack.push(
            SetConnectionDefaultFilterOnlineStatus(self._toolbox.project(), self._connection, checked)
        )

    def set_auto_check_filters_state(self, checked):
        """Sets the checked status of filter default online status check box

        Args:
            checked (bool): True if the checkbox is checked
        """
        self.ui.auto_check_filters_check_box.setChecked(checked)

    def _populate_filter_validation_menu(self):
        """Adds actions to filter validation menu.

        Returns:
            dict: menu actions
        """
        action_data = {"Require at least one checked scenario": SCENARIO_FILTER_TYPE}
        actions = {}
        for label, filter_type in action_data.items():
            action = self._filter_validation_menu.addAction(label)
            action.setCheckable(True)
            action.toggled.connect(self._update_filter_validation_options)
            actions[filter_type] = action
        return actions

    @Slot(bool)
    def _update_filter_validation_options(self, checked):
        """"""
        for filter_type, action in self._filter_validation_actions.items():
            if self._connection.require_filter_online(filter_type) != action.isChecked():
                options = {"require_" + filter_type: checked}
                self._toolbox.undo_stack.push(
                    SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options)
                )
                return

    @Slot(int)
    def _handle_write_index_value_changed(self, value):
        if self._connection.write_index == value:
            return
        options = {"write_index": value}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options))

    @Slot(int)
    def _handle_use_datapackage_state_changed(self, _state):
        checked = self.ui.checkBox_use_datapackage.isChecked()
        if self._connection.use_datapackage == checked:
            return
        options = {"use_datapackage": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options))

    @Slot(int)
    def _handle_use_memory_db_state_changed(self, _state):
        checked = self.ui.checkBox_use_memory_db.isChecked()
        if self._connection.use_memory_db == checked:
            return
        options = {"use_memory_db": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options))

    @Slot(int)
    def _handle_purge_before_writing_state_changed(self, _state):
        checked = self.ui.checkBox_purge_before_writing.isChecked()
        if self._connection.purge_before_writing == checked:
            return
        options = {"purge_before_writing": checked}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options))

    @Slot(bool)
    def _open_purge_settings_dialog(self, _=False):
        """Opens the purge settings dialog."""
        if self._purge_settings_dialog is not None:
            self._purge_settings_dialog.raise_()
            return
        self._purge_settings_dialog = PurgeSettingsDialog(self._connection.purge_settings, parent=self._toolbox)
        self._purge_settings_dialog.setWindowTitle(f"Purge settings for connection {self._connection.link.name}")
        self._purge_settings_dialog.accepted.connect(self._handle_purge_settings_changed)
        self._purge_settings_dialog.destroyed.connect(self._clean_up_purge_settings_dialog)
        self._purge_settings_dialog.show()

    @Slot()
    def _handle_purge_settings_changed(self):
        """Pushes a command that sets new purge settings onto undo stack."""
        purge_settings = self._purge_settings_dialog.get_checked_states()
        if self._connection.purge_settings == purge_settings:
            return
        options = {"purge_settings": purge_settings}
        self._toolbox.undo_stack.push(SetConnectionOptionsCommand(self._toolbox.project(), self._connection, options))

    @Slot()
    def _clean_up_purge_settings_dialog(self):
        """Cleans things related to purge settings dialog."""
        self._purge_settings_dialog = None

    def load_connection_options(self):
        for filter_type, action in self._filter_validation_actions.items():
            action.toggled.disconnect()
            action.setChecked(self._connection.require_filter_online(filter_type))
            action.toggled.connect(self._update_filter_validation_options)
        self.ui.checkBox_use_datapackage.setChecked(self._connection.use_datapackage)
        self.ui.checkBox_use_memory_db.setChecked(self._connection.use_memory_db)
        self.ui.checkBox_purge_before_writing.setChecked(self._connection.purge_before_writing)
        self.ui.purge_settings_button.setEnabled(self._connection.purge_before_writing)
        self.ui.spinBox_write_index.setValue(self._connection.write_index)

    @Slot(str)
    def _select_mutually_exclusive_filter(self, label):
        enabled_filter_type = ResourceFilterModel.FILTER_TYPES[label]
        disabled_filter_types = set(ResourceFilterModel.FILTER_TYPES.values()) - {enabled_filter_type}
        self._toolbox.undo_stack.beginMacro(f"enable {label}s on connection {self._connection.link.name}")
        for disabled_type in disabled_filter_types:
            self._toolbox.undo_stack.push(
                SetConnectionFilterTypeEnabled(self._toolbox.project(), self._connection, disabled_type, False)
            )
        self._toolbox.undo_stack.push(
            SetConnectionFilterTypeEnabled(self._toolbox.project(), self._connection, enabled_filter_type, True)
        )
        self._toolbox.undo_stack.endMacro()

    def set_filter_type_enabled(self, filter_type, enabled):
        """Enables or disables filter type in the tree.

        Args:
            filter_type (str): filter type
            enabled (bool): whether filter type is enabled
        """
        self._set_filter_type_expanded(filter_type, enabled)
        if not enabled:
            return
        filter_type_text = ResourceFilterModel.FILTER_TYPE_TO_TEXT.get(filter_type)
        if filter_type_text is None:
            return
        self.ui.filter_type_combo_box.blockSignals(True)
        self.ui.filter_type_combo_box.setCurrentText(filter_type_text)
        self.ui.filter_type_combo_box.blockSignals(False)

    def _set_filter_type_expanded(self, filter_type, expanded):
        """Expands or collapses filter type branch in the tree.

        Args:
            filter_type (str): filter type
            expanded (bool): True to expand the branch, False to collapse
        """
        action = self.ui.treeView_filters.expand if expanded else self.ui.treeView_filters.collapse
        for item in self._connection.resource_filter_model.filter_type_items(filter_type):
            action(item.index())
