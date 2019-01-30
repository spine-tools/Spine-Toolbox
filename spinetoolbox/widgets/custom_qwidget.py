######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for PivotModel class.

:author: P. Vennström (VTT)
:date:   4.12.2018
"""

from PySide2.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, \
    QMenu, QPushButton, QAction, QTableView, QStyle, QToolBar, QStyleOptionMenuItem
from PySide2.QtCore import Qt, QTimer, Signal, Slot
from PySide2.QtGui import QPixmap, QPainter
from models import MinimalTableModel
from widgets.custom_delegates import CheckBoxDelegate


class AutoFilterWidget(QWidget):
    """A widget to show the auto filter 'menu'."""
    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.model = MinimalTableModel(self)
        self.model.flags = self.model_flags
        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        check_box_delegate = CheckBoxDelegate(self)
        self.view.setItemDelegateForColumn(0, check_box_delegate)
        check_box_delegate.data_committed.connect(self._handle_check_box_data_committed)
        self.button = QPushButton("Ok", self)
        self.button.setFlat(True)
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.hide)
        self.hide()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

    def model_flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 1:
            return ~Qt.ItemIsEditable
        return Qt.ItemIsEditable

    @Slot("QModelIndex", name="_handle_check_box_data_committed")
    def _handle_check_box_data_committed(self, index):
        """Called when checkbox delegate wants to edit data. Toggle the index's value."""
        data = index.data(Qt.EditRole)
        model_data = self.model._main_data
        row_count = self.model.rowCount()
        if index.row() == 0:
            # Ok row
            value = data in (None, False)
            for row in range(row_count):
                model_data[row][0] = value
            self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(row_count - 1, 0))
        else:
            # Data row
            self.model.setData(index, not data)
            self.set_all_index_data()

    def set_all_index_data(self):
        """Set data for 'all' index based on data from all other indexes."""
        all_index = self.model.index(0, 0)
        true_count = 0
        for row_data in self.model._main_data[1:]:
            if row_data[0] == True:
                true_count += 1
        if true_count == len(self.model._main_data) - 1:
            self.model.setData(all_index, True)
        elif true_count == 0:
            self.model.setData(all_index, False)
        else:
            self.model.setData(all_index, None)

    def set_values(self, values):
        """Set values to show in the 'menu'. Reset model using those values and update geometry."""
        self.model.reset_model([[None, "All"]] + values)
        self.set_all_index_data()
        self.view.horizontalHeader().hideSection(2)  # Column 2 holds internal data (cls_id_set)
        self.view.resizeColumnsToContents()
        width = self.view.horizontalHeader().length() + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        self.setFixedWidth(width + 2)
        height = self.view.verticalHeader().length() + self.button.height()
        parent_height = self.parent().height()
        self.setFixedHeight(min(height, parent_height / 2) + 2)

    def set_section_height(self, height):
        """Set vertical header default section size as well as button height."""
        self.view.verticalHeader().setDefaultSectionSize(height)
        self.button.setFixedHeight(height)


class ZoomWidget(QWidget):
    """A widget for a QWidgetAction providing zoom actions for the graph view.

    Attributes
        parent (QWidget): the widget's parent
    """

    minus_pressed = Signal(name="minus_pressed")
    plus_pressed = Signal(name="plus_pressed")
    reset_pressed = Signal(name="reset_pressed")

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.option = QStyleOptionMenuItem()
        zoom_action = QAction("Zoom")
        QMenu(parent).initStyleOption(self.option, zoom_action)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        tool_bar = QToolBar(self)
        tool_bar.setFixedHeight(self.option.rect.height())
        minus_action = tool_bar.addAction("-")
        reset_action = tool_bar.addAction("Reset")
        plus_action = tool_bar.addAction("+")
        layout.addSpacing(self.option.rect.width())
        layout.addWidget(tool_bar)
        minus_action.setToolTip("Zoom out")
        reset_action.setToolTip("Reset zoom")
        plus_action.setToolTip("Zoom in")
        minus_action.triggered.connect(lambda x: self.minus_pressed.emit())
        plus_action.triggered.connect(lambda x: self.plus_pressed.emit())
        reset_action.triggered.connect(lambda x: self.reset_pressed.emit())

    def paintEvent(self, event):
        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_MenuItem, self.option, painter)
        super().paintEvent(event)
