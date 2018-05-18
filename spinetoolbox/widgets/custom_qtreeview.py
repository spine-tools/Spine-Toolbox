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
Class for a custom QTreeView for the Data Store form.

:author: Manuel Marin <manuelma@kth.se>
:date:   25.4.2018
"""

import logging
from PySide2.QtWidgets import QTreeView, QAbstractItemView
from PySide2.QtCore import Signal, Slot


class CustomQTreeView(QTreeView):
    """Custom QTreeView class.

    Attributes:
        parent (QWidget): The parent of this view
    """

    currentIndexChanged = Signal("QModelIndex", name="currentIndexChanged")
    editKeyPressed = Signal("QModelIndex", name="editKeyPressed")

    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)

    @Slot("QModelIndex", "QModelIndex", name="currentChanged")
    def currentChanged(self, current, previous):
        self.currentIndexChanged.emit(current)

    @Slot("QModelIndex", "EditTrigger", "QEvent", name="edit")
    def edit(self, index, trigger, event):
        if trigger == QTreeView.EditKeyPressed:
            self.editKeyPressed.emit(index)
        return False
