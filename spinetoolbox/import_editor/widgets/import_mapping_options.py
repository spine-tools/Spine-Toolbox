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
ImportMappingOptions widget.

:author: P. Vennström (VTT)
:date:   12.5.2020
"""
from PySide2.QtCore import Qt
from spinedb_api import (
    RelationshipClassMapping,
    ObjectClassMapping,
    ObjectGroupMapping,
    ParameterMapMapping,
    ParameterTimeSeriesMapping,
)
from ...widgets.custom_menus import SimpleFilterMenu


class ImportMappingOptions:
    """
    Provides methods for managing Mapping options (class type, dimensions, parameter type, ignore columns, and so on).
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # state
        self._mapping_options_model = None
        self._block_signals = False
        self._model_reset_signal = None
        self._model_data_signal = None
        self._ui_ignore_columns_filtermenu = None

    def _init_import_mapping_options(self):
        # ui
        self._ui_ignore_columns_filtermenu = SimpleFilterMenu(self._ui.ignore_columns_button, show_empty=False)
        self._ui.ignore_columns_button.setMenu(self._ui_ignore_columns_filtermenu)

        # connect signals
        self._ui.dimension_spin_box.valueChanged.connect(self.change_dimension)
        self._ui.class_type_combo_box.currentTextChanged.connect(self.change_class)
        self._ui.parameter_type_combo_box.currentTextChanged.connect(self.change_parameter)
        self._ui.import_objects_check_box.stateChanged.connect(self.change_import_objects)
        self._ui_ignore_columns_filtermenu.filterChanged.connect(self.change_skip_columns)
        self._ui.start_read_row_spin_box.valueChanged.connect(self.change_read_start_row)

        self.update_ui()

    def set_num_available_columns(self, num):
        selected = self._ui_ignore_columns_filtermenu._filter._filter_model.get_selected()
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_list(set(range(num)))
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(selected)

    def change_skip_columns(self, skip_cols):
        if self._mapping_options_model:
            self._mapping_options_model.set_skip_columns(skip_cols)

    def set_mapping_options_model(self, model):
        try:
            self._ui.time_series_repeat_check_box.toggled.disconnect()
        except RuntimeError:
            pass
        try:
            self._ui.map_dimension_spin_box.valueChanged.disconnect()
        except RuntimeError:
            pass
        if self._mapping_options_model:
            if self._model_reset_signal:
                self._mapping_options_model.modelReset.disconnect(self.update_ui)
                self._model_reset_signal = None
            if self._model_data_signal:
                self._mapping_options_model.dataChanged.disconnect(self.update_ui)
                self._model_data_signal = None
        self._mapping_options_model = model
        if self._mapping_options_model:
            self._model_reset_signal = self._mapping_options_model.modelReset.connect(self.update_ui)
            self._model_data_signal = self._mapping_options_model.dataChanged.connect(self.update_ui)
            self._ui.time_series_repeat_check_box.toggled.connect(self._mapping_options_model.set_time_series_repeat)
            self._ui.map_dimension_spin_box.valueChanged.connect(self._mapping_options_model.set_map_dimensions)
        self.update_ui()

    def update_ui(self):
        """
        updates ui to RelationshipClassMapping or ObjectClassMapping model
        """
        if not self._mapping_options_model:
            self.hide()
            return

        self.show()
        self._block_signals = True
        if self._mapping_options_model.map_type == RelationshipClassMapping:
            self._ui.dimension_label.show()
            self._ui.dimension_spin_box.show()
            self._ui.class_type_combo_box.setCurrentIndex(1)
            self._ui.dimension_spin_box.setValue(len(self._mapping_options_model._model.objects))
            self._ui.import_objects_check_box.show()
            if self._mapping_options_model._model.import_objects:
                self._ui.import_objects_check_box.setCheckState(Qt.Checked)
            else:
                self._ui.import_objects_check_box.setCheckState(Qt.Unchecked)
        elif self._mapping_options_model.map_type == ObjectClassMapping:
            self._ui.import_objects_check_box.hide()
            self._ui.dimension_label.hide()
            self._ui.dimension_spin_box.hide()
            self._ui.class_type_combo_box.setCurrentIndex(0)
        elif self._mapping_options_model.map_type == ObjectGroupMapping:
            self._ui.import_objects_check_box.show()
            self._ui.dimension_label.hide()
            self._ui.dimension_spin_box.hide()
            self._ui.class_type_combo_box.setCurrentIndex(2)
        # update parameter mapping
        self._ui.parameter_type_combo_box.setCurrentText(self._mapping_options_model.parameter_type)

        self._ui.ignore_columns_button.setVisible(self._mapping_options_model.is_pivoted)
        self._ui.ignore_columns_label.setVisible(self._mapping_options_model.is_pivoted)

        # update ignore columns filter
        skip_cols = []
        if self._mapping_options_model._model.skip_columns:
            skip_cols = self._mapping_options_model._model.skip_columns
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(skip_cols)
        skip_text = ",".join(str(c) for c in skip_cols)
        if len(skip_text) > 20:
            skip_text = skip_text[:20] + "..."
        self._ui.ignore_columns_button.setText(skip_text)

        self._ui.start_read_row_spin_box.setValue(self._mapping_options_model.read_start_row)

        self._update_time_series_options()
        self._update_map_options()
        self._block_signals = False

    def change_class(self, new_class):
        if self._mapping_options_model and not self._block_signals:
            self._mapping_options_model.change_model_class(new_class)

    def change_dimension(self, dim):
        if self._mapping_options_model and not self._block_signals:
            self._mapping_options_model.set_dimension(dim)

    def change_parameter(self, par):
        if self._mapping_options_model and not self._block_signals:
            self._mapping_options_model.change_parameter_type(par)

    def change_import_objects(self, state):
        if self._mapping_options_model and not self._block_signals:
            self._mapping_options_model.set_import_objects(state)

    def change_read_start_row(self, row):
        if self._mapping_options_model and not self._block_signals:
            self._mapping_options_model.set_read_start_row(row)

    def _update_time_series_options(self):
        if self._mapping_options_model is None:
            return
        par = self._mapping_options_model.model_parameters()
        is_time_series = isinstance(par, ParameterTimeSeriesMapping)
        self._ui.time_series_repeat_check_box.setEnabled(is_time_series)
        self._ui.time_series_repeat_check_box.setCheckState(
            Qt.Checked if is_time_series and par.options.repeat else Qt.Unchecked
        )

    def _update_map_options(self):
        if self._mapping_options_model is None:
            return
        mapping = self._mapping_options_model.model_parameters()
        is_map = isinstance(mapping, ParameterMapMapping)
        self._ui.map_dimension_spin_box.setEnabled(is_map)
        self._ui.map_dimension_spin_box.setValue(len(mapping.extra_dimensions) if is_map else 1)
