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
Contains an editor widget array type parameter values.

:author: A. Soininen (VTT)
:date:   25.3.2020
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import DateTime, Duration
from .indexed_value_table_context_menu import handle_table_context_menu
from ..mvcmodels.array_model import ArrayModel
from ..plotting import add_array_plot


class ArrayEditor(QWidget):
    def __init__(self, parent=None):
        from ..ui.array_editor import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._model = ArrayModel()
        self._model.dataChanged.connect(self._update_plot)
        self._model.modelReset.connect(self._update_plot)
        self._model.rowsInserted.connect(self._update_plot)
        self._model.rowsRemoved.connect(self._update_plot)
        self._ui.array_table_view.setModel(self._model)
        self._ui.array_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.array_table_view.customContextMenuRequested.connect(self._show_table_context_menu)
        self._ui.value_type_combo_box.currentTextChanged.connect(self._change_value_type)
        for i in range(self._ui.splitter.count()):
            self._ui.splitter.setCollapsible(i, False)

    def set_value(self, value):
        """Sets the parameter_value for editing in this widget."""
        type_name = {float: "Float", DateTime: "Datetime", Duration: "Duration", str: "String"}[value.value_type]
        self._ui.value_type_combo_box.blockSignals(True)
        self._ui.value_type_combo_box.setCurrentText(type_name)
        self._ui.value_type_combo_box.blockSignals(False)
        self._model.reset(value)
        self._check_if_plotting_enabled(type_name)

    def value(self):
        return self._model.array()

    def _check_if_plotting_enabled(self, type_name):
        if type_name == "Float":
            self._ui.plot_widget_stack.setCurrentIndex(1)
        else:
            self._ui.plot_widget_stack.setCurrentIndex(0)

    @Slot(str)
    def _change_value_type(self, type_name):
        value_type = {"Float": float, "Datetime": DateTime, "Duration": Duration, "String": str}[type_name]
        self._model.set_array_type(value_type)
        self._check_if_plotting_enabled(type_name)

    @Slot("QPoint")
    def _show_table_context_menu(self, pos):
        """Shows the table's context menu."""
        handle_table_context_menu(pos, self._ui.array_table_view, self._model, self)

    @Slot("QModelIndex", "QModelIndex", "list")
    def _update_plot(self, topLeft=None, bottomRight=None, roles=None):
        """Updates the plot widget."""
        if self._ui.value_type_combo_box.currentText() != "Float":
            return
        self._ui.plot_widget.canvas.axes.cla()
        add_array_plot(self._ui.plot_widget, self._model.array())
        self._ui.plot_widget.canvas.draw()
