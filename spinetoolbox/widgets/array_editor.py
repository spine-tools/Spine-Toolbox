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

"""Contains an editor widget for array type parameter values."""
from PySide6.QtCore import QModelIndex, QPoint, Qt, Slot
from PySide6.QtWidgets import QHeaderView, QWidget
from spinedb_api import DateTime, Duration, ParameterValueFormatError
from .array_value_editor import ArrayValueEditor
from .indexed_value_table_context_menu import ArrayTableContextMenu
from .parameter_value_editor_base import ValueType
from ..helpers import inquire_index_name
from ..mvcmodels.array_model import ArrayModel
from ..plotting import add_array_plot
from ..spine_db_editor.widgets.custom_delegates import ParameterValueElementDelegate


class ArrayEditor(QWidget):
    """Editor widget for Arrays."""

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        from ..ui.array_editor import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._model = ArrayModel(self)
        self._model.dataChanged.connect(self._update_plot)
        self._model.headerDataChanged.connect(self._update_plot)
        self._model.modelReset.connect(self._update_plot)
        self._model.rowsInserted.connect(self._update_plot)
        self._model.rowsRemoved.connect(self._update_plot)
        self._ui.array_table_view.init_copy_and_paste_actions()
        self._ui.array_table_view.setModel(self._model)
        self._ui.array_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.array_table_view.customContextMenuRequested.connect(self._show_table_context_menu)
        header = self._ui.array_table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.sectionDoubleClicked.connect(self._open_header_editor)
        self._ui.value_type_combo_box.currentTextChanged.connect(self._change_value_type)
        delegate = ParameterValueElementDelegate(self._ui.array_table_view)
        delegate.value_editor_requested.connect(self.open_value_editor)
        self._ui.array_table_view.setItemDelegate(delegate)
        for i in range(self._ui.splitter.count()):
            self._ui.splitter.setCollapsible(i, False)

    def set_value(self, value):
        """Sets the parameter_value for editing in this widget.

        Args:
            value (Array): value for editing
        """
        type_name = {float: "Float", DateTime: "Datetime", Duration: "Duration", str: "String"}[value.value_type]
        self._ui.value_type_combo_box.blockSignals(True)
        self._ui.value_type_combo_box.setCurrentText(type_name)
        self._ui.value_type_combo_box.blockSignals(False)
        self._model.reset(value)
        self._check_if_plotting_enabled(type_name)

    def value(self):
        """Returns the array currently being edited.

        Returns:
            Array: array
        """
        return self._model.array()

    def _check_if_plotting_enabled(self, type_name):
        """Checks is array's data type allows the array to be plotted.

        Args:
            type_name (str): data type's name
        """
        if type_name == "Float":
            self._ui.plot_widget_stack.setCurrentIndex(1)
        else:
            self._ui.plot_widget_stack.setCurrentIndex(0)

    @Slot(str)
    def _change_value_type(self, type_name):
        value_type = {"Float": float, "Datetime": DateTime, "Duration": Duration, "String": str}[type_name]
        self._model.set_array_type(value_type)
        self._check_if_plotting_enabled(type_name)

    @Slot(QModelIndex)
    def open_value_editor(self, index):
        """
        Opens an editor widget for array element.

        Args:
            index (QModelIndex): element's index
        """

        value_type = {
            "Float": ValueType.PLAIN_VALUE,
            "Datetime": ValueType.DATETIME,
            "Duration": ValueType.DURATION,
            "String": ValueType.PLAIN_VALUE,
        }[self._ui.value_type_combo_box.currentText()]
        editor = ArrayValueEditor(index, value_type, self)
        editor.show()

    @Slot(QPoint)
    def _show_table_context_menu(self, position):
        """
        Shows the table's context menu.

        Args:
            position (QPoint): menu's position on the table
        """
        menu = ArrayTableContextMenu(self, self._ui.array_table_view, position)
        menu.exec(self._ui.array_table_view.mapToGlobal(position))

    @Slot(QModelIndex, QModelIndex, list)
    def _update_plot(self, topLeft=None, bottomRight=None, roles=None):
        """Updates the plot widget."""
        if self._ui.value_type_combo_box.currentText() != "Float":
            return
        self._ui.plot_widget.canvas.axes.cla()
        try:
            add_array_plot(self._ui.plot_widget, self._model.array())
        except ParameterValueFormatError:
            return
        self._ui.plot_widget.canvas.draw()

    @Slot(int)
    def _open_header_editor(self, column):
        if column != 0:
            return
        inquire_index_name(self._model, column, "Rename array's index", self)
