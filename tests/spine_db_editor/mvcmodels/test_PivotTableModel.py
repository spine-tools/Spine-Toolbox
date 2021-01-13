######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the plotting module.

:author: A. Soininen(VTT)
:date:   10.7.2019
"""
import os.path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    DiffDatabaseMapping,
    import_object_classes,
    import_object_parameters,
    import_objects,
    import_object_parameter_values,
    Map,
)
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor


class TestParameterValuePivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_object_classes(db_map, ("class1",))
        import_object_parameters(db_map, (("class1", "parameter1"), ("class1", "parameter2")))
        import_objects(db_map, (("class1", "object1"), ("class1", "object2")))
        import_object_parameter_values(
            db_map,
            (
                ("class1", "object1", "parameter1", 1.0),
                ("class1", "object2", "parameter1", 3.0),
                ("class1", "object1", "parameter2", 5.0),
                ("class1", "object2", "parameter2", 7.0),
            ),
        )
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._db_mngr = SpineDBManager(app_settings, None)
        with patch.object(SpineDBEditor, "restore_ui"):
            self._editor = SpineDBEditor(self._db_mngr, {url: db_map.codename})
        object_class_index = self._editor.object_tree_model.index(0, 0)
        self._editor.object_tree_model.fetchMore(object_class_index)
        index = self._editor.object_tree_model.index(0, 0, object_class_index)
        self._editor.reload_pivot_table(index)
        self._model = self._editor.pivot_table_model
        self._model.start_fetching()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._temp_dir.cleanup()

    def test_x_flag(self):
        self.assertIsNone(self._model.plot_x_column)
        self._model.set_plot_x_column(1, True)
        self.assertEqual(self._model.plot_x_column, 1)
        self._model.set_plot_x_column(1, False)
        self.assertIsNone(self._model.plot_x_column)

    def test_header_name(self):
        self.assertEqual(self._model.rowCount(), 5)
        self.assertEqual(self._model.columnCount(), 4)
        self.assertEqual(self._model.header_name(self._model.index(2, 0)), 'object1')
        self.assertEqual(self._model.header_name(self._model.index(0, 1)), 'parameter1')
        self.assertEqual(self._model.header_name(self._model.index(3, 0)), 'object2')
        self.assertEqual(self._model.header_name(self._model.index(0, 2)), 'parameter2')

    def test_data(self):
        self.assertEqual(self._model.rowCount(), 5)
        self.assertEqual(self._model.columnCount(), 4)
        self.assertEqual(self._model.index(0, 0).data(), "parameter")
        self.assertEqual(self._model.index(1, 0).data(), "class1")
        self.assertEqual(self._model.index(2, 0).data(), "object1")
        self.assertEqual(self._model.index(3, 0).data(), "object2")
        self.assertEqual(self._model.index(4, 0).data(), None)
        self.assertEqual(self._model.index(0, 1).data(), "parameter1")
        self.assertEqual(self._model.index(1, 1).data(), None)
        self.assertEqual(self._model.index(2, 1).data(), str(1.0))
        self.assertEqual(self._model.index(3, 1).data(), str(3.0))
        self.assertEqual(self._model.index(4, 1).data(), None)
        self.assertEqual(self._model.index(0, 2).data(), "parameter2")
        self.assertEqual(self._model.index(1, 2).data(), None)
        self.assertEqual(self._model.index(2, 2).data(), str(5.0))
        self.assertEqual(self._model.index(3, 2).data(), str(7.0))
        self.assertEqual(self._model.index(4, 2).data(), None)
        self.assertEqual(self._model.index(0, 3).data(), None)
        self.assertEqual(self._model.index(1, 3).data(), None)
        self.assertEqual(self._model.index(2, 3).data(), None)
        self.assertEqual(self._model.index(3, 3).data(), None)
        self.assertEqual(self._model.index(4, 3).data(), None)

    def test_header_row_count(self):
        self.assertEqual(self._model.headerRowCount(), 2)


class TestIndexExpansionPivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "db.sqlite")
        db_map = DiffDatabaseMapping(url, create=True)
        import_object_classes(db_map, ("class1",))
        import_object_parameters(db_map, (("class1", "parameter1"), ("class1", "parameter2")))
        import_objects(db_map, (("class1", "object1"), ("class1", "object2")))
        import_object_parameter_values(
            db_map,
            (
                ("class1", "object1", "parameter1", Map(["A", "B"], [1.1, 2.1])),
                ("class1", "object2", "parameter1", Map(["C", "D"], [1.2, 2.2])),
                ("class1", "object1", "parameter2", Map(["C", "D"], [-1.1, -2.1])),
                ("class1", "object2", "parameter2", Map(["A", "B"], [-1.2, -2.2])),
            ),
        )
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        self._db_mngr = SpineDBManager(app_settings, None)
        with patch.object(SpineDBEditor, "restore_ui"):
            self._editor = SpineDBEditor(self._db_mngr, {url: db_map.codename})
        object_class_index = self._editor.object_tree_model.index(0, 0)
        self._editor.object_tree_model.fetchMore(object_class_index)
        index = self._editor.object_tree_model.index(0, 0, object_class_index)
        for action in self._editor.input_type_action_group.actions():
            if action.text() == self._editor._INDEX_EXPANSION:
                action.trigger()
                break
        self._editor.reload_pivot_table(index)
        self._model = self._editor.pivot_table_model
        self._model.start_fetching()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._temp_dir.cleanup()

    def test_data(self):
        self.assertEqual(self._model.rowCount(), 11)
        self.assertEqual(self._model.columnCount(), 5)
        expected = [
            [None, "parameter", "parameter1", "parameter2", None],
            ["class1", "index", None, None, None],
            ["object1", "A", str(1.1), None, None],
            ["object1", "B", str(2.1), None, None],
            ["object1", "C", None, str(-1.1), None],
            ["object1", "D", None, str(-2.1), None],
            ["object2", "C", str(1.2), None, None],
            ["object2", "D", str(2.2), None, None],
            ["object2", "A", None, str(-1.2), None],
            ["object2", "B", None, str(-2.2), None],
            [None, None, None, None, None],
        ]
        for column in range(5):
            for row in range(11):
                self.assertEqual(
                    self._model.index(row, column).data(),
                    expected[row][column],
                    f"data mismatch on row {row} column {column}",
                )


if __name__ == '__main__':
    unittest.main()
