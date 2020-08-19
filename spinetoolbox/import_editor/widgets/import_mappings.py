######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
ImportMappings widget.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtCore import QObject, QItemSelectionModel, Signal, Slot
from ...widgets.custom_delegates import ComboBoxDelegate
from ..commands import CreateMapping, DeleteMapping

MAPPING_CHOICES = ("Constant", "Column", "Row", "Column Header", "Headers", "Table Name", "None")


class ImportMappings(QObject):
    """
    Provides methods for managing Mappings (add, remove, edit, visualize, and so on).
    """

    mapping_selection_changed = Signal(object)
    """Emitted when a new mapping specification is selected from the Mappings list."""
    mapping_data_changed = Signal(object)
    """Emits the new MappingListModel."""
    about_to_undo = Signal(str)
    """Emitted before an undo/redo action."""

    def __init__(self, ui, undo_stack):
        """
        Args:
            ui (QWidget): importer window's UI
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._ui = ui
        self._source_table = None
        self._mappings_model = None
        self._undo_stack = undo_stack
        # initialize interface
        self._ui.table_view_mappings.setItemDelegateForColumn(1, ComboBoxDelegate(MAPPING_CHOICES))

        # connect signals
        self._ui.new_button.clicked.connect(self.new_mapping)
        self._ui.remove_button.clicked.connect(self.delete_selected_mapping)
        self.mapping_selection_changed.connect(self._ui.table_view_mappings.setModel)

    @Slot(str, object)
    def set_mappings_model(self, source_table_name, model):
        """
        Sets new mappings.

        Args:
            source_table_name (str): source table's name
            model (MappingListModel): mapping list model
        """
        self._source_table = source_table_name
        if self._mappings_model is not None:
            self._mappings_model.dataChanged.disconnect(self.data_changed)
        self._mappings_model = model
        self._ui.list_view.setModel(model)
        for specification in self._mappings_model.mapping_specifications:
            specification.about_to_undo.connect(self.focus_on_changing_specification)
        self._ui.list_view.selectionModel().currentChanged.connect(self.change_mapping)
        self._mappings_model.dataChanged.connect(self.data_changed)
        if self._mappings_model.rowCount() > 0:
            self._select_row(0)
        else:
            self._ui.list_view.clearSelection()

    @Slot(str, str)
    def focus_on_changing_specification(self, source_table_name, mapping_name):
        """
        Selects the given mapping from the list and emits about_to_undo.

        Args:
            source_table_name (str): name of the source table
            mapping_name (str): name of the mapping specification
        """
        self.about_to_undo.emit(source_table_name)
        row = self._mappings_model.row_for_mapping(mapping_name)
        index = self._mappings_model.index(row, 0)
        self._ui.list_view.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)

    @Slot()
    def data_changed(self):
        """Emits the mappingDataChanged signal with the currently selected data mappings."""
        m = None
        indexes = self._ui.list_view.selectedIndexes()
        if self._mappings_model and indexes:
            m = self._mappings_model.data_mapping(indexes[0])
        self.mapping_data_changed.emit(m)

    @Slot()
    def new_mapping(self):
        """
        Pushes a CreateMapping command to the undo stack
        """
        if self._mappings_model is None:
            return
        row = self._mappings_model.rowCount()
        command = CreateMapping(self._source_table, self, row)
        self._undo_stack.push(command)

    def create_mapping(self):
        if self._mappings_model is None:
            return
        mapping_name = self._mappings_model.add_mapping()
        specification = self._mappings_model.mapping_specification(mapping_name)
        row = self._mappings_model.rowCount() - 1

        def select_row_slot():
            # We want to select the mapping during undo/redo to show the user where the changes happen.
            self._select_row(row)

        specification.dataChanged.connect(select_row_slot)
        specification.about_to_undo.connect(self.focus_on_changing_specification)
        self._select_row(row)
        return mapping_name

    def insert_mapping_specification(self, source_table_name, name, row, mapping_specification):
        self.about_to_undo.emit(source_table_name)
        if self._mappings_model is None:
            return
        self._mappings_model.insert_mapping_specification(name, row, mapping_specification)
        self._select_row(row)

    @Slot()
    def delete_selected_mapping(self):
        """
        Pushes a DeleteMapping command to the undo stack.
        """
        selection_model = self._ui.list_view.selectionModel()
        if self._mappings_model is None or not selection_model.hasSelection():
            return
        row = selection_model.currentIndex().row()
        mapping_name = self._mappings_model.mapping_name_at(row)
        self._undo_stack.push(DeleteMapping(self._source_table, self, mapping_name, row))

    def delete_mapping(self, source_table_name, name):
        self.about_to_undo.emit(source_table_name)
        if self._mappings_model is None:
            return None
        row = self._mappings_model.row_for_mapping(name)
        if row is None:
            return None
        mapping_specification = self._mappings_model.remove_mapping(row)
        mapping_count = self._mappings_model.rowCount()
        if mapping_count:
            if row == mapping_count:
                self._select_row(mapping_count - 1)
            else:
                self._select_row(row)
        else:
            self._ui.list_view.clearSelection()
        return mapping_specification

    def _select_row(self, row):
        selection_model = self._ui.list_view.selectionModel()
        if selection_model.hasSelection():
            current_row = selection_model.currentIndex().row()
            if row == current_row:
                return
        selection_model.setCurrentIndex(self._mappings_model.index(row, 0), QItemSelectionModel.ClearAndSelect)

    @Slot(object, object)
    def change_mapping(self, selected, deselected):
        row = selected.row()
        index = self._mappings_model.index(row, 0)
        if index.isValid():
            self.mapping_selection_changed.emit(self._mappings_model.data_mapping(index))
        else:
            self.mapping_selection_changed.emit(None)
