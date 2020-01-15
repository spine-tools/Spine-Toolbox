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
A Qt widget showing a toolbar and a matplotlib plotting canvas.

:author: A. Soininen (VTT)
:date:   27.6.2019
"""

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
from PySide2.QtCore import QMetaObject
from PySide2.QtWidgets import QVBoxLayout, QWidget
from .plot_canvas import PlotCanvas


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self.canvas = PlotCanvas(self)
        self._toolbar = NavigationToolBar(self.canvas, self)
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self.canvas)
        QMetaObject.connectSlotsByName(self)
