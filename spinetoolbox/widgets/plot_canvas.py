######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
A Qt widget to use as a matplotlib backend.

:author: A. Soininen (VTT)
:date:   3.6.2019
"""

import matplotlib
from PySide2 import QtWidgets
import logging
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from pandas.plotting import register_matplotlib_converters


register_matplotlib_converters()  # Needed to plot the time series indexes
matplotlib.use('Qt5Agg')
_mpl_logger = logging.getLogger("matplotlib")
_mpl_logger.setLevel(logging.WARNING)


class PlotCanvas(FigureCanvasQTAgg):
    """A widget for plotting with matplotlib"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        super().setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        super().updateGeometry()
