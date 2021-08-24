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
from types import MethodType
import unittest
from unittest import mock
from PySide2.QtCore import QObject, Qt, Signal, Slot, QItemSelectionModel
from PySide2.QtWidgets import QApplication

from spinedb_api import (
    DiffDatabaseMapping,
    from_database,
    import_object_classes,
    import_objects,
    import_parameter_value_lists,
)
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddObjectClassesDialog, AddObjectsDialog
from spinetoolbox.spine_db_editor.widgets.edit_or_remove_items_dialogs import (
    EditObjectClassesDialog,
    EditObjectsDialog,
    RemoveEntitiesDialog,
)
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

    def _write_to_index(self, view, index, value):
        delegate = view.itemDelegate(index)
        if self._cell_editor is None:
            original_create_editor = delegate.createEditor

            def create_and_store_editor(instance, parent, option, target_index):
                self._cell_editor = original_create_editor(parent, option, target_index)
                return self._cell_editor

            delegate.createEditor = MethodType(create_and_store_editor, delegate)
        view.setCurrentIndex(index)
        view.edit(index)
        self._cell_editor.setText(value)
        delegate.commitData.emit(self._cell_editor)

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_mngr, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            with signal_waiter(self._db_mngr.session_committed) as waiter:
                self._db_editor.ui.actionCommit.trigger()
                waiter.wait()


class TestObjectTreeViewWithInitiallyEmptyDatabase(_Base):
    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def test_empty_view(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 0)
        self.assertEqual(model.columnCount(root_index), 2)
        self.assertEqual(root_index.data(), "root")
        self.assertEqual(model.headerData(0, Qt.Horizontal), "name")
        self.assertEqual(model.headerData(1, Qt.Horizontal), "database")

    def test_add_object_class(self):
        self._add_object_class("an_object_class")
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        class_index = model.index(0, 0, root_index)
        self.assertEqual(model.rowCount(class_index), 0)
        self.assertEqual(class_index.data(), "an_object_class")
        class_database_index = model.index(0, 1, root_index)
        self.assertEqual(class_database_index.data(), "database")
        self._commit_changes_to_database("Add object class.")
        with _access_database(self._db_mngr, self._db_map, "object_class_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "an_object_class")

    def test_add_object(self):
        self._add_object_class("an_object_class")
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        view._context_item = model.item_from_index(class_index)
        self._add_object("an_object")
        self.assertEqual(model.rowCount(class_index), 1)
        self.assertEqual(class_index.data(), "an_object_class")
        object_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(object_index), 0)
        self.assertEqual(object_index.data(), "an_object")
        object_database_index = model.index(0, 1, class_index)
        self.assertEqual(object_database_index.data(), "database")
        self._commit_changes_to_database("Add object.")
        with _access_database(self._db_mngr, self._db_map, "object_class_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "an_object_class")
        with _access_database(self._db_mngr, self._db_map, "object_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "an_object")

    def _add_item(self, item_name, menu_action_text, editor_method_name, dialog, name_column):
        view = self._db_editor.ui.treeView_object
        add_items_action = None
        for action in view._menu.actions():
            if action.text() == menu_action_text:
                add_items_action = action
                break
        self.assertIsNotNone(add_items_action)
        with mock.patch.object(self._db_editor, editor_method_name) as show_dialog_method:
            dialog_ref = _Reference()

            def steal_dialog(*args):
                dialog_ref.value = dialog(self._db_editor, *args, self._db_editor.db_mngr, *self._db_editor.db_maps)

            show_dialog_method.side_effect = lambda *args: steal_dialog(*args)
            add_items_action.trigger()
            self.assertIsNotNone(dialog_ref.value)
            add_items_dialog = dialog_ref.value
            with signal_waiter(add_items_dialog.model.rowsInserted) as waiter:
                QApplication.processEvents()
                waiter.wait()
            item_name_index = add_items_dialog.model.index(0, name_column)
            add_items_dialog.set_model_data(item_name_index, item_name)
            add_items_dialog.accept()

    def _add_object_class(self, class_name):
        self._add_item(class_name, "Add object classes", "show_add_object_classes_form", AddObjectClassesDialog, 0)

    def _add_object(self, object_name):
        self._add_item(object_name, "Add objects", "show_add_objects_form", AddObjectsDialog, 1)


class TestObjectTreeViewWithExistingData(_Base):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_object_classes(db_map, ("object_class_1",))
        import_objects(db_map, (("object_class_1", "object_1"), ("object_class_1", "object_2")))
        db_map.commit_session("Add objects.")
        db_map.connection.close()
        self._common_setup(url, create=False)
        QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        self._temp_dir.cleanup()

    def test_database_contents_shown_correctly(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        view.expand(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(root_index), 2)
        self.assertEqual(root_index.data(), "root")
        self.assertEqual(model.headerData(0, Qt.Horizontal), "name")
        self.assertEqual(model.headerData(1, Qt.Horizontal), "database")
        class_index = model.index(0, 0, root_index)
        view.expand(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(class_index), 2)
        self.assertEqual(class_index.data(), "object_class_1")
        database_index = model.index(0, 1, root_index)
        self.assertEqual(database_index.data(), "database")
        object_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(object_index), 0)
        self.assertEqual(model.columnCount(object_index), 2)
        self.assertEqual(object_index.data(), "object_1")
        database_index = model.index(0, 1, class_index)
        self.assertEqual(database_index.data(), "database")
        object_index = model.index(1, 0, class_index)
        self.assertEqual(model.rowCount(object_index), 0)
        self.assertEqual(model.columnCount(object_index), 2)
        self.assertEqual(object_index.data(), "object_2")
        database_index = model.index(1, 1, class_index)
        self.assertEqual(database_index.data(), "database")

    def test_rename_object_class(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        view.expand(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        view.setCurrentIndex(class_index)
        with signal_waiter(self._db_mngr.object_classes_updated) as waiter:
            self._rename_object_class("renamed_class")
            waiter.wait()
        class_index = model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "renamed_class")
        self._commit_changes_to_database("Rename object class.")
        with _access_database(self._db_mngr, self._db_map, "object_class_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "renamed_class")

    def test_rename_object(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        view.expand(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        view.expand(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        object_index = model.index(0, 0, class_index)
        view.setCurrentIndex(object_index)
        with signal_waiter(self._db_mngr.objects_updated) as waiter:
            self._rename_object("renamed_object")
            waiter.wait()
        object_index = model.index(0, 0, class_index)
        self.assertEqual(object_index.data(), "renamed_object")
        self._commit_changes_to_database("Rename object.")
        with _access_database(self._db_mngr, self._db_map, "object_sq") as db_access:
            self.assertEqual(len(db_access.data), 2)
            self.assertEqual(db_access.data[0].name, "renamed_object")

    def test_remove_object_class(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        view.expand(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        view.selectionModel().setCurrentIndex(class_index, QItemSelectionModel.ClearAndSelect)
        with signal_waiter(self._db_mngr.object_classes_removed) as waiter:
            self._remove_object_class()
            waiter.wait()
        self.assertEqual(model.rowCount(root_index), 0)
        self._commit_changes_to_database("Remove object class.")
        with _access_database(self._db_mngr, self._db_map, "object_class_sq") as db_access:
            self.assertEqual(len(db_access.data), 0)

    def test_remove_object(self):
        view = self._db_editor.ui.treeView_object
        model = view.model()
        root_index = model.index(0, 0)
        view.expand(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        view.expand(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        object_index = model.index(0, 0, class_index)
        view.selectionModel().setCurrentIndex(object_index, QItemSelectionModel.ClearAndSelect)
        with signal_waiter(self._db_mngr.objects_removed) as waiter:
            self._remove_object()
            waiter.wait()
        self.assertEqual(model.rowCount(class_index), 1)
        object_index = model.index(0, 0, class_index)
        self.assertEqual(object_index.data(), "object_2")
        self._commit_changes_to_database("Remove object.")
        with _access_database(self._db_mngr, self._db_map, "object_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "object_2")

    def _rename_object_class(self, class_name):
        self._edit_item(class_name, "Edit...", "show_edit_object_classes_form", EditObjectClassesDialog)

    def _rename_object(self, object_name):
        self._edit_item(object_name, "Edit...", "show_edit_objects_form", EditObjectsDialog)

    def _edit_item(self, item_name, menu_action_text, editor_method_name, dialog):
        view = self._db_editor.ui.treeView_object
        edit_items_action = None
        for action in view._menu.actions():
            if action.text() == menu_action_text:
                edit_items_action = action
                break
        self.assertIsNotNone(edit_items_action)
        with mock.patch.object(self._db_editor, editor_method_name) as show_dialog_method:
            dialog_ref = _Reference()

            def steal_dialog(*args):
                dialog_ref.value = dialog(self._db_editor, self._db_editor.db_mngr, *args)

            show_dialog_method.side_effect = lambda *args: steal_dialog(*args)
            edit_items_action.trigger()
            self.assertIsNotNone(dialog_ref.value)
            edit_items_dialog = dialog_ref.value
            item_name_index = edit_items_dialog.model.index(0, 0)
            edit_items_dialog.set_model_data(item_name_index, item_name)
            edit_items_dialog.accept()

    def _remove_object_class(self):
        self._remove_item("Remove...", "show_remove_entity_tree_items_form", RemoveEntitiesDialog)

    def _remove_object(self):
        self._remove_item("Remove...", "show_remove_entity_tree_items_form", RemoveEntitiesDialog)

    def _remove_item(self, menu_action_text, editor_method_name, dialog):
        view = self._db_editor.ui.treeView_object
        remove_items_action = None
        for action in view._menu.actions():
            if action.text() == menu_action_text:
                remove_items_action = action
                break
        self.assertIsNotNone(remove_items_action)
        with mock.patch.object(self._db_editor, editor_method_name) as show_dialog_method:
            dialog_ref = _Reference()

            def steal_dialog(selected_indexes):
                selected = {
                    item_type: [ind.model().item_from_index(ind) for ind in indexes]
                    for item_type, indexes in selected_indexes.items()
                }
                dialog_ref.value = dialog(self._db_editor, self._db_editor.db_mngr, selected)

            show_dialog_method.side_effect = lambda *args: steal_dialog(*args)
            remove_items_action.trigger()
            self.assertIsNotNone(dialog_ref.value)
            edit_items_dialog = dialog_ref.value
            edit_items_dialog.accept()


class _ParameterValueListTreeViewTestBase(_Base):
    def _append_value_list(self, list_name):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        last_row = model.rowCount(root_index)
        list_name_index = model.index(last_row - 1, 0, root_index)
        self._write_to_index(view, list_name_index, list_name)
        return list_name_index


class TestParameterValueListTreeViewWithInitiallyEmptyDatabase(_ParameterValueListTreeViewTestBase):
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
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        value_index1 = model.index(0, 0, list_name_index)
        self._write_to_index(view, value_index1, "value_1")
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_1")
        self.assertEqual(model.rowCount(list_name_index), 2)
        value_index2 = model.index(1, 0, list_name_index)
        self._write_to_index(view, value_index2, "value_2")
        while model.rowCount(list_name_index) != 3:
            QApplication.processEvents()
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database("Add parameter value list.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(db_access.data[i].name, "a_value_list")
                self.assertEqual(from_database(db_access.data[i].value), expected_value)


class TestParameterValueListTreeViewWithExistingData(_ParameterValueListTreeViewTestBase):
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
        self._commit_changes_to_database("Remove parameter value list value.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 1)
            self.assertEqual(db_access.data[0].name, "value_list_1")
            self.assertEqual(from_database(db_access.data[0].value), "value_2")

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
        self._commit_changes_to_database("Remove parameter value list.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 0)

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
        self._commit_changes_to_database("Remove parameter value list.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 0)

    def test_change_value(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        value_index1 = model.index(0, 0, list_name_index)
        with signal_waiter(self._db_mngr.parameter_value_lists_updated) as waiter:
            self._write_to_index(view, value_index1, "new_value")
            waiter.wait()
        self.assertEqual(model.index(0, 0, list_name_index).data(), "new_value")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database("Update parameter value list value.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 2)
            for i, expected_value in enumerate(("new_value", "value_2")):
                self.assertEqual(db_access.data[i].name, "value_list_1")
                self.assertEqual(from_database(db_access.data[i].value), expected_value)

    def test_rename_list(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        with signal_waiter(self._db_mngr.parameter_value_lists_updated) as waiter:
            self._write_to_index(view, list_name_index, "new_list_name")
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
        self._commit_changes_to_database("Rename parameter value list.")
        with _access_database(self._db_mngr, self._db_map, "parameter_value_list_sq") as db_access:
            self.assertEqual(len(db_access.data), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(db_access.data[i].name, "new_list_name")
                self.assertEqual(from_database(db_access.data[i].value), expected_value)


class _Reference:
    def __init__(self):
        self.value = None


@contextmanager
def _access_database(db_mngr, db_map, subquery_name):
    db_map_access = _DBMapAccess(subquery_name, db_mngr.worker_thread)
    with signal_waiter(db_map_access.finished) as waiter:
        db_map_access.fetch_data.emit(db_map)
        waiter.wait()
    try:
        yield db_map_access
    finally:
        db_map_access.deleteLater()


class _DBMapAccess(QObject):

    fetch_data = Signal(object)
    finished = Signal()

    def __init__(self, subquery_name, thread):
        super().__init__()
        self.data = None
        self._subquery_name = subquery_name
        self.moveToThread(thread)
        self.fetch_data.connect(self._do_subquery)

    @Slot(object)
    def _do_subquery(self, db_map):
        self.data = db_map.query(getattr(db_map, self._subquery_name)).all()
        self.finished.emit()


if __name__ == '__main__':
    unittest.main()
