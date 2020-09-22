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
:date:   25.11.2019
"""
from contextlib import contextmanager
from PySide2.QtCore import QItemSelectionModel, QModelIndex, Qt, Signal, Slot
from PySide2.QtWidgets import QMessageBox, QWidget
from .parameter_index_settings import IndexSettingsState, ParameterIndexSettings
from ..mvcmodels.indexing_domain_list_model import IndexingDomainListModel
from ..db_utils import scenario_filtered_database_map


class ParameterIndexSettingsWindow(QWidget):
    """A window which shows a list of ParameterIndexSettings widgets, one for each parameter with indexed values."""

    settings_approved = Signal()
    """Emitted when the settings have been approved."""
    settings_rejected = Signal()
    """Emitted when the settings have been rejected."""

    def __init__(self, indexing_settings, set_settings, database_path, scenario, parent):
        """
        Args:
            indexing_settings (dict): a map from parameter name to :class:`IndexingSetting`
            set_settings (SetSettings): export settings
            database_path (str): a database url
            scenario (str): scenario name
            parent (QWidget): a parent widget
        """
        from ..ui.parameter_index_settings_window import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent, f=Qt.Window)
        self._indexing_settings = indexing_settings
        self._set_settings = set_settings
        self._database_mapping = scenario_filtered_database_map(database_path, scenario)
        self._enable_domain_updates = True
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle(f"Gdx Parameter Indexing Settings    -- {database_path} --")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._ui.splitter.setSizes([400, 50])
        self._ui.button_box.accepted.connect(self._collect_and_hide)
        self._ui.button_box.rejected.connect(self._reject_and_close)
        self._additional_domains_model = IndexingDomainListModel(set_settings)
        self._additional_domains_model.domain_renamed.connect(self._update_after_domain_rename)
        self._additional_domains_model.rowsInserted.connect(self._send_domains_to_indexing_widgets)
        self._additional_domains_model.rowsRemoved.connect(self._send_domains_to_indexing_widgets)
        self._ui.additional_domains_list_view.setModel(self._additional_domains_model)
        self._ui.additional_domains_list_view.selectionModel().currentChanged.connect(self._load_additional_domain)
        self._ui.add_domain_button.clicked.connect(self._add_domain)
        self._ui.remove_domain_button.clicked.connect(self._remove_selected_domains)
        self._ui.use_expression_radio_button.clicked.connect(self._use_expression)
        self._ui.expression_edit.textChanged.connect(self._update_expression)
        self._ui.length_spin_box.valueChanged.connect(self._update_length)
        self._ui.extract_from_radio_button.clicked.connect(self._use_extraction)
        self._set_additional_domain_widgets_enabled(False)
        self._ui.extract_from_combo_box.addItems(sorted(indexing_settings.keys()))
        self._ui.extract_from_combo_box.currentTextChanged.connect(self._set_extraction_domain)
        self._settings_widgets = dict()
        self._available_domains = {name: set_settings.records(name) for name in set_settings.domain_names}
        for parameter_name, indexing_setting in indexing_settings.items():
            settings_widget = ParameterIndexSettings(
                parameter_name, indexing_setting, self._available_domains, self._ui.settings_area_contents
            )
            self._ui.settings_area_layout.insertWidget(0, settings_widget)
            self._settings_widgets[parameter_name] = settings_widget
        if not indexing_settings:
            self._ui.widget_stack.setCurrentIndex(1)
            return
        self._ui.widget_stack.setCurrentIndex(0)

    @property
    def indexing_settings(self):
        """indexing settings dictionary"""
        return self._indexing_settings

    def additional_indexing_domains(self):
        return self._additional_domains_model.gather_domains(self._database_mapping)

    def set_domain_updated_enabled(self, enabled):
        """
        Enables or disables updating the indexing settings widgets.

        Args:
            enabled (bool): if True, allow the widgets to update
        """
        self._enable_domain_updates = enabled

    def _switch_additional_domain_widgets_enabled_state(self, using_expression):
        """
        Enabled and disables additional domain widgets.

        Args:
            using_expression (bool): True if expression is used,
                False if record keys are extracted from existing parameter
        """
        self._ui.expression_edit.setEnabled(using_expression)
        self._ui.length_spin_box.setEnabled(using_expression)
        self._ui.extract_from_combo_box.setEnabled(not using_expression)

    def _set_additional_domain_widgets_enabled(self, enabled):
        self._ui.description_edit.setEnabled(enabled)
        self._ui.use_expression_radio_button.setEnabled(enabled)
        self._ui.expression_edit.setEnabled(enabled)
        self._ui.extract_from_radio_button.setEnabled(enabled)
        self._ui.extract_from_combo_box.setEnabled(enabled)

    @Slot(bool)
    def _add_domain(self, _):
        """Creates a new additional domain."""
        self._additional_domains_model.create_new_domain()
        new_current = self._additional_domains_model.index(self._additional_domains_model.rowCount() - 1, 0)
        self._ui.additional_domains_list_view.selectionModel().setCurrentIndex(
            new_current, QItemSelectionModel.ClearAndSelect
        )

    @Slot()
    def _collect_and_hide(self):
        """Collects settings from individual ParameterIndexSettings widgets and hides the window."""
        for parameter_name, settings_widget in self._settings_widgets.items():
            if settings_widget.state != IndexSettingsState.OK:
                self._ui.settings_area.ensureWidgetVisible(settings_widget)
                message = f"Parameter '{parameter_name}' indexing not well-defined."
                QMessageBox.warning(self, "Bad Parameter Indexing", message)
                return
        for parameter_name, settings_widget in self._settings_widgets.items():
            setting = self._indexing_settings[parameter_name]
            setting.indexing_domain_name = settings_widget.indexing_domain_name()
            setting.picking = settings_widget.picking()
        self.settings_approved.emit()
        self.hide()

    @Slot(QModelIndex, QModelIndex)
    def _load_additional_domain(self, current, previous):
        if not previous.isValid():
            self._set_additional_domain_widgets_enabled(True)
        if not current.isValid():
            self._set_additional_domain_widgets_enabled(False)
            return
        with _disable_domain_updates(self):
            domain_proto = self._additional_domains_model.item_at(current.row())
            self._ui.description_edit.setText(domain_proto.description)
            if domain_proto.expression is not None:
                self._ui.use_expression_radio_button.setChecked(True)
                self._ui.expression_edit.setText(domain_proto.expression)
                self._ui.length_spin_box.setValue(domain_proto.length)
                self._ui.extract_from_combo_box.setCurrentIndex(-1)
                self._switch_additional_domain_widgets_enabled_state(True)
            else:
                self._ui.extract_from_radio_button.setChecked(True)
                if domain_proto.extract_from:
                    self._ui.extract_from_combo_box.setCurrentText(domain_proto.extract_from)
                else:
                    self._ui.extract_from_combo_box.setCurrentIndex(-1)
                self._ui.expression_edit.clear()
                self._switch_additional_domain_widgets_enabled_state(False)

    @Slot()
    def _reject_and_close(self):
        self.close()

    @Slot(bool)
    def _remove_selected_domains(self, _):
        selection_model = self._ui.additional_domains_list_view.selectionModel()
        if not selection_model.hasSelection():
            return
        rows = [index.row() for index in selection_model.selectedRows()]
        self._additional_domains_model.remove_rows(rows)
        current = selection_model.currentIndex()
        if current.isValid():
            selection_model.select(current, QItemSelectionModel.ClearAndSelect)

    @Slot(QModelIndex, int, int)
    def _send_domains_to_indexing_widgets(self, parent, first, last):
        """Updates the available domains combo boxes in indexing widgets."""
        domains = {
            name: self._set_settings.records(name)
            for name in self._set_settings.domain_names
            if not self._set_settings.metadata(name).is_additional()
        }
        domains.update(self._additional_domains_model.gather_domains(self._database_mapping))
        for widget in self._settings_widgets.values():
            widget.set_domains(domains)

    @Slot(str, str)
    def _update_after_domain_rename(self, old_name, new_name):
        """
        Propagates changes in domain names to widgets.

        Args:
            old_name (str): domain's previous name
            new_name (str): domain's current name
        """
        self._available_domains[new_name] = self._available_domains.pop(old_name)
        for widget in self._settings_widgets.values():
            widget.update_domain_name(old_name, new_name)

    @Slot(str)
    def _update_expression(self, expression):
        """
        Updates the domain's record key expression.

        Args:
            expression (str): new expression
        """
        list_index = self._ui.additional_domains_list_view.currentIndex()
        if not list_index.isValid() or not self._enable_domain_updates:
            return
        item = self._additional_domains_model.item_at(list_index.row())
        item.expression = expression
        records = item.records(self._database_mapping)
        self._available_domains[item.name] = records
        for widget in self._settings_widgets.values():
            widget.update_records(item.name)

    @Slot(int)
    def _update_length(self, length):
        """
        Updates the number of additional domain's records.

        Args:
            length (int): new record count
        """
        list_index = self._ui.additional_domains_list_view.currentIndex()
        if not list_index.isValid() or not self._enable_domain_updates:
            return
        item = self._additional_domains_model.item_at(list_index.row())
        item.length = length
        records = item.records(self._database_mapping)
        self._available_domains[item.name] = records
        for widget in self._settings_widgets.values():
            widget.update_records(item.name)

    @Slot(bool)
    def _use_expression(self, _):
        self._switch_additional_domain_widgets_enabled_state(True)
        list_index = self._ui.additional_domains_list_view.currentIndex()
        if not list_index.isValid():
            return
        item = self._additional_domains_model.item_at(list_index.row())
        item.expression = self._ui.expression_edit.text()
        item.length = self._ui.length_spin_box.value()
        item.extract_from = None
        records = item.records(self._database_mapping)
        self._available_domains[item.name] = records
        for widget in self._settings_widgets.values():
            widget.update_records(item.name)

    @Slot(bool)
    def _use_extraction(self, _):
        self._switch_additional_domain_widgets_enabled_state(False)
        domain_name = self._ui.extract_from_combo_box.currentText()
        self._set_extraction_domain(domain_name)

    @Slot(str)
    def _set_extraction_domain(self, domain_name):
        """
        Sets the domain from which domain's records are extracted.

        Args:
            domain_name (str): domain name
        """
        list_index = self._ui.additional_domains_list_view.currentIndex()
        if not domain_name or not list_index.isValid():
            return
        item = self._additional_domains_model.item_at(list_index.row())
        item.expression = None
        item.extract_from = domain_name
        records = item.records(self._database_mapping)
        self._available_domains[item.name] = records
        for widget in self._settings_widgets.values():
            widget.update_records(item.name)

    def closeEvent(self, event):
        """Handles the close event."""
        super().closeEvent(event)
        self._database_mapping.connection.close()
        self.settings_rejected.emit()


@contextmanager
def _disable_domain_updates(window):
    """
    A context manager which disables updates on the indexing settings widgets.

    Args:
        window (ParameterIndexSettingsWindow): settings window
    """
    window.set_domain_updated_enabled(False)
    try:
        yield None
    finally:
        window.set_domain_updated_enabled(True)
