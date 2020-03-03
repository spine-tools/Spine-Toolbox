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
MappingWidget and MappingOptionsWidget class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt, Signal
from spinedb_api import RelationshipClassMapping, ParameterTimeSeriesMapping
from .custom_menus import SimpleFilterMenu
from .custom_delegates import ComboBoxDelegate
from ..spine_io.io_models import MappingSpecModel

MAPPING_CHOICES = ("Constant", "Column", "Row", "Column Header", "Headers", "None")


class MappingWidget(QWidget):
    """
    A widget for managing Mappings (add, remove, edit, visualize, and so on).
    Intended to be embedded in a ImportPreviewWidget.
    """

    mappingChanged = Signal(MappingSpecModel)
    mappingDataChanged = Signal()

    def __init__(self, parent=None):
        from ..ui.import_mapping import Ui_ImportMapping

        super().__init__(parent)

        # state
        self._model = None

        # initialize interface
        self._ui = Ui_ImportMapping()
        self._ui.setupUi(self)
        self._ui_options = MappingOptionsWidget()
        self._ui.bottom_layout.insertWidget(0, self._ui_options)
        self._ui.table_view.setItemDelegateForColumn(1, ComboBoxDelegate(self, MAPPING_CHOICES))
        for i in range(self._ui.splitter.count()):
            self._ui.splitter.setCollapsible(i, False)

        # connect signals
        self._select_handle = None
        self._ui.new_button.clicked.connect(self.new_mapping)
        self._ui.remove_button.clicked.connect(self.delete_selected_mapping)
        self.mappingChanged.connect(self._ui.table_view.setModel)
        self.mappingChanged.connect(self._ui_options.set_model)

    def set_data_source_column_num(self, num):
        self._ui_options.set_num_available_columns(num)

    def set_model(self, model):
        """
        Sets new model
        """
        if self._select_handle and self._ui.list_view.selectionModel():
            self._ui.list_view.selectionModel().selectionChanged.disconnect(self.select_mapping)
            self._select_handle = None
        if self._model:
            self._model.dataChanged.disconnect(self.data_changed)
        self._model = model
        self._ui.list_view.setModel(model)
        self._select_handle = self._ui.list_view.selectionModel().selectionChanged.connect(self.select_mapping)
        self._model.dataChanged.connect(self.data_changed)
        if self._model.rowCount() > 0:
            self._ui.list_view.setCurrentIndex(self._model.index(0, 0))
        else:
            self._ui.list_view.clearSelection()

    def data_changed(self):
        m = None
        indexes = self._ui.list_view.selectedIndexes()
        if self._model and indexes:
            m = self._model.data_mapping(indexes()[0])
        self.mappingDataChanged.emit(m)

    def new_mapping(self):
        """
        Adds new empty mapping
        """
        if self._model:
            self._model.add_mapping()
            if not self._ui.list_view.selectedIndexes():
                # if no item is selected, select the first item
                self._ui.list_view.setCurrentIndex(self._model.index(0, 0))

    def delete_selected_mapping(self):
        """
        deletes selected mapping
        """
        if self._model is not None:
            # get selected mapping in list
            indexes = self._ui.list_view.selectedIndexes()
            if indexes:
                self._model.remove_mapping(indexes[0].row())
                if self._model.rowCount() > 0:
                    # select the first item
                    self._ui.list_view.setCurrentIndex(self._model.index(0, 0))
                    self.select_mapping(self._ui.list_view.selectionModel().selection())
                else:
                    # no items clear selection so select_mapping is called
                    self._ui.list_view.clearSelection()

    def select_mapping(self, selection):
        """
        gets selected mapping and emits mappingChanged
        """
        if selection.indexes():
            m = self._model.data_mapping(selection.indexes()[0])
        else:
            m = None
        self.mappingChanged.emit(m)


class MappingOptionsWidget(QWidget):
    """
    A widget for managing Mapping options (class type, dimensions, parameter type, ignore columns, and so on).
    Intended to be embedded in a MappingWidget.
    """

    def __init__(self, parent=None):
        from ..ui.import_mapping_options import Ui_ImportMappingOptions

        super().__init__(parent)

        # state
        self._model = None

        # ui
        self._ui = Ui_ImportMappingOptions()
        self._ui.setupUi(self)
        self._ui_ignore_columns_filtermenu = SimpleFilterMenu(self._ui.ignore_columns_button, show_empty=False)
        self._ui.ignore_columns_button.setMenu(self._ui_ignore_columns_filtermenu)

        # connect signals
        self._ui.dimension_spin_box.valueChanged.connect(self.change_dimension)
        self._ui.class_type_combo_box.currentTextChanged.connect(self.change_class)
        self._ui.parameter_type_combo_box.currentTextChanged.connect(self.change_parameter)
        self._ui.import_objects_check_box.stateChanged.connect(self.change_import_objects)
        self._ui_ignore_columns_filtermenu.filterChanged.connect(self.change_skip_columns)
        self._ui.start_read_row_spin_box.valueChanged.connect(self.change_read_start_row)

        self._model_reset_signal = None
        self._model_data_signal = None

        self.update_ui()

    def set_num_available_columns(self, num):
        selected = self._ui_ignore_columns_filtermenu._filter._filter_model.get_selected()
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_list(set(range(num)))
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(selected)

    def change_skip_columns(self, skip_cols):
        if self._model:
            self._model.set_skip_columns(skip_cols)

    def set_model(self, model):
        try:
            self._ui.time_series_repeat_check_box.toggled.disconnect()
        except RuntimeError:
            pass
        if self._model:
            if self._model_reset_signal:
                self._model.modelReset.disconnect(self.update_ui)
                self._model_reset_signal = None
            if self._model_data_signal:
                self._model.dataChanged.disconnect(self.update_ui)
                self._model_data_signal = None
        self._model = model
        if self._model:
            self._model_reset_signal = self._model.modelReset.connect(self.update_ui)
            self._model_data_signal = self._model.dataChanged.connect(self.update_ui)
            self._ui.time_series_repeat_check_box.toggled.connect(self._model.set_time_series_repeat)
        self.update_ui()

    def update_ui(self):
        """
        updates ui to RelationshipClassMapping or ObjectClassMapping model
        """
        if not self._model:
            self.hide()
            return

        self.show()
        self.block_signals = True
        if self._model.map_type == RelationshipClassMapping:
            self._ui.dimension_label.show()
            self._ui.dimension_spin_box.show()
            self._ui.class_type_combo_box.setCurrentIndex(1)
            self._ui.dimension_spin_box.setValue(len(self._model._model.objects))
            self._ui.import_objects_check_box.show()
            if self._model._model.import_objects:
                self._ui.import_objects_check_box.setCheckState(Qt.Checked)
            else:
                self._ui.import_objects_check_box.setCheckState(Qt.Unchecked)
        else:
            self._ui.import_objects_check_box.hide()
            self._ui.dimension_label.hide()
            self._ui.dimension_spin_box.hide()
            self._ui.class_type_combo_box.setCurrentIndex(0)
        # update parameter mapping
        self._ui.parameter_type_combo_box.setCurrentText(self._model.parameter_type)

        self._ui.ignore_columns_button.setVisible(self._model.is_pivoted)
        self._ui.ignore_columns_label.setVisible(self._model.is_pivoted)

        # update ignore columns filter
        skip_cols = []
        if self._model._model.skip_columns:
            skip_cols = self._model._model.skip_columns
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(skip_cols)
        skip_text = ",".join(str(c) for c in skip_cols)
        if len(skip_text) > 20:
            skip_text = skip_text[:20] + "..."
        self._ui.ignore_columns_button.setText(skip_text)

        self._ui.start_read_row_spin_box.setValue(self._model.read_start_row)

        self._update_time_series_options()

        self.block_signals = False

    def change_class(self, new_class):
        if self._model and not self.block_signals:
            self._model.change_model_class(new_class)

    def change_dimension(self, dim):
        if self._model and not self.block_signals:
            self._model.set_dimension(dim)

    def change_parameter(self, par):
        if self._model and not self.block_signals:
            self._model.change_parameter_type(par)

    def change_import_objects(self, state):
        if self._model and not self.block_signals:
            self._model.set_import_objects(state)

    def change_read_start_row(self, row):
        if self._model and not self.block_signals:
            self._model.set_read_start_row(row)

    def _update_time_series_options(self):
        if self._model is None:
            return
        par = self._model.model_parameters()
        is_time_series = isinstance(par, ParameterTimeSeriesMapping)
        self._ui.time_series_repeat_check_box.setEnabled(is_time_series)
        self._ui.time_series_repeat_check_box.setCheckState(
            Qt.Checked if is_time_series and par.options.repeat else Qt.Unchecked
        )
