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

"""Unit tests for DB editor's custom ``QTreeView`` classes."""
import gc
import os.path
from tempfile import TemporaryDirectory
from unittest import mock
from PySide6.QtCore import QItemSelection, QItemSelectionModel, Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    DatabaseMapping,
    from_database,
    import_entities,
    import_entity_classes,
    import_parameter_value_lists,
)
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddEntitiesDialog, AddEntityClassesDialog
from spinetoolbox.spine_db_editor.widgets.edit_or_remove_items_dialogs import (
    EditEntitiesDialog,
    EditEntityClassesDialog,
    RemoveEntitiesDialog,
)
from tests.spine_db_editor.helpers import TestBase
from tests.spine_db_editor.widgets.helpers import (
    EditorDelegateMocking,
    add_entity,
    add_entity_tree_item,
    add_zero_dimension_entity_class,
)


class _ParameterValueListEdits:
    def __init__(self, view):
        self._view = view
        self.view_editor = EditorDelegateMocking()

    def append_value_list(self, db_mngr, list_name):
        model = self._view.model()
        root_index = model.index(0, 0)
        empty_name_row = model.rowCount(root_index) - 1
        empty_name_index = model.index(empty_name_row, 0, root_index)
        self.view_editor.write_to_index(self._view, empty_name_index, list_name)
        new_name_row = model.rowCount(root_index) - 2
        return model.index(new_name_row, 0, root_index)

    def append_value(self, db_mngr, list_name, value):
        model = self._view.model()
        root_index = model.index(0, 0)
        for list_row in range(model.rowCount(root_index)):
            list_index = model.index(list_row, 0, root_index)
            if list_index.data() == list_name:
                last_row = model.rowCount(list_index) - 1
                empty_value_index = model.index(last_row, 0, list_index)
                self.view_editor.write_to_index(self._view, empty_value_index, value)
                return model.index(last_row, 0, list_index)
        raise RuntimeError(f"{list_name} not found.")


def _edit_entity_tree_item(new_entries, view, menu_action_text, dialog_class):
    edit_items_action = None
    for action in view._menu.actions():
        if action.text() == menu_action_text:
            edit_items_action = action
            break
    if edit_items_action is None:
        raise RuntimeError("Menu action not found.")
    patched = "spinetoolbox.spine_db_editor.widgets.tree_view_mixin." + dialog_class.__name__
    with mock.patch(patched) as mock_dialog:
        edit_items_action.trigger()
        arguments_list = mock_dialog.call_args_list
    for arguments in arguments_list:
        edit_items_dialog = dialog_class(*arguments[0])
        for column, entry in new_entries.items():
            item_name_index = edit_items_dialog.model.index(0, column)
            edit_items_dialog.set_model_data(item_name_index, entry)
            edit_items_dialog.accept()


def _remove_entity_tree_item(view, menu_action_text, dialog_class):
    remove_items_action = None
    for action in view._menu.actions():
        if action.text() == menu_action_text:
            remove_items_action = action
            break
    if remove_items_action is None:
        raise RuntimeError("Menu action not found.")
    patched = "spinetoolbox.spine_db_editor.widgets.tree_view_mixin." + dialog_class.__name__
    with mock.patch(patched) as mock_dialog:
        remove_items_action.trigger()
        arguments_list = mock_dialog.call_args_list
    for arguments in arguments_list:
        edit_items_dialog = dialog_class(*arguments[0])
        edit_items_dialog.accept()


def _remove_entity_class(view):
    _remove_entity_tree_item(view, "Remove...", RemoveEntitiesDialog)


def _remove_entity(view):
    _remove_entity_tree_item(view, "Remove...", RemoveEntitiesDialog)


def _append_table_row(view, row):
    model = view.model()
    last_row = model.rowCount() - 1
    for column, value in enumerate(row):
        delegate_mock = EditorDelegateMocking()
        index = model.index(last_row, column)
        delegate_mock.write_to_index(view, index, value)


class TestEntityTreeViewWithInitiallyEmptyDatabase(TestBase):
    def test_empty_view(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 0)
        self.assertEqual(model.columnCount(root_index), 2)
        self.assertEqual(root_index.data(), "root")
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "name")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "database")

    def test_add_class_with_zero_dimensions(self):
        view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(view, "an_entity_class")
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        class_index = model.index(0, 0, root_index)
        self.assertEqual(model.rowCount(class_index), 0)
        self.assertEqual(class_index.data(), "an_entity_class")
        class_database_index = model.index(0, 1, root_index)
        self.assertEqual(class_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity class.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].name, "an_entity_class")

    def test_add_class_with_single_dimension(self):
        add_zero_dimension_entity_class(self._db_editor.ui.treeView_entity, "an_entity_class")
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        view._context_item = model.item_from_index(class_index)
        self._add_multidimensional_class("a_relationship_class", ["an_entity_class"])
        class_index = model.index(1, 0, root_index)
        self.assertEqual(model.rowCount(class_index), 0)
        self.assertEqual(class_index.data(), "a_relationship_class")
        class_database_index = model.index(0, 1, root_index)
        self.assertEqual(class_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity classes.")
        with self._db_map:
            entity_class = (
                self._db_map.query(self._db_map.wide_entity_class_sq)
                .filter(self._db_map.wide_entity_class_sq.c.name == "a_relationship_class")
                .one()
            )
        self.assertEqual(entity_class.name, "a_relationship_class")
        self.assertEqual(entity_class.dimension_name_list, "an_entity_class")

    def test_add_entity(self):
        view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(view, "an_entity_class")
        add_entity(view, "an_entity")
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(class_index), 1)
        self.assertEqual(class_index.data(), "an_entity_class")
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(entity_index.data(), "an_entity")
        entity_database_index = model.index(0, 1, class_index)
        self.assertEqual(entity_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "an_entity_class")
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "an_entity")

    def test_add_entity_with_alternative(self):
        """Tests that adding a new entity with the alternative column filled
        will actually add the alternative"""
        view = self._db_editor.ui.treeView_entity
        self._db_mngr.add_items("alternative", {self._db_map: [{"name": "Alt1"}]})
        add_zero_dimension_entity_class(view, "an_entity_class")
        entity_class_id = self._db_map.entity_class(name="an_entity_class")["id"]
        add_entity(view, "an_entity", alternative="Alt1")
        entity = self._db_map.entity(class_id=entity_class_id, name="an_entity")
        entity_alternative = self._db_map.entity_alternative(
            alternative_name="Alt1", entity_class_id=entity_class_id, entity_id=entity["id"]
        )
        self.assertTrue(entity_alternative["active"])
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(class_index), 1)
        self.assertEqual(class_index.data(), "an_entity_class")
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(entity_index.data(), "an_entity")
        entity_database_index = model.index(0, 1, class_index)
        self.assertEqual(entity_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "an_entity_class")
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "an_entity")

    def test_add_entity_with_group(self):
        """Tests that adding a new entity with the group -column filled
        will actually create the entity group and add the entity to it."""
        view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(view, "classy")
        with mock.patch.object(self._db_mngr, "import_data") as mock_add_entity_groups:
            add_entity(view, "wine", group="beverages")
            mock_add_entity_groups.assert_called_once_with(
                {
                    self._db_map: {
                        "entities": {("classy", "beverages")},
                        "entity_groups": {("classy", "beverages", "wine")},
                    }
                },
                command_text="Add entity group",
            )
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(class_index), 1)
        self.assertEqual(class_index.data(), "classy")
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(entity_index.data(), "wine")
        entity_database_index = model.index(0, 1, class_index)
        self.assertEqual(entity_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "classy")
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "wine")

    def test_add_entity_with_single_dimension(self):
        view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(view, "an_entity_class")
        add_entity(view, "an_entity")
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        view._context_item = model.item_from_index(class_index)
        self._add_multidimensional_class("a_relationship_class", ["an_entity_class"])
        self.assertEqual(model.rowCount(root_index), 2)
        class_index = model.index(1, 0, root_index)  # N-D classes come after 0-D classes
        self.assertEqual(class_index.data(), "a_relationship_class")
        view._context_item = model.item_from_index(class_index)
        self._add_multidimensional_entity("a_relationship", ["an_entity"])
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(class_index), 1)
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(entity_index.data(), "an_entity")
        database_index = model.index(0, 1, class_index)
        self.assertEqual(database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add an entities.")
        with self._db_map:
            class_id = (
                self._db_map.query(self._db_map.entity_class_sq)
                .filter(self._db_map.entity_class_sq.c.name == "a_relationship_class")
                .one()
                .id
            )
            entity = (
                self._db_map.query(self._db_map.wide_entity_sq)
                .filter(self._db_map.wide_entity_sq.c.class_id == class_id)
                .one()
            )
        self.assertEqual(entity.name, "a_relationship")
        self.assertEqual(entity.element_name_list, "an_entity")

    def test_add_entity_class_with_another_class_as_preselected_first_dimension(self):
        entity_tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(entity_tree_view, "an_entity_class")
        entity_model = entity_tree_view.model()
        root_index = entity_model.index(0, 0)
        entity_class_index = entity_model.index(0, 0, root_index)
        entity_tree_view._context_item = entity_model.item_from_index(entity_class_index)
        add_entity_tree_item(
            {1: "my_first_dimension_is_an_entity_class"},
            entity_tree_view,
            "Add entity classes...",
            AddEntityClassesDialog,
        )
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(1, 0, root_index)
        self.assertEqual(model.rowCount(class_index), 0)
        self.assertEqual(class_index.data(), "my_first_dimension_is_an_entity_class")
        class_database_index = model.index(0, 1, root_index)
        self.assertEqual(class_database_index.data(), self.db_codename)
        self._commit_changes_to_database("Add entity classes.")
        with self._db_map:
            data = self._db_map.query(self._db_map.wide_entity_class_sq).all()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0].name, "an_entity_class")
        self.assertIsNone(data[0].dimension_name_list)
        self.assertEqual(data[1].name, "my_first_dimension_is_an_entity_class")
        self.assertEqual(data[1].dimension_name_list, "an_entity_class")

    def _add_multidimensional_class(self, class_name, dimension_names):
        item_names = dict(enumerate(dimension_names))
        item_names[len(dimension_names)] = class_name
        add_entity_tree_item(
            item_names,
            self._db_editor.ui.treeView_entity,
            "Add entity classes...",
            AddEntityClassesDialog,
        )

    def _add_multidimensional_entity(self, element_name, entity_names):
        item_names = dict(enumerate(entity_names))
        item_names[len(entity_names)] = element_name
        add_entity_tree_item(item_names, self._db_editor.ui.treeView_entity, "Add entities...", AddEntitiesDialog)


class TestEntityTreeViewWithExistingZeroDimensionalEntities(TestBase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            import_entity_classes(db_map, (("entity_class_1",),))
            import_entities(db_map, (("entity_class_1", "entity_1"), ("entity_class_1", "entity_2")))
            db_map.commit_session("Add entities.")
        db_map.close()
        self._common_setup(url, create=False)
        model = self._db_editor.ui.treeView_entity.model()
        root_index = model.index(0, 0)
        while model.rowCount(root_index) != 1:
            # Wait for fetching to finish.
            QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        gc.collect()
        self._temp_dir.cleanup()

    def test_database_contents_shown_correctly(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(root_index), 2)
        self.assertEqual(root_index.data(), "root")
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "name")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "database")
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(class_index), 2)
        self.assertEqual(class_index.data(), "entity_class_1")
        database_index = model.index(0, 1, root_index)
        self.assertEqual(database_index.data(), self.db_codename)
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(model.columnCount(entity_index), 2)
        self.assertEqual(entity_index.data(), "entity_1")
        database_index = model.index(0, 1, class_index)
        self.assertEqual(database_index.data(), self.db_codename)
        entity_index = model.index(1, 0, class_index)
        self.assertEqual(model.rowCount(entity_index), 0)
        self.assertEqual(model.columnCount(entity_index), 2)
        self.assertEqual(entity_index.data(), "entity_2")
        database_index = model.index(1, 1, class_index)
        self.assertEqual(database_index.data(), self.db_codename)

    def test_rename_entity_class(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        view.setCurrentIndex(class_index)
        self._rename_entity_class("renamed_class")
        class_index = model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "renamed_class")
        self._commit_changes_to_database("Rename entity class.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "renamed_class")

    def test_rename_entity(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.setCurrentIndex(entity_index)
        self._rename_entity("renamed_entity")
        QApplication.processEvents()  # Fixes a "silent" Traceback
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(entity_index.data(), "renamed_entity")
        self._commit_changes_to_database("Rename entity.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0].name, "renamed_entity")

    def test_remove_entity_class(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        class_index = model.index(0, 0, root_index)
        view.selectionModel().setCurrentIndex(class_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        _remove_entity_class(view)
        self.assertEqual(model.rowCount(root_index), 0)
        self._commit_changes_to_database("Remove entity class.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_class_sq).all()
            self.assertEqual(len(data), 0)

    def test_remove_entity(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.selectionModel().setCurrentIndex(entity_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        _remove_entity(view)
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(class_index), 1)
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(entity_index.data(), "entity_2")
        self._commit_changes_to_database("Remove entity.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "entity_2")

    def test_set_db_column_visibility(self):
        view = self._db_editor.ui.treeView_entity
        self.assertTrue(view._header.isSectionHidden(1))
        view.set_db_column_visibility(True)
        self.assertFalse(view._header.isSectionHidden(1))

    def test_reload_database_while_entity_is_selected_does_not_produce_traceback(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 1:
            QApplication.processEvents()
        class_index = model.index(0, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.selectionModel().setCurrentIndex(entity_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with DatabaseMapping(self._db_map.db_url) as db_map:
            db_map.add_entity_item(name="entity_3", entity_class_name="entity_class_1")
            db_map.commit_session("Add external data.")
        db_map.close()
        with mock.patch.object(self._db_editor, "_set_stacked_model_default_data") as expected_callable:
            with signal_waiter(view.selectionModel().selectionChanged, timeout=1.0) as waiter:
                self._db_mngr.refresh_session(self._db_map)
                waiter.wait()
            self.assertEqual(expected_callable.call_count, 2 * len(self._db_editor._all_empty_models))

    def _rename_entity_class(self, class_name):
        view = self._db_editor.ui.treeView_entity
        _edit_entity_tree_item({0: class_name}, view, "Edit...", EditEntityClassesDialog)

    def _rename_entity(self, entity_name):
        view = self._db_editor.ui.treeView_entity
        _edit_entity_tree_item({0: entity_name}, view, "Edit...", EditEntitiesDialog)


class TestEntityTreeViewWithExistingMultidimensionalEntities(TestBase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            import_entity_classes(db_map, (("object_class_1",), ("object_class_2",)))
            import_entities(
                db_map,
                (
                    ("object_class_1", "object_11"),
                    ("object_class_1", "object_12"),
                    ("object_class_2", "object_21"),
                    ("object_class_2", "object_22"),
                ),
            )
            import_entity_classes(db_map, (("relationship_class", ("object_class_1", "object_class_2")),))
            import_entities(
                db_map,
                (
                    ("relationship_class", ("object_11", "object_21")),
                    ("relationship_class", ("object_11", "object_22")),
                ),
            )
            db_map.commit_session("Add relationships.")
        db_map.close()
        self._common_setup(url, create=False)
        model = self._db_editor.ui.treeView_entity.model()
        root_index = model.index(0, 0)
        while model.rowCount(root_index) != 3:
            # Wait for fetching to finish.
            QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        gc.collect()
        self._temp_dir.cleanup()

    def test_database_contents_shown_correctly(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(root_index), 2)
        self.assertEqual(root_index.data(), "root")
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "name")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "database")
        class_index = model.index(2, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        self.assertEqual(model.columnCount(class_index), 2)
        self.assertEqual(class_index.data(), "relationship_class")
        database_index = model.index(0, 1, root_index)
        self.assertEqual(database_index.data(), self.db_codename)
        entity_ndex = model.index(0, 0, class_index)
        self.assertEqual(model.rowCount(entity_ndex), 0)
        self.assertEqual(model.columnCount(entity_ndex), 2)
        self.assertEqual(entity_ndex.data(), "object_11 ǀ object_21")
        database_index = model.index(0, 1, class_index)
        self.assertEqual(database_index.data(), self.db_codename)
        entity_ndex = model.index(1, 0, class_index)
        self.assertEqual(model.rowCount(entity_ndex), 0)
        self.assertEqual(model.columnCount(entity_ndex), 2)
        self.assertEqual(entity_ndex.data(), "object_11 ǀ object_22")
        database_index = model.index(1, 1, class_index)
        self.assertEqual(database_index.data(), self.db_codename)

    def test_rename_multidimensional_entity_class(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        view.setCurrentIndex(class_index)
        self._rename_class("renamed_class")
        class_index = model.index(2, 0, root_index)
        self.assertEqual(class_index.data(), "renamed_class")
        self._commit_changes_to_database("Rename relationship class.")
        with self._db_map:
            entity_class = (
                self._db_map.query(self._db_map.entity_class_sq)
                .filter(self._db_map.entity_class_sq.c.name == "renamed_class")
                .one()
            )
            self.assertIsNotNone(entity_class)
            self.assertEqual(entity_class.name, "renamed_class")

    def test_rename_multidimensional_entity(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.setCurrentIndex(entity_index)
        self._rename_entity("renamed_relationship")
        QApplication.processEvents()  # Fixes a "silent" Traceback.
        self._commit_changes_to_database("Rename relationship.")
        with self._db_map:
            class_id = (
                self._db_map.query(self._db_map.entity_class_sq)
                .filter(self._db_map.entity_class_sq.c.name == "relationship_class")
                .one()
                .id
            )
            data = (
                self._db_map.query(self._db_map.wide_entity_sq)
                .filter(self._db_map.wide_entity_sq.c.class_id == class_id)
                .all()
            )
            self.assertEqual(len(data), 2)
            names = {i.name for i in data}
            self.assertEqual(names, {"renamed_relationship", "object_11__object_22"})

    def test_modify_entitys_elements(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        self.assertEqual(model.item_from_index(class_index).display_data, "relationship_class")
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.setCurrentIndex(entity_index)
        _edit_entity_tree_item({0: "object_12"}, view, "Edit...", EditEntitiesDialog)
        QApplication.processEvents()  # Fixes "silent" Traceback.
        self.assertEqual(entity_index.data(), "object_12 ǀ object_21")
        self._commit_changes_to_database("Change relationship's objects.")
        with self._db_map:
            class_id = (
                self._db_map.query(self._db_map.entity_class_sq)
                .filter(self._db_map.entity_class_sq.c.name == "relationship_class")
                .one()
                .id
            )
            data = self._db_map.query(self._db_map.wide_entity_sq).all()
            self.assertEqual(len(data), 6)
            objects = {i.element_name_list for i in data if i.class_id == class_id}
            self.assertEqual(objects, {"object_12,object_21", "object_11,object_22"})

    def test_remove_multidimensional_entity_class(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        self.assertEqual(model.item_from_index(class_index).display_data, "relationship_class")
        view.selectionModel().setCurrentIndex(class_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._remove_class()
        self.assertEqual(model.rowCount(root_index), 2)
        self._commit_changes_to_database("Remove relationship class.")
        with self._db_map:
            data = self._db_map.query(self._db_map.wide_entity_class_sq).all()
            self.assertEqual(len(data), 2)
            self.assertEqual({i.name for i in data}, {"object_class_1", "object_class_2"})

    def test_remove_multidimensional_entity(self):
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        self.assertEqual(model.item_from_index(class_index).display_data, "relationship_class")
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 2:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        view.selectionModel().setCurrentIndex(entity_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._remove_entity()
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        self._commit_changes_to_database("Remove relationship.")
        with self._db_map:
            class_id = (
                self._db_map.query(self._db_map.entity_class_sq)
                .filter(self._db_map.entity_class_sq.c.name == "relationship_class")
                .one()
                .id
            )
            record = (
                self._db_map.query(self._db_map.wide_entity_sq)
                .filter(self._db_map.wide_entity_sq.c.class_id == class_id)
                .one()
            )
            self.assertEqual(record.name, "object_11__object_22")

    def test_removing_dimension_class_removes_corresponding_multidimensional_entity_class(self):
        object_tree_view = self._db_editor.ui.treeView_entity
        object_model = object_tree_view.model()
        root_index = object_model.index(0, 0)
        object_model.fetchMore(root_index)
        while object_model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = object_model.index(0, 0, root_index)
        object_tree_view.selectionModel().setCurrentIndex(class_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        _remove_entity_class(object_tree_view)
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        QApplication.processEvents()
        self.assertEqual(model.rowCount(root_index), 1)
        self._commit_changes_to_database("Remove object class.")
        with self._db_map:
            data = self._db_map.query(self._db_map.wide_entity_class_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual({i.name for i in data}, {"object_class_2"})

    def test_removing_element_removes_corresponding_entity(self):
        object_tree_view = self._db_editor.ui.treeView_entity
        object_model = object_tree_view.model()
        root_index = object_model.index(0, 0)
        object_model.fetchMore(root_index)
        while object_model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = object_model.index(1, 0, root_index)
        self.assertEqual(class_index.data(), "object_class_2")
        object_model.fetchMore(class_index)
        while object_model.rowCount(class_index) != 2:
            QApplication.processEvents()
        object_index = object_model.index(0, 0, class_index)
        self.assertEqual(object_index.data(), "object_21")
        object_tree_view.selectionModel().setCurrentIndex(
            object_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        _remove_entity(object_tree_view)
        view = self._db_editor.ui.treeView_entity
        model = view.model()
        root_index = model.index(0, 0)
        model.fetchMore(root_index)
        while model.rowCount(root_index) != 3:
            QApplication.processEvents()
        class_index = model.index(2, 0, root_index)
        model.fetchMore(class_index)
        while model.rowCount(class_index) != 1:
            QApplication.processEvents()
        entity_index = model.index(0, 0, class_index)
        self.assertEqual(entity_index.data(), "object_11 ǀ object_22")
        self._commit_changes_to_database("Remove object.")
        with self._db_map:
            data = self._db_map.query(self._db_map.entity_sq).all()
            self.assertEqual(len(data), 4)
            self.assertEqual({i.name for i in data}, {"object_11", "object_12", "object_22", "object_11__object_22"})

    def _rename_class(self, class_name):
        view = self._db_editor.ui.treeView_entity
        _edit_entity_tree_item({0: class_name}, view, "Edit...", EditEntityClassesDialog)

    def _rename_entity(self, name):
        view = self._db_editor.ui.treeView_entity
        _edit_entity_tree_item({2: name}, view, "Edit...", EditEntitiesDialog)

    def _remove_class(self):
        view = self._db_editor.ui.treeView_entity
        _remove_entity_tree_item(view, "Remove...", RemoveEntitiesDialog)

    def _remove_entity(self):
        view = self._db_editor.ui.treeView_entity
        _remove_entity_tree_item(view, "Remove...", RemoveEntitiesDialog)


class TestEntityTreeViewSorting(TestBase):
    """Tests that the entity tree is sorted correctly"""

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            import_entity_classes(db_map, (("entity_class",), ("P_entity_class",), ("P_entity_class (1)",)))
            import_entities(
                db_map,
                (
                    ("entity_class", "entity_11"),
                    ("entity_class", "entity_12"),
                    ("P_entity_class", "entity_1"),
                    ("P_entity_class", "entity_2"),
                    ("P_entity_class (1)", "entity_1 (1)"),
                    ("P_entity_class (1)", "entity_2 (1)"),
                ),
            )
            import_entity_classes(db_map, (("entity_class_ND", ("entity_class", "P_entity_class")),))
            import_entities(
                db_map,
                (("entity_class_ND", ("entity_11", "entity_2")), ("entity_class_ND", ("entity_12", "entity_1"))),
            )
            db_map.commit_session("Add entities.")
        self._common_setup(url, create=False)
        model = self._db_editor.ui.treeView_entity.model()
        self.root_item = model.root_item
        for item in model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        gc.collect()
        self._temp_dir.cleanup()

    def test_tree_item_sorting(self):
        result = [tuple((i.name, [x.name for x in i.children])) for i in self.root_item.children]
        expected = [
            ("entity_class", ["entity_11", "entity_12"]),
            ("P_entity_class", ["entity_1", "entity_2"]),
            ("P_entity_class (1)", ["entity_1 (1)", "entity_2 (1)"]),
            ("entity_class_ND", ["entity_11__entity_2", "entity_12__entity_1"]),
        ]
        self.assertEqual(expected, result)


class TestParameterValueListTreeViewWithInitiallyEmptyDatabase(TestBase):
    def setUp(self):
        self._common_setup("sqlite://", create=True)
        self._edits = _ParameterValueListEdits(self._db_editor.ui.treeView_parameter_value_list)

    def test_empty_tree_has_correct_contents(self):
        model = self._db_editor.ui.treeView_parameter_value_list.model()
        root_index = model.index(0, 0)
        self.assertTrue(root_index.isValid())
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self.assertEqual(model.rowCount(list_name_index), 0)

    def test_add_parameter_value_list(self):
        list_name_index = self._edits.append_value_list(self._db_mngr, "a_value_list")
        self.assertEqual(list_name_index.data(), "a_value_list")
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        self.assertEqual(model.rowCount(list_name_index), 1)
        new_value_index = model.index(0, 0, list_name_index)
        self.assertEqual(new_value_index.data(), "Enter new list value here...")
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 2)
        new_name_index = model.index(1, 0, root_index)
        self.assertEqual(new_name_index.data(), "Type new list name here...")
        self.assertEqual(model.rowCount(new_name_index), 0)

    def test_add_list_then_remove_it(self):
        list_name_index = self._edits.append_value_list(self._db_mngr, "a_value_list")
        self.assertEqual(list_name_index.data(), "a_value_list")
        view = self._db_editor.ui.treeView_parameter_value_list
        view.selectionModel().select(list_name_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.remove_selected()
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(list_name_index.data(), "Type new list name here...")

    def test_add_two_parameter_value_list_values(self):
        list_name_index = self._edits.append_value_list(self._db_mngr, "a_value_list")
        view = self._db_editor.ui.treeView_parameter_value_list
        view.expandAll()
        model = view.model()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 2)
        value_index1 = model.index(0, 0, list_name_index)
        self._edits.view_editor.write_to_index(view, value_index1, "value_1")
        self.assertEqual(model.index(0, 0, list_name_index).data(), "value_1")
        self.assertEqual(model.rowCount(list_name_index), 2)
        value_index2 = model.index(1, 0, list_name_index)
        self._edits.view_editor.write_to_index(view, value_index2, "value_2")
        while model.rowCount(list_name_index) != 3:
            QApplication.processEvents()
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database("Add parameter value list.")
        with self._db_map:
            data = self._db_map.query(self._db_map.parameter_value_list_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "a_value_list")
            data = self._db_map.query(self._db_map.list_value_sq).all()
            self.assertEqual(len(data), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(from_database(data[i].value, data[i].type), expected_value)


class TestParameterValueListTreeViewWithExistingData(TestBase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            import_parameter_value_lists(db_map, (("value_list_1", "value_1"), ("value_list_1", "value_2")))
            db_map.commit_session("Add parameter value list.")
        self._common_setup(url, create=False)

        view = self._db_editor.ui.treeView_parameter_value_list
        self._edits = _ParameterValueListEdits(view)
        model = view.model()
        root_index = model.index(0, 0)
        while model.rowCount(root_index) != 2:
            # Wait for fetching to finish.
            QApplication.processEvents()
        list_name_index = model.index(0, 0, root_index)
        model.fetchMore(list_name_index)
        while model.rowCount(list_name_index) != 3:
            QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        gc.collect()
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
        view.selectionModel().setCurrentIndex(value_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.remove_selected()
        QApplication.processEvents()
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
        with self._db_map:
            data = self._db_map.query(self._db_map.parameter_value_list_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "value_list_1")
            data = self._db_map.query(self._db_map.list_value_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(from_database(data[0].value, data[0].type), "value_2")

    def test_remove_list(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        view.selectionModel().setCurrentIndex(list_name_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.remove_selected()
        root_index = model.index(0, 0)
        self.assertEqual(model.rowCount(root_index), 1)
        list_name_index = model.index(0, 0, root_index)
        self.assertEqual(model.rowCount(list_name_index), 0)
        self.assertEqual(list_name_index.data(), "Type new list name here...")
        self._commit_changes_to_database("Remove parameter value list.")
        with self._db_map:
            data = self._db_map.query(self._db_map.parameter_value_list_sq).all()
            self.assertEqual(len(data), 0)

    def test_change_value(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        value_index1 = model.index(0, 0, list_name_index)
        self._edits.view_editor.write_to_index(view, value_index1, "new_value")
        self.assertEqual(model.index(0, 0, list_name_index).data(), "new_value")
        self.assertEqual(model.index(1, 0, list_name_index).data(), "value_2")
        self._commit_changes_to_database("Update parameter value list value.")
        with self._db_map:
            data = self._db_map.query(self._db_map.parameter_value_list_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "value_list_1")
            data = self._db_map.query(self._db_map.list_value_sq).all()
            self.assertEqual(len(data), 2)
            for i, expected_value in enumerate(("new_value", "value_2")):
                self.assertEqual(from_database(data[i].value, data[i].type), expected_value)

    def test_rename_list(self):
        view = self._db_editor.ui.treeView_parameter_value_list
        model = view.model()
        root_index = model.index(0, 0)
        list_name_index = model.index(0, 0, root_index)
        self._edits.view_editor.write_to_index(view, list_name_index, "new_list_name")
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
        with self._db_map:
            data = self._db_map.query(self._db_map.parameter_value_list_sq).all()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].name, "new_list_name")
            data = self._db_map.query(self._db_map.list_value_sq).all()
            self.assertEqual(len(data), 2)
            for i, expected_value in enumerate(("value_1", "value_2")):
                self.assertEqual(from_database(data[i].value, data[i].type), expected_value)


class TestAlternativeTreeView:
    def test_scenario_generation_action_availability(self, db_editor):
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        view.selectionModel().select(database_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.update_actions_availability(model.item_from_index(database_index))
        assert not view._generate_scenarios_action.isEnabled()
        empty_row_index = model.index(1, 0, database_index)
        assert empty_row_index.data() == "Type new alternative name here..."
        empty_description_index = model.index(1, 1, database_index)
        assert empty_description_index.data() == ""
        view.selectionModel().select(empty_row_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.selectionModel().select(empty_description_index, QItemSelectionModel.SelectionFlag.Select)
        view.update_actions_availability(model.item_from_index(empty_row_index))
        assert not view._generate_scenarios_action.isEnabled()
        view.update_actions_availability(model.item_from_index(empty_description_index))
        assert not view._generate_scenarios_action.isEnabled()
        alternative_row_index = model.index(0, 0, database_index)
        assert alternative_row_index.data() == "Base"
        description_index = model.index(0, 1, database_index)
        assert description_index.data() == "Base alternative"
        view.selectionModel().select(alternative_row_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        view.selectionModel().select(description_index, QItemSelectionModel.SelectionFlag.Select)
        view.update_actions_availability(model.item_from_index(alternative_row_index))
        assert view._generate_scenarios_action.isEnabled()
        view.update_actions_availability(model.item_from_index(description_index))
        assert view._generate_scenarios_action.isEnabled()

    def test_open_scenario_generator(self, db_editor):
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        db_map = database_index.data(DB_MAP_ROLE)
        alternative_row_index = model.index(0, 0, database_index)
        assert alternative_row_index.data() == "Base"
        alternatives = [db_map.alternative(name="Base")]
        view.setCurrentIndex(alternative_row_index)
        view.selectionModel().select(model.index(0, 1, database_index), QItemSelectionModel.SelectionFlag.Select)
        self._assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map)
        view.selectionModel().select(model.index(1, 0, database_index), QItemSelectionModel.SelectionFlag.Select)
        view.selectionModel().select(model.index(1, 1, database_index), QItemSelectionModel.SelectionFlag.Select)
        self._assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map)
        view.selectionModel().select(database_index, QItemSelectionModel.SelectionFlag.Select)
        self._assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map)

    def test_opening_scenario_generator_ignores_alternatives_from_other_databases(self, db_editor, logger, tmp_path):
        fake_db_listener = mock.MagicMock()
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger)
        db_mngr.register_listener(fake_db_listener, db_map)
        db_path = tmp_path / "db.sqlite"
        url = "sqlite:///" + str(db_path)
        with DatabaseMapping(url, create=True) as db_map:
            db_map.add_alternative(name="Other")
            db_map.commit_session("Add alternative to foreign database.")
        with (
            mock.patch(
                "spinetoolbox.spine_db_editor.widgets.spine_db_editor.get_open_file_name_in_last_dir"
            ) as mocK_file_name_giver,
            mock.patch.object(db_editor, "restore_ui"),
        ):
            mocK_file_name_giver.return_value = (str(db_path), "")
            db_editor.add_db_file()
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        assert model.rowCount() == 2
        database1_index = model.index(0, 0)
        assert database1_index.data() == "TestAlternativeTreeView_db"
        assert model.rowCount(database1_index) == 2
        view.selectionModel().select(database1_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        top_left = model.index(0, 0, database1_index)
        bottom_right = model.index(1, 1, database1_index)
        view.selectionModel().select(QItemSelection(top_left, bottom_right), QItemSelectionModel.SelectionFlag.Select)
        database2_index = model.index(1, 0)
        assert database2_index.data() == db_path.stem
        while model.rowCount(database2_index) != 3:
            QApplication.processEvents()
        view.selectionModel().select(database2_index, QItemSelectionModel.SelectionFlag.Select)
        top_left = model.index(0, 0, database2_index)
        bottom_right = model.index(2, 1, database2_index)
        view.selectionModel().select(QItemSelection(top_left, bottom_right), QItemSelectionModel.SelectionFlag.Select)
        view.selectionModel().setCurrentIndex(
            model.index(0, 0, database1_index), QItemSelectionModel.SelectionFlag.Current
        )
        db_map1 = database1_index.data(DB_MAP_ROLE)
        alternatives = [db_map1.alternative(name="Base")]
        self._assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map1)
        view.selectionModel().setCurrentIndex(
            model.index(0, 0, database2_index), QItemSelectionModel.SelectionFlag.Current
        )
        db_map2 = database2_index.data(DB_MAP_ROLE)
        alternatives = [db_map2.alternative(name="Base"), db_map2.alternative(name="Other")]
        self._assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map2)

    @staticmethod
    def _assert_scenario_generator_initialized_with(alternatives, db_editor, view, db_map):
        with mock.patch("spinetoolbox.spine_db_editor.widgets.custom_qtreeview.ScenarioGenerator") as mock_init:
            mock_scenario_generator = mock.MagicMock()
            mock_init.return_value = mock_scenario_generator
            mock_scenario_generator.show = mock.MagicMock()
            view._generate_scenarios_action.trigger()
            mock_init.assert_called_once_with(view, db_map, alternatives, db_editor)
            mock_scenario_generator.show.assert_called_once_with()
