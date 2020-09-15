######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Parameter indexing settings window for .gdx export.

:author: A. Soininen (VTT)
:date:   26.11.2019
"""
from contextlib import contextmanager
import enum
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.spine_io.exporters import gdx
from ..mvcmodels.indexing_table_model import IndexingTableModel


class IndexSettingsState(enum.Enum):
    """An enumeration indicating the state of the settings window."""

    OK = enum.auto()
    DOMAIN_MISSING_INDEXES = enum.auto()


class ParameterIndexSettings(QWidget):
    """A widget showing setting for a parameter with indexed values."""

    def __init__(self, parameter_name, indexing_setting, available_domains, parent):
        """
        Args:
            parameter_name (str): parameter's name
            indexing_setting (IndexingSetting): indexing settings for the parameter
            available_domains (dict): a dict from existing domain name to :class:`Records`
            parent (QWidget, optional): a parent widget
        """
        from ..ui.parameter_index_settings import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._indexing_setting = indexing_setting
        self._state = IndexSettingsState.OK
        self._monitor_domains_combo_box = True
        self._using_pick_expression = False
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.box.setTitle(parameter_name)
        self._indexing_table_model = IndexingTableModel(indexing_setting.parameter)
        self._ui.index_table_view.setModel(self._indexing_table_model)
        self._available_domains = available_domains
        self._ui.domains_combo.addItems(sorted(available_domains.keys()))
        self._ui.domains_combo.currentTextChanged.connect(self._change_domain)
        self._ui.pick_expression_edit.textChanged.connect(self._update_index_list_selection)
        self._ui.move_domain_left_button.clicked.connect(self._move_indexing_domain_left)
        self._ui.move_domain_right_button.clicked.connect(self._move_indexing_domain_right)
        indexing_domain_name = indexing_setting.indexing_domain_name
        if indexing_domain_name is None and available_domains:
            indexing_domain_name = next(iter(available_domains))
        if indexing_domain_name is not None:
            if self._ui.domains_combo.currentText() != indexing_domain_name:
                self._ui.domains_combo.setCurrentText(indexing_domain_name)
            else:
                self._change_domain(indexing_domain_name)
            picking = indexing_setting.picking
            if isinstance(picking, gdx.GeneratedPicking):
                self._ui.pick_expression_edit.setText(picking.expression)
            else:
                self._indexing_table_model.set_picking(picking)
        self._check_state()
        self._indexing_table_model.selection_changed.connect(self._check_state)
        self._indexing_table_model.manual_selection.connect(self._clear_pick_expression_silently)

    @property
    def state(self):
        """widget's state"""
        return self._state

    @state.setter
    def state(self, new_state):
        """Sets the state of the widget and possibly shows an error indicator."""
        self._state = new_state
        if self._state == IndexSettingsState.DOMAIN_MISSING_INDEXES:
            self.error_message("Not enough selected indexes to index all values.")
        elif self._state == IndexSettingsState.OK:
            self.notification_message("Parameter successfully indexed.")

    def indexing_domain_name(self):
        """
        Returns the selected indexing domain's name

        Returns:
            str: domain name
        """
        return self._ui.domains_combo.currentText()

    def picking(self):
        """
        Returns picking.

        Returns:
            Picking: picking
        """
        if self._using_pick_expression:
            return gdx.GeneratedPicking(self._ui.pick_expression_edit.text())
        return self._indexing_table_model.get_picking()

    def set_domains(self, domains):
        """
        Sets new domains and record keys.

        Args:
            domains (dict): mapping from domain name to records
        """
        self._available_domains = domains
        current = self._ui.domains_combo.currentText()
        with _freely_update_domains_combo(self):
            self._ui.domains_combo.clear()
            self._ui.domains_combo.addItems(sorted(domains.keys()))
        if current in domains:
            self._ui.domains_combo.setCurrentText(current)
        else:
            self._ui.domains_combo.setCurrentIndex(-1)

    def set_domains_combo_monitoring_enabled(self, enabled):
        """
        Enables or disables monitoring of current text in domains combo box.

        Args:
            enabled (bool): True enables monitoring, False disables
        """
        self._monitor_domains_combo_box = enabled

    def update_domain_name(self, old_name, new_name):
        """
        Renames a domain.

        Args:
            old_name (str): previous name
            new_name (str): new name
        """
        index = self._ui.domains_combo.findText(old_name)
        self._ui.domains_combo.setItemText(index, new_name)

    def update_records(self, domain_name):
        """
        Updates existing domain's records.

        Args:
            domain_name (str): domain's name
        """
        if domain_name == self._ui.domains_combo.currentText():
            self._indexing_table_model.set_records(self._available_domains[domain_name])

    def notification_message(self, message):
        """Shows a notification message on the widget."""
        self._ui.message_label.setText(message)

    def warning_message(self, message):
        """Shows a warning message on the widget."""
        yellow_message = "<span style='color:#b89e00;white-space: pre-wrap;'>" + message + "</span>"
        self._ui.message_label.setText(yellow_message)

    def error_message(self, message):
        """Shows an error message on the widget."""
        red_message = "<span style='color:#ff3333;white-space: pre-wrap;'>" + message + "</span>"
        self._ui.message_label.setText(red_message)

    @Slot()
    def _check_state(self):
        """Updated the widget's state."""
        mapped_values_balance = self._indexing_table_model.mapped_values_balance()
        if self._check_errors(mapped_values_balance):
            return
        if self._check_warnings(mapped_values_balance):
            return
        self.state = IndexSettingsState.OK

    def _check_errors(self, mapped_values_balance):
        """Checks if the parameter is correctly indexed."""
        if mapped_values_balance < 0:
            self.state = IndexSettingsState.DOMAIN_MISSING_INDEXES
            return True
        return False

    def _check_warnings(self, mapped_values_balance):
        """Checks if there are non-fatal issues with parameter indexing."""
        if mapped_values_balance > 0:
            self._state = IndexSettingsState.OK
            self.warning_message("Too many indexes selected. The excess indexes will not be used.")
            return True
        return False

    def _update_indexing_domains_name(self):
        """Updates the model's header and the label showing the indexing domains."""
        parameter = self._indexing_setting.parameter
        index_position = self._indexing_setting.index_position
        domain_name = self._ui.domains_combo.currentText()
        self._indexing_table_model.set_index_name(domain_name)
        name = "<b>{}</b>".format(domain_name if domain_name else "unnamed")
        label = (
            "("
            + ", ".join(parameter.domain_names[:index_position] + [name] + parameter.domain_names[index_position:])
            + ")"
        )
        self._ui.indexing_domains_label.setText(label)

    @Slot()
    def _clear_pick_expression_silently(self):
        """Clears the pick expression line edit."""
        self._ui.pick_expression_edit.textChanged.disconnect(self._update_index_list_selection)
        self._ui.pick_expression_edit.clear()
        self._using_pick_expression = False
        self._ui.pick_expression_edit.textChanged.connect(self._update_index_list_selection)

    @Slot(str)
    def _change_domain(self, domain_name):
        """Change the domain used on the table."""
        if not self._monitor_domains_combo_box:
            return
        if domain_name:
            self._indexing_table_model.set_records(self._available_domains[domain_name])
        else:
            self._indexing_table_model.set_records(gdx.LiteralRecords([]))
        self._update_indexing_domains_name()

    @Slot(str)
    def _update_index_list_selection(self, expression):
        """Updates selection according to changed selection expression."""
        if not expression:
            self._indexing_table_model.select_all()
            self._using_pick_expression = False
            return
        self._indexing_table_model.set_picking(gdx.GeneratedPicking(expression))
        self._using_pick_expression = True

    @Slot(bool)
    def _move_indexing_domain_left(self, _):
        """Moves the indexing domain name left on the indexing label."""
        if self._indexing_setting.index_position > 0:
            self._indexing_setting.index_position -= 1
            self._update_indexing_domains_name()

    @Slot(bool)
    def _move_indexing_domain_right(self, _):
        """Moves the indexing domain name right on the indexing label."""
        if self._indexing_setting.index_position < len(self._indexing_setting.parameter.domain_names):
            self._indexing_setting.index_position += 1
            self._update_indexing_domains_name()


@contextmanager
def _freely_update_domains_combo(widget):
    """
    A context manager which temporarily disables the monitoring of current text changes in domains combo box.

    Args:
        widget (ParameterIndexSettings): settings widget
    """
    widget.set_domains_combo_monitoring_enabled(False)
    try:
        yield None
    finally:
        widget.set_domains_combo_monitoring_enabled(True)
