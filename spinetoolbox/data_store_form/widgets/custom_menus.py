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
Classes for custom context menus and pop-up menus.

:author: M. Marin (KTH)
:date:   13.5.2020
"""

from PySide2.QtWidgets import QWidgetAction
from PySide2.QtCore import QEvent, QPoint, Signal
from .custom_qwidgets import LazyFilterWidget, DataToValueFilterWidget
from ...widgets.custom_menus import FilterMenuBase


class ParameterViewFilterMenu(FilterMenuBase):

    filterChanged = Signal(set, bool)

    def __init__(self, parent, source_model, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            source_model (CompoundParameterModel): a model to lazily get data from
        """
        super().__init__(parent)
        self._filter = LazyFilterWidget(self, source_model, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.connect_signals()
        self.aboutToShow.connect(self._filter.set_model)

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(valid_values, self._filter.has_filter())


class TabularViewFilterMenu(FilterMenuBase):
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    filterChanged = Signal(int, set, bool)

    def __init__(self, parent, identifier, data_to_value, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            identifier (int): index identifier
            data_to_value (method): a method to translate item data to a value for display role
        """
        super().__init__(parent)
        self.identifier = identifier
        self._filter = DataToValueFilterWidget(self, data_to_value, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.anchor = parent
        self.connect_signals()

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(self.identifier, valid_values, self._filter.has_filter())

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)
