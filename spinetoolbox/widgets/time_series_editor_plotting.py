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
Common plotting functions for time series parameter value editors.

:author: A. Soininen (VTT)
:date:   15.7.2019
"""

def plot_time_series(plot_widget, x, y):
    plot_widget.canvas.axes.cla()
    plot_widget.canvas.axes.step(x, y, where='post')
    plot_widget.canvas.axes.get_xaxis().set_tick_params(labelrotation=45.0)
    plot_widget.canvas.draw()
