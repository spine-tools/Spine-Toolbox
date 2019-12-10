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

import enum
from PySide2.QtCore import QAbstractTableModel, QItemSelection, QItemSelectionModel, QModelIndex, Qt, Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.spine_io.exporters import gdx


class IndexSettingsState(enum.Enum):
    OK = enum.auto()
    DOMAIN_MISSING_INDEXES = enum.auto()
    DOMAIN_NAME_MISSING = enum.auto()
    DOMAIN_NAME_CLASH = enum.auto()


class ParameterIndexSettings(QWidget):
    def __init__(self, parameter_name, indexing_setting, available_existing_domains, parent):
        from ..ui.parameter_index_settings import Ui_Form

        super().__init__(parent)
        self._indexing_setting = indexing_setting
        self._state = IndexSettingsState.OK
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.box.setTitle(parameter_name)
        self._indexing_table_model = _IndexingTableModel(indexing_setting.parameter)
        self._ui.index_table_view.setModel(self._indexing_table_model)
        self._ui.index_table_view.selectionModel().selectionChanged.connect(self._update_model_to_selection)
        self._available_domains = available_existing_domains
        for domain_name in available_existing_domains:
            self._ui.existing_domains_combo.insertItem(0, domain_name)
        self._ui.existing_domains_combo.setCurrentIndex(0)
        self._ui.existing_domains_combo.activated.connect(self._existing_domain_changed)
        self._ui.use_existing_domain_radio_button.toggled.connect(self._set_enabled_use_existing_domain_widgets)
        self._ui.create_domain_radio_button.toggled.connect(self._set_enabled_create_domain_widgets)
        self._set_enabled_use_existing_domain_widgets(True)
        self._set_enabled_create_domain_widgets(False)
        self._ui.pick_expression_edit.textChanged.connect(self._update_index_list_selection)
        self._ui.generator_expression_edit.textChanged.connect(self._generate_index)
        self._ui.extract_indexes_button.clicked.connect(self._extract_index_from_parameter)
        self._ui.domain_name_edit.textEdited.connect(self._domain_name_changed)
        self._ui.move_domain_left_button.clicked.connect(self._move_indexing_domain_left)
        self._ui.move_domain_right_button.clicked.connect(self._move_indexing_domain_right)
        self._check_state()

    @property
    def new_domain_name(self):
        return str(self._ui.domain_name_edit.text())

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state
        if self._state == IndexSettingsState.DOMAIN_MISSING_INDEXES:
            self.error_message("Not enough selected indexes to index all values.")
        elif self._state == IndexSettingsState.DOMAIN_NAME_MISSING:
            self.error_message("Domain name missing for the new index domain.")
        elif self._state == IndexSettingsState.DOMAIN_NAME_CLASH:
            self.error_message("Domain name already exists. Choose another name.")
        elif self._state == IndexSettingsState.OK:
            self.notification_message("Parameter successfully indexed.")

    def indexing_domain(self):
        new_domain = None
        if self._ui.use_existing_domain_radio_button.isChecked():
            domain_name = self._ui.existing_domains_combo.currentText()
            base_domain = gdx.Set(domain_name)
            base_domain.records = [gdx.Record((keys,)) for keys in self._available_domains[domain_name]]
        else:
            indexes = self._indexing_table_model.indexes
            domain_name = self._ui.domain_name_edit.text()
            domain_description = self._ui.domain_description_edit.text()
            base_domain = gdx.Set(domain_name, domain_description)
            base_domain.records += [gdx.Record((index,)) for index in indexes]
            new_domain = base_domain
        pick_list = self._indexing_table_model.index_selection
        indexing_domain = gdx.IndexingDomain(base_domain, pick_list)
        return indexing_domain, new_domain

    def serialize(self):
        serialized = dict()
        use_existing_domain = self._ui.use_existing_domain_radio_button.isChecked()
        serialized["use_existing_domain"] = use_existing_domain
        if use_existing_domain:
            serialized["domain_name"] = str(self._ui.existing_domains_combo.currentText())
            pick_expression = str(self._ui.pick_expression_edit.text())
            if pick_expression:
                serialized["pick_expression"] = pick_expression
            else:
                serialized["pick_indexes"] = self._indexing_table_model.index_selection
        else:
            serialized["domain_name"] = str(self._ui.domain_name_edit.text())
            serialized["domain_description"] = str(self._ui.domain_description_edit.text())
            generator_expression = str(self._ui.generator_expression_edit.text())
            if generator_expression:
                serialized["generator_expression"] = generator_expression
            else:
                serialized["indexes"] = self._indexing_table_model.indexes
            serialized["pick_indexes"] = self._indexing_table_model.index_selection

    def deserialize(self, serialized):
        def select_pick_indexes(pick_indexes):
            select = QItemSelection()
            for row, selected in enumerate(pick_indexes):
                if selected:
                    top_left = self._indexing_table_model.index(row, 0)
                    bottom_right = self._indexing_table_model.index(row, 1)
                    select.select(top_left, bottom_right)
            self._ui.index_table_view.selectionModel().select(select, Qt.ClearAndSelect)

        if serialized["use_existing_domain"]:
            self._ui.existing_domains_combo.setCurrentText(serialized["domain_name"])
            pick_expression = serialized.get(["pick_expression"], None)
            if pick_expression is not None:
                self._ui.pick_expression_edit.setText(pick_expression)
            else:
                select_pick_indexes(serialized["pick_indexes"])
        else:
            self._ui.domain_name_edit.setText(serialized["domain_name"])
            self._ui.domain_description_edit.setText(serialized["domain_description"])
            generator_expression = serialized.get("generator_expression", None)
            if generator_expression is not None:
                self._ui.generator_expression_edit.setText(generator_expression)
            else:
                self._indexing_table_model.set_indexes(serialized["indexes"])
            select_pick_indexes(serialized["pick_indexes"])

    def notification_message(self, message):
        self._ui.message_label.setText(message)

    def warning_message(self, message):
        yellow_message = "<span style='color:#b89e00;white-space: pre-wrap;'>" + message + "</span>"
        self._ui.message_label.setText(yellow_message)

    def error_message(self, message):
        red_message = "<span style='color:#ff3333;white-space: pre-wrap;'>" + message + "</span>"
        self._ui.message_label.setText(red_message)

    def _check_state(self):
        mapped_values_count = self._indexing_table_model.mapped_values_count()
        if self._check_errors(mapped_values_count):
            return
        if self._check_warnings(mapped_values_count):
            return
        self.state = IndexSettingsState.OK

    def _check_errors(self, mapped_values_count):
        if mapped_values_count < 0:
            self.state = IndexSettingsState.DOMAIN_MISSING_INDEXES
            return True
        if self._ui.create_domain_radio_button.isChecked() and not self._ui.domain_name_edit.text():
            self.state = IndexSettingsState.DOMAIN_NAME_MISSING
            return True
        return False

    def _check_warnings(self, mapped_values_count):
        if mapped_values_count > 0:
            self._state = IndexSettingsState.OK
            self.warning_message("Too many indexes selected. The excess indexes will not be used.")
            return True
        return False

    def _update_indexing_domains_label(self):
        parameter = self._indexing_setting.parameter
        index_position = self._indexing_setting.index_position
        if self._ui.use_existing_domain_radio_button.isChecked():
            domain_name = self._ui.existing_domains_combo.currentText()
        else:
            domain_name = self._ui.domain_name_edit.text()
        name = "<b>{}</b>".format(domain_name if domain_name else "unnamed")
        label = (
            "("
            + ", ".join(parameter.domain_names[:index_position] + [name] + parameter.domain_names[index_position:])
            + ")"
        )
        self._ui.indexing_domains_label.setText(label)

    @Slot(str)
    def _domain_name_changed(self, text):
        if text and self._state in (IndexSettingsState.DOMAIN_NAME_MISSING, IndexSettingsState.DOMAIN_NAME_CLASH):
            self._check_state()
        elif not text and self._state == IndexSettingsState.OK:
            self._check_state()
        self._update_indexing_domains_label()

    @Slot(bool)
    def _set_enabled_use_existing_domain_widgets(self, enabled):
        self._ui.existing_domains_combo.setEnabled(enabled)
        self._ui.pick_expression_edit.setEnabled(enabled)
        self._ui.pick_expression_label.setEnabled(enabled)
        if enabled:
            self._existing_domain_changed(self._ui.existing_domains_combo.currentIndex())
            self._update_index_list_selection(self._ui.pick_expression_edit.text(), False)
        self._update_indexing_domains_label()

    @Slot(bool)
    def _set_enabled_create_domain_widgets(self, enabled):
        self._ui.domain_name_label.setEnabled(enabled)
        self._ui.domain_name_edit.setEnabled(enabled)
        self._ui.domain_description_label.setEnabled(enabled)
        self._ui.domain_description_edit.setEnabled(enabled)
        self._ui.generator_expression_label.setEnabled(enabled)
        self._ui.generator_expression_edit.setEnabled(enabled)
        self._ui.extract_indexes_button.setEnabled(enabled)
        if enabled:
            expression = self._ui.generator_expression_edit.text()
            if expression:
                self._generate_index(expression)
            else:
                self._indexing_table_model.clear()
                self._check_state()

    @Slot(int)
    def _existing_domain_changed(self, index):
        selected_domain_name = self._ui.existing_domains_combo.itemText(index)
        self._indexing_table_model.set_indexes(self._available_domains[selected_domain_name])
        self._ui.index_table_view.selectAll()
        self._update_indexing_domains_label()

    @Slot("QString")
    def _update_index_list_selection(self, expression, clear_selection_if_expression_empty=True):
        if not expression:
            if clear_selection_if_expression_empty:
                self._ui.index_table_view.clearSelection()
            return
        get_index = self._indexing_table_model.index
        selection = QItemSelection()
        selected_domain_name = self._ui.existing_domains_combo.currentText()
        try:
            for index in range(len(self._available_domains[selected_domain_name])):
                if eval(expression, {}, {"i": index + 1}):  # pylint: disable=eval-used
                    selected_top_left = get_index(index, 0)
                    selected_bottom_right = get_index(index, 1)
                    selection.select(selected_top_left, selected_bottom_right)
        except (AttributeError, NameError, SyntaxError):
            return
        selection_model = self._ui.index_table_view.selectionModel()
        selection_model.select(selection, QItemSelectionModel.ClearAndSelect)

    @Slot("QItemSelection", "QItemSelection")
    def _update_model_to_selection(self, selected, deselected):
        self._indexing_table_model.selection_changed(selected, deselected)
        self._check_state()

    @Slot(str)
    def _generate_index(self, expression):
        indexes = list()
        try:
            for index in range(len(self._parameter)):
                indexes.append(str(eval(expression, {}, {"i": index + 1})))  # pylint: disable=eval-used
        except (AttributeError, NameError, SyntaxError):
            return
        self._indexing_table_model.set_indexes(indexes)
        self._ui.index_table_view.selectAll()
        self._check_state()

    @Slot(bool)
    def _extract_index_from_parameter(self, _=True):
        indexes = [str(index) for index in self._indexing_setting.parameter.values[0].indexes]
        self._indexing_table_model.set_indexes(indexes)
        self._ui.index_table_view.selectAll()

    @Slot(bool)
    def _move_indexing_domain_left(self, _):
        if self._indexing_setting.index_position > 0:
            self._indexing_setting.index_position -= 1
            self._update_indexing_domains_label()

    @Slot(bool)
    def _move_indexing_domain_right(self, _):
        if self._indexing_setting.index_position < len(self._indexing_setting.parameter.domain_names):
            self._indexing_setting.index_position += 1
            self._update_indexing_domains_label()


class _IndexingTableModel(QAbstractTableModel):
    def __init__(self, parameter):
        super().__init__()
        self._indexes = list()
        self._parameter_values = list()
        self._parameter_nonexpanded_indexes = list()
        for value_index, parameter_value in zip(parameter.indexes, parameter.values):
            self._parameter_nonexpanded_indexes.append(value_index)
            self._parameter_values.append(parameter_value)
        self._selected = list()
        self._values = len(parameter.values) * [list()]

    @property
    def indexes(self):
        return self._indexes

    @property
    def index_selection(self):
        return self._selected

    def clear(self):
        self.beginResetModel()
        self._indexes = list()
        self._selected = list()
        self._values = len(self._parameter_values) * [list()]
        self.endResetModel()

    def columnCount(self, parent=QModelIndex()):
        return len(self._parameter_values) + 1

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.ToolTipRole) or not index.isValid():
            return None
        row = index.row()
        if index.column() == 0:
            return self._indexes[row]
        column = index.column() - 1
        value = self._values[column][row]
        return str(value) if value is not None else None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        if section == 0:
            return "Index"
        return ", ".join(self._parameter_nonexpanded_indexes[section - 1])

    def mapped_values_count(self):
        count = 0
        for selected in self._selected:
            if selected:
                count += 1
        return count - len(self._parameter_values[0].values) if self._parameter_values else 0

    def rowCount(self, parent=QModelIndex()):
        return len(self._indexes)

    def selection_changed(self, selected, deselected):
        selected_indexes = selected.indexes()
        deselected_indexes = deselected.indexes()
        min_changed_row = len(self._indexes)
        for i in selected_indexes:
            if i.column() != 1:
                continue
            row = i.row()
            self._selected[row] = True
            min_changed_row = min(min_changed_row, row)
        for i in deselected_indexes:
            if i.column() != 1:
                continue
            row = i.row()
            self._selected[row] = False
            min_changed_row = min(min_changed_row, row)
        for i, parameter_value in enumerate(self._parameter_values):
            self._values[i] = len(self._indexes) * [None]
            value_index = 0
            for j, is_selected in enumerate(self._selected):
                if is_selected and value_index < len(parameter_value):
                    self._values[i][j] = parameter_value.values[value_index]
                    value_index += 1
        top_left = self.index(min_changed_row, 1)
        bottom_right = self.index(len(self._indexes), len(self._parameter_values))
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    def set_indexes(self, indexes):
        self.beginResetModel()
        self._indexes = indexes
        self._selected = len(indexes) * [False]
        self._values = len(self._parameter_values) * [len(indexes) * [None]]
        self.endResetModel()
