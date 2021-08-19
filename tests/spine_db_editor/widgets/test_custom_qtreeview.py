######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for DB editor's custom ``QTreeView`` classes.

:author: A. Soininen
:date:   17.8.2021
"""
import os.path
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from time import sleep
from types import MethodType
import unittest
from unittest import mock
from PySide2.QtCore import QObject, Signal, Slot, QItemSelectionModel
from PySide2.QtWidgets import QApplication

from spinedb_api import DiffDatabaseMapping, from_database, import_parameter_value_lists
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.helpers import signal_waiter


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def _common_setup(self, url, create):
        self._cell_editor = None
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=create)
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "database"})
            self._db_editor.pivot_table_model = mock.MagicMock()

    def _common_tear_down(self):
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None

    def _append_value_list(self, list_name):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        last_row = model.rowCount(root_index)
        list_name_index = model.index(last_row - 1, 0, root_index)
        self._write_to_index(list_name_index, list_name)
        return list_name_index

    def _write_to_index(self, index, value):
        delegate = self._db_editor.ui.treeView_parameter_value_list.itemDelegate(index)
        if self._cell_editor is None:
            original_create_editor = delegate.createEditor

            def create_and_store_editor(instance, parent, option, target_index):
                self._cell_editor = original_create_editor(parent, option, target_index)
                return self._cell_editor

            delegate.createEditor = MethodType(create_and_store_editor, delegate)
        self._db_editor.ui.treeView_parameter_value_list.setCurrentIndex(index)
        self._db_editor.ui.treeView_parameter_value_list.edit(index)
        self._cell_editor.setText(value)
        delegate.commitData.emit(self._cell_editor)

    def _commit_changes_to_database(self):
        with mock.patch.object(self._db_mngr, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = "Add parameter value list."
            with signal_waiter(self._db_mngr.session_committed) as waiter:
                self._db_editor.ui.actionCommit.trigger()
                waiter.wait()


class TestParameterValueListTreeViewWithInMemoryDatabase(_Base):
    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def test_empty_tree_has_correct_contents(self):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        self.assertTrue(root_index.isValid())
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self.assertEqual(model.rowCount(list_name_index), 0)

    def test_add_parameter_value_list(self):
        list_name_index = self._append_value_list("a_value_list")
        self.assertEqual(list_name_index.data(), "a_value_list")
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        self.assertEqual(model.rowCount(list_name_index), 1)
        new_value_index = model.index(0, 0, list_name_index)
        self.assertEqual(new_value_index.data(), "Enter new list value here...")
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 2)
        new_name_index = model.index(1, 0, root_index)
        self.assertEqual(new_name_index.data(), "Type new list name here...")
        self.assertEqual(model.rowCount(new_name_index), 0)

    def test_add_list_then_remove_it(self):
        list_name_index = self._append_value_list("a_value_list")
        self.assertEqual(list_name_index.data(), "a_value_list")
        view = self._db_editor.ui.treeView_parameter_value_list
        view.selectionModel().select(list_name_index, QItemSelectionModel.ClearAndSelect)
        view.remove_selected()
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")

    def test_add_two_parameter_value_list_values(self):
        list_name_index = self._append_value_list("a_value_list")
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        value_index1 = model.index(0, 0, list_name_index)
        self._write_to_index(value_index1, "value_1")
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_1")
        self.assertEqual(model.rowCount(list_name_index), 2)
        value_index2 = model.index(1, 0, list_name_index)
        self._write_to_index(value_index2, "value_2")
        while model.rowCount(list_name_index) != 3:
            QApplication.processEvents()
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(db_access.lists[i].name, "a_value_list")
                self.assertEqual(from_database(db_access.lists[i].value), expected_value)


class TestParameterValueListTreeViewWithExistingDatabase(_Base):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.cell_editor = None
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_parameter_value_lists(db_map, (("value_list_1", "value_1"), ("value_list_1", "value_2")))
        db_map.commit_session("Add parameter value list.")
        db_map.connection.close()
        self._common_setup(url, create=False)
        QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        self._temp_dir.cleanup()

    def test_tree_has_correct_initial_contents(self):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 2)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "value_list_1")
        self.assertEqual(model.rowCount(list_name_index), 3)
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_1")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self.assertEqual(model.index(2, 0, list_name_index).data(), "Enter new list value here...")
        list_name_index = model.index(1, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")

    def test_remove_value(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        value_index = model.index(0, 0, list_name_index)
        view.selectionModel().setCurrentIndex(value_index, QItemSelectionModel.ClearAndSelect)
        view.remove_selected()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 2)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "value_list_1")
        self.assertEqual(model.rowCount(list_name_index), 2)
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_2")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "Enter new list value here...")
        list_name_index = model.index(1, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 1)
            self.assertEqual(db_access.lists[0].name, "value_list_1")
            self.assertEqual(from_database(db_access.lists[0].value), "value_2")

    def test_remove_list(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        view.selectionModel().setCurrentIndex(list_name_index, QItemSelectionModel.ClearAndSelect)
        with signal_waiter(self._db_mngr.parameter_value_lists_removed) as waiter:
            view.remove_selected()
            waiter.wait()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(model.rowCount(list_name_index), 0)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 0)

    def test_removing_all_values_from_list_removes_the_list_too(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        view.selectionModel().select(model.index(0, 0, list_name_index), QItemSelectionModel.ClearAndSelect)
        view.selectionModel().select(model.index(1, 0, list_name_index), QItemSelectionModel.Select)
        with signal_waiter(self._db_mngr.parameter_value_lists_removed) as waiter:
            view.remove_selected()
            waiter.wait()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(model.rowCount(list_name_index), 0)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 0)

    def test_change_value(self):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        value_index1 = model.index(0, 0, list_name_index)
        with signal_waiter(self._db_mngr.parameter_value_lists_updated) as waiter:
            self._write_to_index(value_index1, "new_value")
            waiter.wait()
        self.assertEqual(model.index(0, 0, list_name_index).data(), "new_value")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 2)
            for i, expected_value in enumerate(("new_value", "value_2")):
                self.assertEqual(db_access.lists[i].name, "value_list_1")
                self.assertEqual(from_database(db_access.lists[i].value), expected_value)

    def test_rename_list(self):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        with signal_waiter(self._db_mngr.parameter_value_lists_updated) as waiter:
            self._write_to_index(list_name_index, "new_list_name")
            waiter.wait()
        self.assertEqual(model.rowCount(root_index), 2)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "new_list_name")
        self.assertEqual(model.rowCount(list_name_index), 3)
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_1")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self.assertEqual(model.index(2, 0, list_name_index).data(), "Enter new list value here...")
        list_name_index = model.index(1, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self._commit_changes_to_database()
        with _access_database(self._db_mngr, self._db_map) as db_access:
            self.assertEqual(len(db_access.lists), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(db_access.lists[i].name, "new_list_name")
                self.assertEqual(from_database(db_access.lists[i].value), expected_value)


@contextmanager
def _access_database(db_mngr, db_map):
    db_map_access = _DBMapAccess(db_mngr.worker_thread)
    with signal_waiter(db_map_access.finished) as waiter:
        db_map_access.fetch_parameter_value_lists.emit(db_map)
        waiter.wait()
    try:
        yield db_map_access
    finally:
        db_map_access.deleteLater()


class _DBMapAccess(QObject):

    fetch_parameter_value_lists = Signal(object)
    finished = Signal()

    def __init__(self, thread):
        super().__init__()
        self.lists = None
        self.moveToThread(thread)
        self.fetch_parameter_value_lists.connect(self._store_parameter_value_lists)

    @Slot(object)
    def _store_parameter_value_lists(self, db_map):
        self.lists = db_map.query(db_map.parameter_value_list_sq).all()
        self.finished.emit()


if __name__ == '__main__':
    unittest.main()
