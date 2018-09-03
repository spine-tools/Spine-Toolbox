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
Class for a custom QTableView that allows copy-paste, and maybe some other feature we may think of.

:author: Manuel Marin <manuelma@kth.se>
:date:   18.5.2018
"""

import logging
from PySide2.QtWidgets import QTableView, QApplication, QMenu, QAction
from PySide2.QtCore import Qt, Signal, Slot, QItemSelection, QItemSelectionModel, QPoint, QSignalMapper, \
    QModelIndex
from PySide2.QtGui import QKeySequence
from widgets.custom_menus import QOkMenu


class CustomQTableView(QTableView):
    """Custom QTableView class with copy-paste functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initialize the class."""
        super().__init__(parent)
        # self.editing = False
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = self.clipboard.text()

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            selection = self.selectionModel().selection()
            if not selection:
                super().keyPressEvent(event)
                return
            # Take only the first selection in case of multiple selection.
            first = selection.first()
            content = ""
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            for i in range(first.top(), first.bottom()+1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right()+1):
                    if h_header.isSectionHidden(j):
                        continue
                    row.append(str(self.model().index(i, j).data(Qt.DisplayRole)))
                content += "\t".join(row)
                content += "\n"
            self.clipboard.setText(content)
        elif event.matches(QKeySequence.Paste):
            if not self.clipboard_text:
                super().keyPressEvent(event)
                return
            top_left_index = self.currentIndex()
            if not top_left_index.isValid():
                super().keyPressEvent(event)
                return
            data = [line.split('\t') for line in self.clipboard_text.split('\n')[0:-1]]
            self.selectionModel().select(top_left_index, QItemSelectionModel.Select)
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            row = top_left_index.row()
            for line in data:
                if v_header.isSectionHidden(row):
                    row += 1
                column = top_left_index.column()
                for value in line:
                    if h_header.isSectionHidden(column):
                        column += 1
                    sibling = top_left_index.sibling(row, column)
                    if sibling.flags() & Qt.ItemIsEditable:
                        self.model().setData(sibling, value, Qt.EditRole)
                        self.selectionModel().select(sibling, QItemSelectionModel.Select)
                    column += 1
                row += 1
        else:
            super().keyPressEvent(event)


    # TODO: This below was intended to improve navigation while setting edit trigger on current changed.
    # But it's too try-hard. Better edit on double click like excel, which is what most people are used to anyways
    # def moveCursor(self, cursor_action, modifiers):
    #     """Don't move to next index if the self.editing flag is set.
    #     """
    #     if self.editing and cursor_action == self.CursorAction.MoveNext:
    #         self.editing = False
    #         return self.currentIndex()
    #     return super().moveCursor(cursor_action, modifiers)

    # def edit(self, index, trigger, event):
    #     self.editing = True
    #     return super().edit(index, trigger, event)


class ParameterTableView(CustomQTableView):
    """Custom QTableView class with autofilter functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    filter_changed = Signal("QObject", "int", "QStringList", name="filter_changed")
    filter_triggered = Signal("QObject", name="filter_triggered")

    def __init__(self, parent):
        """Initialize the class."""
        super().__init__(parent)
        self.filter_action_list = list()
        self.action_all = None
        self.filter_text = None
        self.filter_column = None

    def setModel(self, model):
        """Disconnect sectionPressed signal, only connect it to show_filter_menu slot.
        Otherwise the column is selected when pressing on the header."""
        super().setModel(model)
        self.horizontalHeader().sectionPressed.disconnect()
        self.horizontalHeader().sectionPressed.connect(self.show_filter_menu)

    @Slot(int, name="show_filter_menu")
    def show_filter_menu(self, logical_index):
        """Called when user clicks on a horizontal section header.
        Show the menu to select a filter."""
        self.filter_column = logical_index
        model = self.model()
        filter_menu = QOkMenu(self)
        self.filter_action_list = list()
        # Add 'All' action
        self.action_all = QAction("All", self)
        self.action_all.setCheckable(True)
        self.action_all.triggered.connect(self.action_all_triggered)
        filter_menu.addAction(self.action_all)
        filter_menu.addSeparator()
        # Get values from model, after the application of all filters and subfilters from other columns
        values = list()
        source_model = model.sourceModel()
        for source_row in range(source_model.rowCount()):
            # Skip values rejected by filter
            if not model.filter_accept_rows(source_row, QModelIndex()):
                continue
            # Skip values rejected by subfilters from *other* columns
            if not model.subfilter_accept_rows(source_row, QModelIndex(), skip_source_column=[self.filter_column]):
                continue
            data = source_model.index(source_row, self.filter_column).data(Qt.DisplayRole)
            if data is None:
                continue
            values.append(data)
        # Get values currently filtered in this column
        try:
            filtered_values = model.subrule_dict[self.filter_column]
        except KeyError:
            filtered_values = list()
        # Add filter actions
        self.filter_action_list = list()
        for i, value in enumerate(sorted(list(set(values)))):
            action = QAction(str(value), self)
            action.setCheckable(True)
            action.triggered.connect(self.update_action_all_checked)
            filter_menu.addAction(action)
            self.filter_action_list.append(action)
            if value in filtered_values:
                action.setChecked(True)
            action.trigger()  # Note: this toggles the checked property
        # 'Ok' action
        action_ok = QAction("Ok", self)
        action_ok.triggered.connect(self.update_and_apply_filter)
        filter_menu.addSeparator()
        filter_menu.addAction(action_ok)
        header_pos = self.mapToGlobal(self.horizontalHeader().pos())
        pos_x = header_pos.x() + self.horizontalHeader().sectionViewportPosition(self.filter_column)
        pos_y = header_pos.y() + self.horizontalHeader().height()
        filter_menu.exec_(QPoint(pos_x, pos_y))

    @Slot("bool", name="update_action_all_checked")
    def update_action_all_checked(self, checked=False):
        """Called when one filter action is triggered.
        In case they are all checked, check to 'All' action too.
        """
        self.action_all.setChecked(all([a.isChecked() for a in self.filter_action_list]))

    @Slot("bool", name="action_all_triggered")
    def action_all_triggered(self, checked=False):
        """Check or uncheck all filter actions."""
        for action in self.filter_action_list:
            action.setChecked(checked)

    @Slot(name="apply_filter")
    def update_and_apply_filter(self):
        """Called when user clicks Ok in a filter. Emit `filter_triggered` signal."""
        filter_text_list = list()
        for action in self.filter_action_list:
            if not action.isChecked():
                filter_text_list.append(action.text())
        self.filter_changed.emit(self.model(), self.filter_column, filter_text_list)
