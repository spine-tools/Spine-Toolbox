######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialogButtonBox,
    QGridLayout,
    QComboBox,
    QPushButton,
    QTableView,
    QHBoxLayout,
    QSpinBox,
    QGroupBox,
    QLabel,
    QListView,
    QCheckBox,
    QSplitter,
)
from PySide2.QtCore import Qt, Signal
from spinedb_api import RelationshipClassMapping
from widgets.custom_menus import FilterMenu
from widgets.custom_delegates import ComboBoxDelegate
from spine_io.io_models import MappingSpecModel

MAPPING_CHOICES = ("Constant", "Column", "Row", "Header", "None")


class MappingWidget(QWidget):
    """
    A widget for managing Mappings (add, remove, edit, visualize, and so on).
    Intended to be embeded in a ImportPreviewWidget.
    """

    mappingChanged = Signal(MappingSpecModel)
    mappingDataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # state
        self._model = None

        # create widgets
        self._ui_add_mapping = QPushButton("New")
        self._ui_remove_mapping = QPushButton("Remove")
        self._ui_list = QListView()
        self._ui_table = QTableView()
        self._ui_options = MappingOptionsWidget()
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self._ui_table.setItemDelegateForColumn(1, ComboBoxDelegate(self, MAPPING_CHOICES))

        # layout
        self.setLayout(QVBoxLayout())
        splitter = QSplitter()

        top_widget = QWidget()
        top_widget.setLayout(QVBoxLayout())
        bl = QHBoxLayout()
        bl.addWidget(self._ui_add_mapping)
        bl.addWidget(self._ui_remove_mapping)
        top_widget.layout().addLayout(bl)
        top_widget.layout().addWidget(self._ui_list)

        bottom_widget = QWidget()
        bottom_widget.setLayout(QVBoxLayout())
        bottom_widget.layout().addWidget(self._ui_options)
        bottom_widget.layout().addWidget(self._ui_table)

        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setOrientation(Qt.Vertical)

        self.layout().addWidget(splitter)
        # self.layout().addWidget(self._ui_list)
        # self.layout().addWidget(self._ui_options)
        # self.layout().addWidget(self._ui_table)

        # connect signals
        self._select_handle = None
        self._ui_add_mapping.clicked.connect(self.new_mapping)
        self._ui_remove_mapping.clicked.connect(self.delete_selected_mapping)
        self.mappingChanged.connect(self._ui_table.setModel)
        self.mappingChanged.connect(self._ui_options.set_model)

    def set_data_source_column_num(self, num):
        self._ui_options.set_num_available_columns(num)

    def set_model(self, model):
        """
        Sets new model
        """
        if self._select_handle and self._ui_list.selectionModel():
            self._ui_list.selectionModel().selectionChanged.disconnect(self.select_mapping)
            self._select_handle = None
        if self._model:
            self._model.dataChanged.disconnect(self.data_changed)
        self._model = model
        self._ui_list.setModel(model)
        self._select_handle = self._ui_list.selectionModel().selectionChanged.connect(self.select_mapping)
        self._model.dataChanged.connect(self.data_changed)
        if self._model.rowCount() > 0:
            self._ui_list.setCurrentIndex(self._model.index(0, 0))
        else:
            self._ui_list.clearSelection()

    def data_changed(self):
        m = None
        indexes = self._ui_list.selectedIndexes()
        if self._model and indexes:
            m = self._model.data_mapping(indexes()[0])
        self.mappingDataChanged.emit(m)

    def new_mapping(self):
        """
        Adds new empty mapping
        """
        if self._model:
            self._model.add_mapping()
            if not self._ui_list.selectedIndexes():
                # if no item is selected, select the first item
                self._ui_list.setCurrentIndex(self._model.index(0, 0))

    def delete_selected_mapping(self):
        """
        deletes selected mapping
        """
        if self._model is not None:
            # get selected mapping in list
            indexes = self._ui_list.selectedIndexes()
            if indexes:
                self._model.remove_mapping(indexes[0].row())
                if self._model.rowCount() > 0:
                    # select the first item
                    self._ui_list.setCurrentIndex(self._model.index(0, 0))
                    self.select_mapping(self._ui_list.selectionModel().selection())
                else:
                    # no items clear selection so select_mapping is called
                    self._ui_list.clearSelection()

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
    Intended to be embeded in a MappingWidget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # state
        self._model = None

        # ui
        self._ui_class_type = QComboBox()
        self._ui_parameter_type = QComboBox()
        self._ui_dimension = QSpinBox()
        self._ui_ignore_columns = QPushButton()
        self._ui_ignore_columns_label = QLabel("Ignore columns:")
        self._ui_dimension_label = QLabel("Dimension:")
        self._ui_import_objects = QCheckBox("Import objects")
        self._ui_ignore_columns_filtermenu = FilterMenu(self._ui_ignore_columns, show_empty=False)
        self._ui_ignore_columns.setMenu(self._ui_ignore_columns_filtermenu)

        self._ui_class_type.addItems(["Object", "Relationship"])
        self._ui_parameter_type.addItems(["Single value", "Time series", "None"])

        self._ui_dimension.setMinimum(1)

        # layout
        groupbox = QGroupBox("Mapping:")
        self.setLayout(QVBoxLayout())
        layout = QGridLayout()
        layout.addWidget(QLabel("Class type:"), 0, 0)
        layout.addWidget(QLabel("Parameter type:"), 1, 0)
        layout.addWidget(self._ui_ignore_columns_label, 3, 0)
        layout.addWidget(self._ui_dimension_label, 0, 2)
        layout.addWidget(self._ui_class_type, 0, 1)
        layout.addWidget(self._ui_parameter_type, 1, 1)
        layout.addWidget(self._ui_import_objects, 2, 1)
        layout.addWidget(self._ui_ignore_columns, 3, 1)
        layout.addWidget(self._ui_dimension, 0, 3)
        groupbox.setLayout(layout)
        self.layout().addWidget(groupbox)

        # connect signals
        self._ui_dimension.valueChanged.connect(self.change_dimension)
        self._ui_class_type.currentTextChanged.connect(self.change_class)
        self._ui_parameter_type.currentTextChanged.connect(self.change_parameter)
        self._ui_import_objects.stateChanged.connect(self.change_import_objects)
        self._ui_ignore_columns_filtermenu.filterChanged.connect(self.change_skip_columns)

        self._model_reset_signal = None
        self._model_data_signal = None

        self.update_ui()

    def set_num_available_columns(self, num):
        selected = self._ui_ignore_columns_filtermenu._filter._filter_model.get_selected()
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_list(set(range(num)))
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(selected)

    def change_skip_columns(self, filterw, skip_cols, has_filter):
        if self._model:
            self._model.set_skip_columns(skip_cols)

    def set_model(self, model):
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
            self._ui_dimension_label.show()
            self._ui_dimension.show()
            self._ui_class_type.setCurrentIndex(1)
            self._ui_dimension.setValue(len(self._model._model.objects))
            self._ui_import_objects.show()
            if self._model._model.import_objects:
                self._ui_import_objects.setCheckState(Qt.Checked)
            else:
                self._ui_import_objects.setCheckState(Qt.Unchecked)
        else:
            self._ui_import_objects.hide()
            self._ui_dimension_label.hide()
            self._ui_dimension.hide()
            self._ui_class_type.setCurrentIndex(0)
        if self._model._model.parameters is None:
            self._ui_parameter_type.setCurrentIndex(2)
        else:
            if self._model._model.parameters.extra_dimensions:
                self._ui_parameter_type.setCurrentIndex(1)
            else:
                self._ui_parameter_type.setCurrentIndex(0)
        if self._model._model.is_pivoted():
            self._ui_ignore_columns.show()
            self._ui_ignore_columns_label.show()
        else:
            self._ui_ignore_columns.hide()
            self._ui_ignore_columns_label.hide()
        # update ignore columns filter
        skip_cols = []
        if self._model._model.skip_columns:
            skip_cols = self._model._model.skip_columns
        self._ui_ignore_columns_filtermenu._filter._filter_model.set_selected(skip_cols)
        skip_text = ",".join(str(c) for c in skip_cols)
        if len(skip_text) > 20:
            skip_text = skip_text[:20] + "..."
        self._ui_ignore_columns.setText(skip_text)

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
