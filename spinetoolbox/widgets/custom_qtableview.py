#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Class for a custom QTableView for the Data store form.

:author: Manuel Marin <manuelma@kth.se>
:date:   18.5.2018
"""

import logging
from PySide2.QtWidgets import QTableView, QAbstractItemView
from PySide2.QtCore import Signal, Slot


class CustomQTableView(QTableView):
    """Custom QTableView class.

    Attributes:
        parent (QWidget): The parent of this view
    """


    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)


    def edit(self, index, trigger=None, event=None):

        logging.debug(event)
        if trigger == QAbstractItemView.NoEditTriggers:
            logging.debug("noeditt")
        elif trigger == QAbstractItemView.CurrentChanged:
            logging.debug("currentch")
        elif trigger == QAbstractItemView.DoubleClicked:
            logging.debug("doublecl")
        elif trigger == QAbstractItemView.SelectedClicked:
            logging.debug("selcl")
        elif trigger == QAbstractItemView.EditKeyPressed:
            logging.debug("editkey")
        elif trigger == QAbstractItemView.AnyKeyPressed:
            logging.debug("anyke")
        elif trigger == QAbstractItemView.AllEditTriggers:
            logging.debug("all")
        if trigger is not None:
            return super().edit(index, trigger, event)
        return super().edit(index)
