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

"""Unit tests for DB editor's custom ``QTableView`` classes."""
import unittest

from PySide2.QtCore import QItemSelectionModel
from PySide2.QtWidgets import QApplication

from tests.spine_db_editor.widgets.helpers import add_object, add_object_class, TestBase, EditorDelegateMocking


class TestParameterTableView(TestBase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def test_remove_last_empty_row(self):
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        index = model.index(0, 0)
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(selection_model.hasSelection())
        self.assertEqual(model.rowCount(), 1)

    def test_remove_rows_from_empty_model(self):
        tree_view = self._db_editor.ui.treeView_object
        add_object_class(tree_view, "an_object_class")
        add_object(tree_view, "an_object")
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(table_view, index, "an_object_class")
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        self.assertEqual(model.index(0, 0).data(), "an_object_class")
        self.assertEqual(model.index(0, 1).data(), None)
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), None)
        self.assertEqual(model.index(0, 4).data(), None)
        self.assertEqual(model.index(0, 5).data(), "database")
        self.assertEqual(model.index(1, 0).data(), None)
        self.assertEqual(model.index(1, 1).data(), None)
        self.assertEqual(model.index(1, 2).data(), None)
        self.assertEqual(model.index(1, 3).data(), None)
        self.assertEqual(model.index(1, 4).data(), None)
        self.assertEqual(model.index(1, 5).data(), "database")
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), None)
        self.assertEqual(model.index(0, 1).data(), None)
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), None)
        self.assertEqual(model.index(0, 4).data(), None)
        self.assertFalse(selection_model.hasSelection())


if __name__ == '__main__':
    unittest.main()
