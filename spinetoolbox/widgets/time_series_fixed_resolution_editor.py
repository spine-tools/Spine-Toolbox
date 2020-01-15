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
Contains logic for the fixed step time series editor widget.

:author: A. Soininen (VTT)
:date:   14.6.2019
"""

from datetime import datetime
from PySide2.QtCore import QDate, QPoint, Qt, Slot
from PySide2.QtWidgets import QCalendarWidget, QWidget
from spinedb_api import (
    duration_to_relativedelta,
    ParameterValueFormatError,
    relativedelta_to_duration,
    TimeSeriesFixedResolution,
)
from ..plotting import add_time_series_plot
from ..mvcmodels.time_series_model_fixed_resolution import TimeSeriesModelFixedResolution
from .custom_qtableview import TimeSeriesFixedResolutionTableView
from .indexed_value_table_context_menu import handle_table_context_menu
from .plot_widget import PlotWidget


def _resolution_to_text(resolution):
    """Converts a list of durations into a string of comma-separated durations."""
    if len(resolution) == 1:
        return relativedelta_to_duration(resolution[0])
    affix = ''
    text = ''
    for r in resolution:
        text = text + affix + relativedelta_to_duration(r)
        affix = ', '
    return text


def _text_to_resolution(text):
    """Converts a comma-separated string of durations into a resolution array."""
    return [token.strip() for token in text.split(',')]


class TimeSeriesFixedResolutionEditor(QWidget):
    """
    A widget for editing time series data with a fixed time step.

    Attributes:
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        from ..ui.time_series_fixed_resolution_editor import Ui_TimeSeriesFixedResolutionEditor

        super().__init__(parent)
        start = datetime(year=2000, month=1, day=1)
        resolution = [duration_to_relativedelta("1 hour")]
        values = 2 * [0.0]
        initial_value = TimeSeriesFixedResolution(start, resolution, values, False, False)
        self._model = TimeSeriesModelFixedResolution(initial_value)
        self._model.dataChanged.connect(self._update_plot)
        self._model.modelReset.connect(self._update_plot)
        self._model.rowsInserted.connect(self._update_plot)
        self._model.rowsRemoved.connect(self._update_plot)
        self._ui = Ui_TimeSeriesFixedResolutionEditor()
        self._ui.setupUi(self)
        self._plot_widget = PlotWidget()
        self._ui.splitter.insertWidget(1, self._plot_widget)
        self._ui.start_time_edit.setText(str(initial_value.start))
        self._ui.start_time_edit.editingFinished.connect(self._start_time_changed)
        self._ui.calendar_button.clicked.connect(self._show_calendar)
        self._ui.resolution_edit.setText(_resolution_to_text(initial_value.resolution))
        self._ui.resolution_edit.editingFinished.connect(self._resolution_changed)
        self._time_series_table = TimeSeriesFixedResolutionTableView(self._ui.splitter)
        self._ui.left_layout.addWidget(self._time_series_table)
        self._time_series_table.setModel(self._model)
        self._time_series_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._time_series_table.customContextMenuRequested.connect(self._show_table_context_menu)
        self._ui.ignore_year_check_box.setChecked(self._model.value.ignore_year)
        self._ui.ignore_year_check_box.toggled.connect(self._model.set_ignore_year)
        self._ui.repeat_check_box.setChecked(self._model.value.repeat)
        self._ui.repeat_check_box.toggled.connect(self._model.set_repeat)
        self._calendar = QCalendarWidget(self)
        self._calendar.setMinimumDate(QDate(100, 1, 1))
        self._calendar.setWindowFlags(Qt.Popup)
        self._calendar.activated.connect(self._select_date)
        self._update_plot()

    @Slot(name='_resolution_changed')
    def _resolution_changed(self):
        """Updates the models after resolution change."""
        try:
            resolution = _text_to_resolution(self._ui.resolution_edit.text())
            self._model.set_resolution(resolution)
        except ParameterValueFormatError:
            text = _resolution_to_text(self._model.value.resolution)
            self._ui.resolution_edit.setText(text)

    @Slot("QPoint", name="_show_table_context_menu")
    def _show_table_context_menu(self, pos):
        """Shows the table's context menu."""
        handle_table_context_menu(pos, self._time_series_table, self._model, self)

    @Slot("QDate", name='_select_date')
    def _select_date(self, selected_date):
        self._calendar.hide()
        time = self._model.value.start.time()
        new_date = datetime(year=selected_date.year(), month=selected_date.month(), day=selected_date.day())
        new_datetime = datetime.combine(new_date, time)
        self._ui.start_time_edit.setText(str(new_datetime))
        self._model.set_start(new_datetime)

    def set_value(self, value):
        """Sets the parameter value for editing in this widget."""
        self._model.reset(value)
        self._ui.start_time_edit.setText(str(self._model.value.start))
        self._ui.resolution_edit.setText(_resolution_to_text(self._model.value.resolution))
        self._ui.ignore_year_check_box.setChecked(self._model.value.ignore_year)
        self._ui.repeat_check_box.setChecked(self._model.value.repeat)

    @Slot(name='_show_calendar')
    def _show_calendar(self):
        start = self._model.value.start
        if start.year >= 100:
            self._calendar.setSelectedDate(QDate(start.year, start.month, start.day))
        else:
            self._calendar.setSelectedDate(QDate.currentDate())
        button_position = self._ui.calendar_button.mapToGlobal(QPoint(0, 0))
        calendar_x = button_position.x()
        calendar_y = button_position.y() + self._ui.calendar_button.height()
        self._calendar.move(calendar_x, calendar_y)
        self._calendar.show()

    @Slot(name='_start_time_changed')
    def _start_time_changed(self):
        """Updates the model due to start time change."""
        text = self._ui.start_time_edit.text()
        try:
            self._model.set_start(text)
        except ParameterValueFormatError:
            self._ui.start_time_edit.setText(str(self._model.value.start))

    @Slot("QModelIndex", "QModelIndex", "list", name="_update_plot")
    def _update_plot(self, topLeft=None, bottomRight=None, roles=None):
        """Updated the plot."""
        self._plot_widget.canvas.axes.cla()
        add_time_series_plot(self._plot_widget, self._model)
        self._plot_widget.canvas.draw()

    def value(self):
        """Returns the parameter value currently being edited."""
        return self._model.value
