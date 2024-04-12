######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains the CommitViewer class."""
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QLabel,
)
from PySide6.QtCore import Qt, Slot
from spinetoolbox.helpers import restore_ui, save_ui, busy_effect, DB_ITEM_SEPARATOR


class _DBCommitViewer(QWidget):
    def __init__(self, db_mngr, db_map, parent=None):
        super().__init__(parent=parent)
        self._db_mngr = db_mngr
        self._db_map = db_map
        self._commit_list = QTreeWidget(self)
        self._commit_list.setHeaderLabel("Commits")
        self._commit_list.setIndentation(0)
        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([0.3, 0.7])
        self._affected_items = QTreeWidget(self)
        self._affected_items.setHeaderLabel("Affected items")
        self.splitter.addWidget(self._commit_list)
        self.splitter.addWidget(self._affected_items)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout = self.layout()
        layout.addWidget(self.splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for commit in reversed(db_map.get_items("commit")):
            tree_item = QTreeWidgetItem(self._commit_list)
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, commit["id"])
            self._commit_list.addTopLevelItem(tree_item)
            index = self._commit_list.indexFromItem(tree_item)
            widget = _CommitItem(commit)
            self._commit_list.setIndexWidget(index, widget)
        self._commit_list.currentItemChanged.connect(self._select_commit)

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _select_commit(self, current, previous):
        self._commit_list.setDisabled(True)
        self._do_select_commit(current)
        self._commit_list.setEnabled(True)

    @busy_effect
    def _do_select_commit(self, current):
        commit_id = current.data(0, Qt.ItemDataRole.UserRole + 1)
        self._affected_items.clear()
        # TODO: If no items, show message that data was overwritten by a further commit
        for item_type, ids in self._db_mngr.get_items_for_commit(self._db_map, commit_id).items():
            top_level_item = QTreeWidgetItem([item_type])
            self._affected_items.addTopLevelItem(top_level_item)
            bottom_level_item = QTreeWidgetItem(top_level_item)
            bottom_level_item.setFlags(bottom_level_item.flags() & ~Qt.ItemIsSelectable)
            index = self._affected_items.indexFromItem(bottom_level_item)
            items = [self._db_mngr.get_item(self._db_map, item_type, id_) for id_ in ids]
            widget = _AffectedItemsFromOneTable(items, parent=self._affected_items)
            self._affected_items.setIndexWidget(index, widget)
            top_level_item.setExpanded(True)


class _CommitItem(QWidget):
    """A widget to show commit message, author and data on a QTreeWidget."""

    def __init__(self, commit, parent=None):
        super().__init__(parent=parent)
        comment = QLabel(str(commit["comment"]) or "<no comment>")
        user = QLabel(str(commit["user"]))
        date = QLabel(str(commit["date"]))
        layout = QGridLayout()
        self.setLayout(layout)
        ss = "QLabel{color:gray; font: italic;}"
        user.setStyleSheet(ss)
        date.setStyleSheet(ss)
        layout.addWidget(comment, 0, 0, 1, -1)
        layout.addWidget(user, 1, 0)
        layout.addWidget(date, 1, 1)


class _AffectedItemsFromOneTable(QTreeWidget):
    """A widget to show all the items from one table that are affected by a commit."""

    def __init__(self, items, parent=None):
        super().__init__(parent=parent)
        self.setIndentation(0)
        first = next(iter(items), None)
        if first is None:
            return
        self._margin = 6
        keys = [key for key in first._extended() if not any(word in key for word in ("id", "parsed"))]
        self.setHeaderLabels(keys)
        tree_items = [QTreeWidgetItem([self._parse_value(item[key]) for key in keys]) for item in items]
        self.addTopLevelItems(tree_items)
        last = tree_items[-1]
        rect = self.visualItemRect(last)
        self._height = rect.bottom()
        for k, _ in enumerate(keys):
            self.resizeColumnToContents(k)

    @staticmethod
    def _parse_value(value):
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, (tuple, list)):
            return DB_ITEM_SEPARATOR.join(value)
        return value

    def moveEvent(self, ev):
        if ev.pos().x() > 0:
            self.move(self._margin, ev.pos().y())
            offset = ev.pos().x() - self._margin
            self.resize(self.size().width() + offset - 2, self.size().height())
            return
        super().moveEvent(ev)

    def sizeHint(self):
        size = super().sizeHint()
        height = self._height + self.frameWidth() * 2 + self.header().height() + self._margin
        scroll_bar = self.horizontalScrollBar()
        if scroll_bar.isVisible():
            height += scroll_bar.height()
        height = min(size.height(), height)
        size.setHeight(height)
        return size


class CommitViewer(QMainWindow):
    def __init__(self, qsettings, db_mngr, *db_maps, parent=None):
        """
        Args:
            qsettings (QSettings): application settings
            db_mngr (SpineDBManager): database manager
            *db_maps: database mappings to view
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent=parent)
        self.setWindowTitle("Commit viewer")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        tab_widget = QTabWidget(self)
        self.setCentralWidget(tab_widget)
        self._qsettings = qsettings
        self._db_mngr = db_mngr
        self._db_maps = db_maps
        self._current_index = 0
        for db_map in self._db_maps:
            widget = _DBCommitViewer(self._db_mngr, db_map)
            tab_widget.addTab(widget, db_map.codename)
        restore_ui(self, self._qsettings, "commitViewer")
        self._qsettings.beginGroup("commitViewer")
        current = self.centralWidget().widget(self._current_index)
        current.splitter.restoreState(self._qsettings.value("splitterState"))
        self._qsettings.endGroup()
        tab_widget.currentChanged.connect(self._carry_splitter_state)

    @Slot(int)
    def _carry_splitter_state(self, index):
        previous = self.centralWidget().widget(self._current_index)
        current = self.centralWidget().widget(index)
        self._current_index = index
        state = previous.splitter.saveState()
        current.splitter.restoreState(state)

    def closeEvent(self, ev):
        super().closeEvent(ev)
        save_ui(self, self._qsettings, "commitViewer")
        current = self.centralWidget().widget(self._current_index)
        self._qsettings.beginGroup("commitViewer")
        self._qsettings.setValue("splitterState", current.splitter.saveState())
        self._qsettings.endGroup()
