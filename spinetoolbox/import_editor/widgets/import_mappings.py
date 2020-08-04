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

from PySide2.QtCore import QObject, Signal, Slot
from ...widgets.custom_delegates import ComboBoxDelegate

MAPPING_CHOICES = ("Constant", "Column", "Row", "Column Header", "Headers", "Table Name", "None")


class ImportMappings(QObject):
    """
    Provides methods for managing Mappings (add, remove, edit, visualize, and so on).
    """

    mapping_changed = Signal(object)
    """Emitted when a new mapping MappingSpecModel is selected from the Mappings list."""
    mapping_data_changed = Signal(object)
    """Emits the new MappingListModel."""

    def __init__(self, ui):
        """
        Args:
            ui (QWidget): importer window's UI
        """
        super().__init__()
        self._ui = ui
        self._mappings_model = None
        self._select_handle = None
        # initialize interface
        self._ui.table_view_mappings.setItemDelegateForColumn(1, ComboBoxDelegate(None, MAPPING_CHOICES))

        # connect signals
        self._ui.new_button.clicked.connect(self.new_mapping)
        self._ui.remove_button.clicked.connect(self.delete_selected_mapping)
        self.mapping_changed.connect(self._ui.table_view_mappings.setModel)

    @Slot(object)
    def set_mappings_model(self, model):
        """
        Sets new model
        """
        if self._select_handle and self._ui.list_view.selectionModel():
            self._ui.list_view.selectionModel().selectionChanged.disconnect(self.select_mapping)
            self._select_handle = None
        if self._mappings_model:
            self._mappings_model.dataChanged.disconnect(self.data_changed)
        self._mappings_model = model
        self._ui.list_view.setModel(model)
        self._select_handle = self._ui.list_view.selectionModel().selectionChanged.connect(self.select_mapping)
        self._mappings_model.dataChanged.connect(self.data_changed)
        if self._mappings_model.rowCount() > 0:
            self._ui.list_view.setCurrentIndex(self._mappings_model.index(0, 0))
        else:
            self._ui.list_view.clearSelection()

    @Slot()
    def data_changed(self):
        """Emits the mappingDataChanged signal with the currently selected data mappings."""
        m = None
        indexes = self._ui.list_view.selectedIndexes()
        if self._mappings_model and indexes:
            m = self._mappings_model.data_mapping(indexes()[0])
        self.mapping_data_changed.emit(m)

    @Slot()
    def new_mapping(self):
        """
        Adds new empty mapping
        """
        if self._mappings_model:
            self._mappings_model.add_mapping()
            if not self._ui.list_view.selectedIndexes():
                # if no item is selected, select the first item
                self._ui.list_view.setCurrentIndex(self._mappings_model.index(0, 0))

    @Slot()
    def delete_selected_mapping(self):
        """
        deletes selected mapping
        """
        if self._mappings_model is not None:
            # get selected mapping in list
            indexes = self._ui.list_view.selectedIndexes()
            if indexes:
                self._mappings_model.remove_mapping(indexes[0].row())
                if self._mappings_model.rowCount() > 0:
                    # select the first item
                    self._ui.list_view.setCurrentIndex(self._mappings_model.index(0, 0))
                    self.select_mapping(self._ui.list_view.selectionModel().selection())
                else:
                    # no items clear selection so select_mapping is called
                    self._ui.list_view.clearSelection()

    @Slot("QItemSelection")
    def select_mapping(self, selection):
        """Emits mappingChanged with the selected mapping."""
        if selection.indexes():
            m = self._mappings_model.data_mapping(selection.indexes()[0])
        else:
            m = None
        self.mapping_changed.emit(m)

    def selected_mapping_name(self):
        """Returns the name of the selected mapping."""
        if not self._ui.list_view.selectionModel().hasSelection():
            return None
        return self._ui.list_view.selectionModel().selection().indexes()[0].data()
