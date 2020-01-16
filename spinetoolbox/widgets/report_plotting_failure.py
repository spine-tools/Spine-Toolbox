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
Functions to report failures in plotting to the user.

:author: A. Soininen (VTT)
:date:   10.7.2019
"""

from PySide2.QtWidgets import QMessageBox


def report_plotting_failure(error, parent_widget):
    """Reports a PlottingError exception to the user."""
    QMessageBox.warning(parent_widget, "Plotting Failed", error.message)
