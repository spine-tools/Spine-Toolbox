######################################################################################################################
# Copyright (C) 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains logic for the time series editor widget.

:author: A. Soininen (VTT)
:date:   31.5.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget
from models import MinimalTableModel
from ui.time_series_editor import Ui_dialog


class TimeSeriesEditor(QWidget):
    def __init__(self, data):
        super().__init__()
        self.ui = Ui_dialog()
        self.ui.setupUi(self)
        self.ui.close_button.clicked.connect(self.close)
        self._model = MinimalTableModel()
        self._model.reset_model(data)
        self._model.setHeaderData(0, Qt.Horizontal, 'Time')
        self._model.setHeaderData(1, Qt.Horizontal, 'Value')
        self.ui.time_series_table.setModel(self._model)
