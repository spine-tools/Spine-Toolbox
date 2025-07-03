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

"""Unit tests for ``custom_delegates`` module."""
import unittest
from unittest import mock
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QStyleOptionViewItem
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.widgets.custom_delegates import BooleanValueDelegate, EntityBynameDelegate
from spinetoolbox.spine_db_editor.widgets.custom_editors import GroupEditor
from tests.mock_helpers import TestCaseWithQApplication, assert_table_model_data_pytest


class TestBooleanValueDelegate(TestCaseWithQApplication):
    def setUp(self):
        self._model = QStandardItemModel()
        row = [QStandardItem()]
        self._model.appendRow(row)
        self._delegate = BooleanValueDelegate(None, None)

    def tearDown(self):
        self._model.deleteLater()
        self._delegate.deleteLater()

    def test_set_model_data_emits_when_true_is_selected(self):
        editor = mock.MagicMock()
        index = self._model.index(0, 0)
        for value in (True, False):
            with self.subTest(value=value):
                editor.data.return_value = value
                with signal_waiter(self._delegate.data_committed, timeout=1.0) as waiter:
                    self._delegate.setModelData(editor, self._model, index)
                    waiter.wait()
                    self.assertEqual(len(waiter.args), 2)
                    self.assertEqual(waiter.args[0], index)
                    if value:
                        self.assertTrue(waiter.args[1])
                    else:
                        self.assertFalse(waiter.args[1])

    def test_set_model_data_does_not_emit_when_editor_value_is_unrecognized(self):
        editor = mock.MagicMock()
        index = self._model.index(0, 0)
        editor.data.return_value = None
        with mock.patch.object(self._delegate, "data_committed") as data_committed_signal:
            self._delegate.setModelData(editor, self._model, index)
            data_committed_signal.emit.assert_not_called()


class TestEntityBynameDelegate:
    def test_create_editor_for_undefined_entity_with_empty_model(self, db_map, db_mngr, db_editor):
        db_map.add_entity_class(name="Object")
        db_map.add_entity(entity_class_name="Object", name="cube")
        db_map.add_entity(entity_class_name="Object", name="sphere")
        table_view = db_editor.ui.empty_entity_alternative_table_view
        model = table_view.model()
        entity_class_column = model.header.index("entity_class_name")
        entity_byname_column = model.header.index("entity_byname")
        model.batch_set_data([model.index(0, entity_class_column)], ["Object"])
        delegate = EntityBynameDelegate(db_editor, db_mngr)
        editor = delegate.createEditor(db_editor, QStyleOptionViewItem(), model.index(0, entity_byname_column))
        assert isinstance(editor, GroupEditor)
        assert editor.data() is ()
        expected = [[""], ["cube"], ["sphere"]]
        assert_table_model_data_pytest(editor.proxy_model, expected)

    def test_create_editor_for_empty_byname_with_empty_model(self, db_map, db_mngr, db_editor):
        db_map.add_entity_class(name="Object")
        db_map.add_entity(entity_class_name="Object", name="cube")
        db_map.add_entity(entity_class_name="Object", name="sphere")
        table_view = db_editor.ui.empty_entity_alternative_table_view
        model = table_view.model()
        entity_class_column = model.header.index("entity_class_name")
        entity_byname_column = model.header.index("entity_byname")
        model.batch_set_data([model.index(0, entity_class_column)], ["Object"])
        model.batch_set_data([model.index(0, entity_byname_column)], [()])
        delegate = EntityBynameDelegate(db_editor, db_mngr)
        editor = delegate.createEditor(db_editor, QStyleOptionViewItem(), model.index(0, entity_byname_column))
        assert isinstance(editor, GroupEditor)
        assert editor.data() == ()
        expected = [[""], ["cube"], ["sphere"]]
        assert_table_model_data_pytest(editor.proxy_model, expected)

    def test_create_editor_for_preselected_0_dimensional_entity_with_empty_model(self, db_map, db_mngr, db_editor):
        db_map.add_entity_class(name="Object")
        db_map.add_entity(entity_class_name="Object", name="cube")
        db_map.add_entity(entity_class_name="Object", name="sphere")
        table_view = db_editor.ui.empty_entity_alternative_table_view
        model = table_view.model()
        entity_class_column = model.header.index("entity_class_name")
        entity_byname_column = model.header.index("entity_byname")
        model.batch_set_data([model.index(0, entity_class_column)], ["Object"])
        model.batch_set_data([model.index(0, entity_byname_column)], [("cube",)])
        delegate = EntityBynameDelegate(db_editor, db_mngr)
        editor = delegate.createEditor(db_editor, QStyleOptionViewItem(), model.index(0, entity_byname_column))
        assert isinstance(editor, GroupEditor)
        assert editor.data() == ("cube",)
        expected = [["cube"], ["cube"], ["sphere"]]
        assert_table_model_data_pytest(editor.proxy_model, expected)

    def test_create_editor_for_preselected_multi_dimensional_entity_with_empty_model(self, db_map, db_mngr, db_editor):
        db_map.add_entity_class(name="Source")
        db_map.add_entity(entity_class_name="Source", name="source")
        db_map.add_entity_class(name="Target")
        db_map.add_entity(entity_class_name="Target", name="target1")
        db_map.add_entity(entity_class_name="Target", name="target2")
        relationship = db_map.add_entity_class(dimension_name_list=["Source", "Target"])
        db_map.add_entity(entity_class_name="Source__Target", entity_byname=("source", "target1"))
        db_map.add_entity(entity_class_name="Source__Target", entity_byname=("source", "target2"))
        table_view = db_editor.ui.empty_entity_alternative_table_view
        model = table_view.model()
        model.set_default_row(
            entity_class_name="Source__Target", database=db_mngr.name_registry.display_name(db_map.db_url)
        )
        model.set_rows_to_default(0)
        entity_byname_column = model.header.index("entity_byname")
        model.batch_set_data([model.index(0, entity_byname_column)], [("source", "target1")])
        delegate = EntityBynameDelegate(db_editor, db_mngr)
        index = model.index(0, entity_byname_column)
        with signal_waiter(delegate.element_name_list_editor_requested) as waiter:
            editor = delegate.createEditor(db_editor, QStyleOptionViewItem(), index)
        assert editor is None
        assert waiter.args == (index, relationship["id"], db_map)
