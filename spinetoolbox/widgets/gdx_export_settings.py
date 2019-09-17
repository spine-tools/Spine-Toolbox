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
Gdx Export item's settings window.

:author: A. Soininen (VTT)
:date:   9.9.2019
"""

from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, Slot
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QMainWindow, QWidget
from ui.gdx_export_settings import Ui_Form


def _move_selected_elements_by(list_view, delta):
    selection_model = list_view.selectionModel()
    selected_rows = sorted(selection_model.selectedRows())
    if not selected_rows:
        return
    first_row = selected_rows[0].row()
    contiguous_selections = [(first_row, 1)]
    current_contiguous_chunk = contiguous_selections[0]
    for row in selected_rows[1:]:
        if row == current_contiguous_chunk[0] + 1:
            current_contiguous_chunk[1] += 1
        else:
            contiguous_selections.append((row, 1))
            current_contiguous_chunk = contiguous_selections[-1]
    model = list_view.model()
    for chunk in contiguous_selections:
        model.moveRows(QModelIndex(), chunk[0], chunk[1], QModelIndex(), chunk[0] + delta)


class GdxExportSettings(QMainWindow):
    def __init__(self, settings, parent):
        super().__init__(parent)
        central_widget = QWidget()
        self._central_widget_ui = Ui_Form()
        self._central_widget_ui.setupUi(central_widget)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("Gdx Export settings")
        self._central_widget_ui.button_box.accepted.connect(self.close)
        self._central_widget_ui.button_box.rejected.connect(self.close)
        self._central_widget_ui.set_move_up_button.clicked.connect(self.__move_sets_up)
        self._central_widget_ui.set_move_down_button.clicked.connect(self.__move_sets_down)
        self._central_widget_ui.set_as_global_parameters_object_class_button.clicked.connect(self.__set_selected_set_as_global_parameters_object_class)
        self._central_widget_ui.record_move_up_button.clicked.connect(self.__move_records_up)
        self._central_widget_ui.record_move_down_button.clicked.connect(self.__move_records_down)
        self._central_widget_ui.global_parameters_object_class_line_edit.textChanged.connect(self.__update_global_parameters_object_class)
        self._settings = settings
        set_list_model = GAMSSetListModel(settings)
        self._central_widget_ui.set_list_view.setModel(set_list_model)
        record_list_model = GAMSRecordListModel()
        self._central_widget_ui.record_list_view.setModel(record_list_model)
        self._central_widget_ui.set_list_view.selectionModel().selectionChanged.connect(self.__populate_set_contents)
        self._central_widget_ui.set_list_view.selectionModel().currentChanged.connect(self.__update_as_global_button_enabled_state)

    @property
    def settings(self):
        return self._settings

    @property
    def button_box(self):
        return self._central_widget_ui.button_box

    @Slot(bool)
    def __move_sets_up(self, checked=False):
        _move_selected_elements_by(self._central_widget_ui.set_list_view, -1)

    @Slot(bool)
    def __move_sets_down(self, checked=False):
        _move_selected_elements_by(self._central_widget_ui.set_list_view, 1)

    @Slot(bool)
    def __move_records_up(self, checked=False):
        _move_selected_elements_by(self._central_widget_ui.record_list_view, -1)

    @Slot(bool)
    def __move_records_down(self, checked=False):
        _move_selected_elements_by(self._central_widget_ui.record_list_view, 1)

    @Slot("QModelIndex", "QModelIndex")
    def __update_as_global_button_enabled_state(self, current, previous):
        model = current.model()
        is_previous_domain = model.is_domain(previous)
        is_current_domain = model.is_domain(current)
        if is_current_domain != is_previous_domain:
            self._central_widget_ui.set_as_global_parameters_object_class_button.setEnabled(is_current_domain)

    @Slot(bool)
    def __set_selected_set_as_global_parameters_object_class(self, checked=False):
        selection_model = self._central_widget_ui.set_list_view.selectionModel()
        current_index = selection_model.currentIndex()
        model = current_index.model()
        if not current_index.isValid() or not model.is_domain(current_index):
            return
        set_name = current_index.data()
        self._central_widget_ui.global_parameters_object_class_line_edit.setText(set_name)
        model.setData(current_index, Qt.Unchecked, Qt.CheckStateRole)

    @Slot(str)
    def __update_global_parameters_object_class(self, text):
        self._settings.global_parameters_domain_name = text

    @Slot("QItemSelection", "QItemSelection")
    def __populate_set_contents(self, selected, deselected):
        selected_indexes = selected.indexes()
        if not selected_indexes:
            return
        set_model = self._central_widget_ui.set_list_view.model()
        selected_set_name = set_model.data(selected_indexes[0])
        records = self._settings.records(selected_set_name)
        record_model = self._central_widget_ui.record_list_view.model()
        record_model.reset(records)


def move_list_elements(originals, first, last, target):
    trashable = list(originals)
    elements_to_move = list(originals[first:last + 1])
    del trashable[first:last + 1]
    elements_that_come_before = trashable[:target]
    elements_that_come_after = trashable[target:]
    brave_new_list = elements_that_come_before + elements_to_move + elements_that_come_after
    return brave_new_list


class GAMSSetListModel(QAbstractListModel):
    def __init__(self, settings):
        super().__init__()
        self._settings = settings

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.column() != 0 or index.row() >= self.rowCount():
            return None
        row = index.row()
        domain_count = len(self._settings.domain_names)
        if role == Qt.DisplayRole:
            if row < domain_count:
                return self._settings.domain_names[row]
            return self._settings.set_names[row - domain_count]
        if role == Qt.BackgroundRole:
            if row < domain_count:
                return QColor(Qt.lightGray)
            return None
        if role == Qt.CheckStateRole:
            if row < domain_count:
                checked = self._settings.domain_exportable_flags[row]
            else:
                checked = self._settings.set_exportable_flags[row - domain_count]
            return Qt.Checked if checked else Qt.Unchecked
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            return ''
        return section + 1

    def is_domain(self, index):
        if not index.isValid():
            return False
        return index.row() < len(self._settings.domain_names)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        domain_count = len(self._settings.domain_names)
        # Cannot move domains to ordinary sets and vice versa.
        if sourceRow < domain_count and last_source_row >= domain_count:
            return False
        if sourceRow < domain_count and destinationChild >= domain_count:
            return False
        if sourceRow >= domain_count and destinationChild < domain_count:
            return False
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        if sourceRow < domain_count:
            names = self._settings.domain_names
            export_flags = self._settings.domain_exportable_flags
        else:
            names = self._settings.set_names
            export_flags = self._settings.set_exportable_flags
            sourceRow -= domain_count
            last_source_row -= domain_count
            destinationChild -= domain_count
        names[:] = move_list_elements(names, sourceRow, last_source_row, destinationChild)
        export_flags[:] = move_list_elements(export_flags, sourceRow, last_source_row, destinationChild)
        self.endMoveRows()
        return True

    def rowCount(self, parent=QModelIndex()):
        return len(self._settings.domain_names) + len(self._settings.set_names)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.CheckStateRole:
            return False
        row = index.row()
        domain_count = len(self._settings.domain_names)
        if row < domain_count:
            self._settings.domain_exportable_flags[row] = value != Qt.Unchecked
        else:
            self._settings.set_exportable_flags[row - domain_count] = value != Qt.Unchecked
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])
        return True


class GAMSRecordListModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._records = list()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._records[index.row()]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            return ''
        return section + 1

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        self._records[:] = move_list_elements(self._records, sourceRow, last_source_row, destinationChild)
        self.endMoveRows()
        return True

    def reset(self, records):
        self.beginResetModel()
        self._records = records
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._records)
