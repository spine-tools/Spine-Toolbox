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

"""Contains Database editor's Commit viewer."""
from PySide6.QtCore import QEventLoop, QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidgetItem,
    QWidget,
)
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, restore_ui, save_ui


class _DBCommitViewer(QWidget):
    """Commit viewer's central widget."""

    def __init__(self, db_mngr, db_map, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_map (DatabaseMapping): database mapping
            parent (QWidget, optional): parent widget
        """
        from ..ui.db_commit_viewer import Ui_DBCommitViewer  # pylint: disable=import-outside-toplevel

        super().__init__(parent=parent)
        self._ui = Ui_DBCommitViewer()
        self._ui.setupUi(self)
        self._db_mngr = db_mngr
        self._db_map = db_map
        self._ui.commit_list.setHeaderLabel("Commits")
        self._ui.commit_list.setIndentation(0)
        self._ui.splitter.setSizes([0.3, 0.7])
        self._ui.splitter.setStretchFactor(0, 0)
        self._ui.splitter.setStretchFactor(1, 1)
        self._ui.affected_items_widget_stack.setCurrentIndex(3)
        for commit in reversed(db_map.get_items("commit")):
            tree_item = QTreeWidgetItem(self._ui.commit_list)
            tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, commit["id"])
            self._ui.commit_list.addTopLevelItem(tree_item)
            index = self._ui.commit_list.indexFromItem(tree_item)
            widget = _CommitItem(commit)
            self._ui.commit_list.setIndexWidget(index, widget)
        self._ui.commit_list.currentItemChanged.connect(self._select_commit)
        self._ui.affected_item_tab_widget.tabBarClicked.connect(self._set_preferred_item_type)
        self._affected_item_widgets = {}
        self._preferred_affected_item_type = None
        self._thread = None
        self._worker = None

    @property
    def splitter(self) -> QSplitter:
        return self._ui.splitter

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _select_commit(self, current, previous):
        """Start a worker thread that fetches affected items for the selected commit.

        Args:
            current (QTreeWidgetItem): currently selected commit item
            previous (QTreeWidgetItem): previously selected commit item
        """
        commit_id = current.data(0, Qt.ItemDataRole.UserRole + 1)
        self._ui.affected_items_widget_stack.setCurrentIndex(2)
        self._ui.affected_item_tab_widget.clear()
        for widget in self._affected_item_widgets.values():
            widget.table.setRowCount(0)
        self._launch_new_worker(commit_id)

    def _launch_new_worker(self, commit_id):
        """Starts a new worker thread.

        If a thread is already running, it is quite before starting a new one.

        Args:
            commit_id (TempId): commit id
        """
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = QThread(self)
        self._worker = Worker(self._db_mngr, self._db_map, commit_id)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.chunk_ready.connect(self._process_affected_items)
        self._worker.max_ids_reached.connect(self._max_affected_items_fetched)
        self._worker.all_ids_fetched.connect(self._all_affected_items_fetched)
        self._worker.finished.connect(self._finish_work)
        self._thread.start()

    @Slot(str, list, list)
    def _process_affected_items(self, item_type, keys, items):
        """Adds a fetched chunk of affected items to appropriate table view.

        Args:
            item_type (str): fethced item type
            keys (Sequence of str): item keys
            items (Sequence of Sequence): list of items, each item being a list of labels;
                items must have the same length as keys
        """
        affected_items_widget = self._affected_item_widgets.get(item_type)
        if affected_items_widget is None:
            affected_items_widget = _AffectedItemsWidget()
            self._affected_item_widgets[item_type] = affected_items_widget
            item_table = affected_items_widget.table
            item_table.setColumnCount(len(keys))
            item_table.setHorizontalHeaderLabels(keys)
        else:
            item_table = affected_items_widget.table
        if self._ui.affected_item_tab_widget.indexOf(affected_items_widget) == -1:
            self._ui.affected_item_tab_widget.addTab(affected_items_widget, item_type)
            if self._preferred_affected_item_type is None:
                self._preferred_affected_item_type = item_type
            if item_type == self._preferred_affected_item_type:
                self._ui.affected_item_tab_widget.setCurrentWidget(affected_items_widget)
        if self._ui.affected_items_widget_stack.currentIndex() != 0:
            self._ui.affected_items_widget_stack.setCurrentIndex(0)
        for item in items:
            row = item_table.rowCount()
            item_table.insertRow(row)
            for column, label in enumerate(item):
                cell = QTableWidgetItem(label)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item_table.setItem(row, column, cell)

    @Slot(str, int)
    def _max_affected_items_fetched(self, item_type, still_available):
        """Updates the fetch status label.

        Args:
            item_type (str): item type
            still_available (int): number of items left unfetched
        """
        label = self._affected_item_widgets[item_type].label
        label.setVisible(True)
        label.setText(f"...and {still_available} {item_type} items more.")

    @Slot(str)
    def _all_affected_items_fetched(self, item_type):
        """Hides the fetch status label.

        Args:
            item_type (str): item type
        """
        self._affected_item_widgets[item_type].label.setVisible(False)

    @Slot()
    def _finish_work(self):
        """Quits the worker thread if it is running."""
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._worker = None
            self._thread = None
            if self._ui.affected_item_tab_widget.count() == 0:
                self._ui.affected_items_widget_stack.setCurrentIndex(1)

    def tear_down(self):
        """Tears down the widget."""
        self._finish_work()

    @Slot(int)
    def _set_preferred_item_type(self, preferred_tab_index):
        """Sets the preferred item type for affected items.

        The tab showing the preferred type is selected automatically as the current tab when/if it gets fetched.

        Args:
            preferred_tab_index (int): index of the preferred tab
        """
        self._preferred_affected_item_type = self._ui.affected_item_tab_widget.tabText(preferred_tab_index)


class _CommitItem(QWidget):
    """A widget to show commit message, author and data on a QTreeWidget."""

    def __init__(self, commit, parent=None):
        """
        Args:
            commit (dict): commit database item
            parent (QWidget, optional): parent widget
        """
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


class _AffectedItemsWidget(QWidget):
    """A composite widget that contains a table and a label."""

    def __init__(self):
        from ..ui.commit_viewer_affected_item_info import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__()
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.fetch_status_label.setVisible(False)

    @property
    def table(self) -> QTableWidget:
        return self._ui.affected_items_table

    @property
    def label(self) -> QLabel:
        return self._ui.fetch_status_label


class CommitViewer(QMainWindow):
    """Commit viewer window."""

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
            tab_widget.addTab(widget, db_mngr.name_registry.display_name(db_map.sa_url))
        restore_ui(self, self._qsettings, "commitViewer")
        self._qsettings.beginGroup("commitViewer")
        current = self.centralWidget().widget(self._current_index)
        current.splitter.restoreState(self._qsettings.value("splitterState"))
        self._qsettings.endGroup()
        tab_widget.currentChanged.connect(self._carry_splitter_state)

    @Slot(int)
    def _carry_splitter_state(self, index):
        """Ensures that splitters have the same state in all tabs.

        Args:
            index (int): current database tab index
        """
        previous = self.centralWidget().widget(self._current_index)
        current = self.centralWidget().widget(index)
        self._current_index = index
        state = previous.splitter.saveState()
        current.splitter.restoreState(state)

    def closeEvent(self, ev):
        super().closeEvent(ev)
        save_ui(self, self._qsettings, "commitViewer")
        tab_view: QTabWidget = self.centralWidget()
        current = tab_view.widget(self._current_index)
        self._qsettings.beginGroup("commitViewer")
        self._qsettings.setValue("splitterState", current.splitter.saveState())
        self._qsettings.endGroup()
        for tab_index in range(tab_view.count()):
            commit_widget = tab_view.widget(tab_index)
            commit_widget.tear_down()


class Worker(QObject):
    """Worker that fetches affected items.

    The items are fetched in chunks which makes it possible to quit the thread mid-execution.
    There is also a hard limit to how many items are fetched.
    """

    SOFT_MAX_IDS = 400
    HARD_EXTRA_ID_LIMIT = 100
    CHUNK_SIZE = 50

    max_ids_reached = Signal(str, int)
    all_ids_fetched = Signal(str)
    chunk_ready = Signal(str, list, list)
    finished = Signal()

    def __init__(self, db_mngr, db_map, commit_id):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_map (DatabaseMapping): database mapping
            commit_id (TempId): commit id
        """
        super().__init__()
        self._db_mngr = db_mngr
        self._db_map = db_map
        self._commit_id = commit_id

    @Slot()
    def run(self):
        """Fetches affected items."""
        try:
            for item_type, ids in self._db_mngr.get_items_for_commit(self._db_map, self._commit_id).items():
                items = []
                keys = None
                max_reached = False
                id_count = 0
                for id_count, id_ in enumerate(ids):
                    db_item = self._db_mngr.get_item(self._db_map, item_type, id_)
                    if keys is None:
                        keys = [key for key in db_item.extended() if not any(word in key for word in ("id", "parsed"))]
                    items.append([self._parse_value(self._db_mngr, self._db_map, db_item, key) for key in keys])
                    if id_count % self.CHUNK_SIZE == 0:
                        self.thread().eventDispatcher().processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
                        QThread.yieldCurrentThread()
                        if id_count != 0:
                            self.chunk_ready.emit(item_type, keys, items)
                            items = []
                    if id_count + 1 >= self.SOFT_MAX_IDS and len(ids) - id_count > self.HARD_EXTRA_ID_LIMIT:
                        max_reached = True
                        break
                if items:
                    self.chunk_ready.emit(item_type, keys, items)
                if max_reached:
                    self.max_ids_reached.emit(item_type, len(ids) - id_count - 1)
                else:
                    self.all_ids_fetched.emit(item_type)
        finally:
            self.finished.emit()

    @staticmethod
    def _parse_value(db_mngr, db_map, item, key):
        """Converts item field values to something more displayable.

        Args:
            db_mngr (SpineDBManager): database manager
            db_map (DatabaseMapping): database mapping
            item (PublicItem): database item
            key (str): value's key

        Returns:
            str: displayable presentation of the value
        """
        if item.item_type in ("parameter_definition", "parameter_value", "list_value") and key in (
            "value",
            "default_value",
        ):
            return db_mngr.get_value(db_map, item, role=Qt.ItemDataRole.DisplayRole)
        value = item[key]
        if isinstance(value, (tuple, list)):
            return DB_ITEM_SEPARATOR.join(value)
        return value
