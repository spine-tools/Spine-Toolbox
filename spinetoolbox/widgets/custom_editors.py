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
Custom editors for model/view programming.


:author: M. Marin (KTH)
:date:   2.9.2018
"""
from PySide2.QtCore import Qt, Slot, Signal, QRect, QItemSelectionModel, QPoint
from PySide2.QtWidgets import QComboBox, QLineEdit, QWidget, QHBoxLayout, QToolButton, QVBoxLayout, \
    QTableView, QStyle
from PySide2.QtGui import QIntValidator, QStandardItemModel, QStandardItem


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, current_text, items):
        self.addItems(items)
        if current_text and current_text in items:
            self.setCurrentText(current_text)
        else:
            self.setCurrentIndex(-1)
        self.activated.connect(lambda: self.data_committed.emit())
        self.showPopup()

    def data(self):
        return self.currentText()


class CustomLineEditor(QLineEdit):
    """A custom QLineEdit to handle data from models.

    Attributes:
        parent (QWidget): the widget that wants to edit the data
    """
    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)

    def set_data(self, data):
        if data is not None:
            self.setText(str(data))
        if type(data) is int:
            self.setValidator(QIntValidator(self))

    def data(self):
        return self.text()


class MultipleOptionsEditor(QWidget):
    """A widget to edit fields with multiple options."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent, option, index):
        """Initialize class."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.model = QStandardItemModel(self)
        self.view = QTableView(self)
        self.view.setModel(self.model)
        self.view.verticalHeader().hide()
        self.view.horizontalHeader().hide()
        self.view.setShowGrid(False)
        self.view.setMouseTracking(True)
        self.view.mouseMoveEvent = self._view_mouse_move_event
        self.view.mousePressEvent = self._view_mouse_press_event
        self.button = QToolButton(self)
        self.button.setText("Ok")
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.button.clicked.connect(self._handle_ok_button_clicked)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        x_offset = parent.parent().columnViewportPosition(index.column())
        y_offset = parent.parent().rowViewportPosition(index.row())
        self.position = parent.mapToGlobal(QPoint(0, 0)) + QPoint(x_offset, y_offset)
        self.option_rect_width = option.rect.width()

    def _view_mouse_move_event(self, event):
        """Highlight current row."""
        index = self.view.indexAt(event.pos())
        self.view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
        event.accept()

    def _view_mouse_press_event(self, event):
        """Toggle checked state."""
        index = self.view.indexAt(event.pos())
        item = self.model.itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        event.accept()

    @Slot("bool", name="_handle_ok_button_clicked")
    def _handle_ok_button_clicked(self, checked=False):
        """Called when user pressed Ok."""
        self.data_committed.emit()

    def set_data(self, item_names, current_item_names):
        """Set data and update geometry."""
        for name in item_names:
            qitem = QStandardItem(name)
            if name in current_item_names:
                qitem.setCheckState(Qt.Checked)
            else:
                qitem.setCheckState(Qt.Unchecked)
            self.model.appendRow(qitem)
        self.view.resizeColumnsToContents()
        table_width = self.view.horizontalHeader().length() + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2
        width = max(self.option_rect_width, table_width)
        height = self.view.verticalHeader().length() + self.button.height()
        parent_height = self.parent().height()
        self.setFixedHeight(min(height, parent_height / 2) + 2)
        self.setFixedWidth(width)
        self.view.horizontalHeader().setMinimumSectionSize(width)
        self.button.setFixedWidth(width)
        self.move(self.position)

    def data(self):
        return ",".join(q.text() for q in self.model.findItems('*', Qt.MatchWildcard) if q.checkState() == Qt.Checked)


class ObjectNameListEditor(QWidget):
    """A custom QWidget to edit object name lists."""

    data_committed = Signal(name="data_committed")

    def __init__(self, parent):
        super().__init__(parent)
        self.missing_dimensions = set()
        self.combos = list()
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_data(self, object_icons, object_class_names, object_names, object_names_dict):
        for i, object_class_name in enumerate(object_class_names):
            combo = QComboBox(self)
            model = QStandardItemModel()
            icon = object_icons[i]
            qitem = QStandardItem(icon, object_class_name)
            qitem.setFlags(~Qt.ItemIsSelectable)
            model.appendRow(qitem)
            all_object_names = object_names_dict[object_class_name]
            for object_name in all_object_names:
                qitem = QStandardItem(object_name)
                model.appendRow(qitem)
            combo.setModel(model)
            combo.insertSeparator(1)
            combo.activated.connect(lambda index, i=i: self.remove_missing_dimension(i))
            self.layout().addWidget(combo)
            self.combos.append(combo)
            try:
                object_name = object_names[i]
            except IndexError:
                self.missing_dimensions.add(i)
                continue
            if object_name:
                combo.setCurrentText(object_name)
            else:
                self.missing_dimensions.add(i)

    def remove_missing_dimension(self, dim):
        combo = self.combos[dim]
        try:
            self.missing_dimensions.remove(dim)
        except KeyError:
            pass
        if not self.missing_dimensions:
            self.data_committed.emit()

    def data(self):
        object_name_list = list()
        for combo in self.combos:
            if combo.currentIndex() == 0:
                object_name = ''
            else:
                object_name = combo.currentText()
            object_name_list.append(object_name)
        return ','.join(object_name_list)
