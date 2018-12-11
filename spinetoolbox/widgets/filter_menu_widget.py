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

from PySide2.QtWidgets import QWidget, QApplication, QVBoxLayout, QListView, QLineEdit, \
    QDialogButtonBox, QMenu, QPushButton, QWidgetAction, QAction, QTableView, QStyle
from PySide2.QtCore import Qt, QTimer, Signal, Slot
from tabularview_models import FilterCheckboxListModel
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
            self.set_ok_index_data()

    def set_ok_index_data(self):
        """Set data for ok index based on data from all other indexes."""
        ok_index = self.model.index(0, 0)
        true_count = 0
        for row_data in self.model._main_data[1:]:
            if row_data[0] == True:
                true_count += 1
        if true_count == len(self.model._main_data) - 1:
            self.model.setData(ok_index, True)
        elif true_count == 0:
            self.model.setData(ok_index, False)
        else:
            self.model.setData(ok_index, None)

    def set_values(self, values):
        """Set values to show in the 'menu'. Reset model using those values and update geometry."""
        self.model.reset_model([[None, "All"]] + values)
        self.set_ok_index_data()
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


class FilterWidget(QWidget):
    okPressed = Signal()
    cancelPressed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)

        # parameters
        self._filter_state = set()
        self._filter_empty_state = False
        self._search_text = ''
        self.search_delay = 200

        # create ui elements
        self._ui_vertical_layout = QVBoxLayout(self)
        self._ui_list = QListView()
        self._ui_edit = QLineEdit()
        self._ui_edit.setPlaceholderText('Search')
        self._ui_edit.setClearButtonEnabled(True)
        self._ui_buttons = QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self._ui_vertical_layout.addWidget(self._ui_edit)
        self._ui_vertical_layout.addWidget(self._ui_list)
        self._ui_vertical_layout.addWidget(self._ui_buttons)


        # add models
        # used to limit search so it doesn't search when typing
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)

        self._filter_model = FilterCheckboxListModel()
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)

        # connect signals
        self._ui_list.clicked.connect(self._filter_model.click_index)
        self._search_timer.timeout.connect(self._filter_list)
        self._ui_edit.textChanged.connect(self._text_edited)
        self._ui_buttons.button(QDialogButtonBox.Ok).clicked.connect(self._apply_filter)
        self._ui_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self._cancel_filter)

    def save_state(self):
        """Saves the state of the FilterCheckboxListModel"""
        self._filter_state = self._filter_model.get_selected()
        self._filter_empty_state = self._filter_model._empty_selected

    def reset_state(self):
        """Sets the state of the FilterCheckboxListModel to saved state"""
        self._filter_model.set_selected(self._filter_state, self._filter_empty_state)

    def clear_filter(self):
        """Selects all items in FilterCheckBoxListModel"""
        self._filter_model.reset_selection()
        self.save_state()

    def has_filter(self):
        """Returns true if any item is filtered in FilterCheckboxListModel false otherwise"""
        return not self._filter_model._all_selected

    def set_filter_list(self, data):
        """Sets the list of items to filter"""
        self._filter_state = set(data)
        self._filter_empty_state = True
        self._filter_model.set_list(self._filter_state)

    def _apply_filter(self):
        """apply current filter and save state"""
        self._filter_model.apply_filter()
        self.save_state()
        self._ui_edit.setText('')
        self.okPressed.emit()

    def _cancel_filter(self):
        """cancel current edit of filter and set the state to the stored state"""
        self._filter_model.remove_filter()
        self.reset_state()
        self._ui_edit.setText('')
        self.cancelPressed.emit()

    def _filter_list(self):
        """filter list with current text"""
        # filter model
        self._filter_model.set_filter(self._search_text)

    def _text_edited(self, new_text):
        """callback for edit text, starts/restarts timer"""
        # start timer after text is edited, restart timer if text
        # is edited before last time is out.
        self._search_text = new_text
        self._search_timer.start(self.search_delay)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    b = QPushButton()
    b.show()
    m = FilterMenu(None)
    b.setMenu(m)

    #w.show()
    sys.exit(app.exec_())
