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

from PySide2.QtWidgets import QWidget, QApplication, QVBoxLayout, QListView, QLineEdit, QDialogButtonBox, QMenu, QPushButton, QWidgetAction, QAction
from PySide2.QtCore import QTimer, Signal
from tabularview_models import FilterCheckboxListModel


class FilterMenu(QMenu):
    filterChanged = Signal(object, set, bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._remove_filter = QAction('Remove filters', None)
        self._filter = FilterWidget()
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._remove_filter)
        self.addAction(self._filter_action)
        
        # add connections
        self.aboutToHide.connect(self._cancel_filter)
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self._clear_filter)
        self._filter.okPressed.connect(self._change_filter)
        self._filter.cancelPressed.connect(self.hide)

    def add_items_to_filter_list(self, items):
        self._filter._filter_model.add_item(items)
        self._filter.save_state()

    def remove_items_from_filter_list(self, items):
        self._filter._filter_model.remove_items(items)
        self._filter.save_state()
    
    def set_filter_list(self, data):
        self._filter.set_filter_list(data)

    def _clear_filter(self):
        self._filter.clear_filter()
        self._change_filter()

    def _check_filter(self):
        self._remove_filter.setEnabled(self._filter.has_filter())

    def _cancel_filter(self):
        self._filter._cancel_filter()

    def _change_filter(self):
        valid_values = set(self._filter._filter_state)
        if self._filter._filter_empty_state:
            valid_values.add(None)
        self.filterChanged.emit(self, valid_values, self._filter.has_filter())
        self.hide()


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