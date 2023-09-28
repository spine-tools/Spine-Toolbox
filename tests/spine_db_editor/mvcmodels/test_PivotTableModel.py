######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for :class:`ParameterValuePivotTableModel` module.
"""
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QModelIndex
from spinedb_api import Map
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestParameterValuePivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch.object(SpineDBEditor, "restore_ui"):
            self._editor = SpineDBEditor(self._db_mngr, {"sqlite://": db_map.codename})
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", 1.0),
                ("class1", "object2", "parameter1", 3.0),
                ("class1", "object1", "parameter2", 5.0),
                ("class1", "object2", "parameter2", 7.0),
            ),
        }
        self._db_mngr.import_data({db_map: data})
        object_class_index = self._editor.entity_tree_model.index(0, 0)
        fetch_model(self._editor.entity_tree_model)
        index = self._editor.entity_tree_model.index(0, 0, object_class_index)
        self._editor._update_class_attributes(index)
        with patch.object(self._editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
            mock_is_visible.return_value = True
            self._editor.do_reload_pivot_table()
        self._model = self._editor.pivot_table_model
        self._model.beginResetModel()
        self._model.endResetModel()
        qApp.processEvents()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

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
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch.object(SpineDBEditor, "restore_ui"):
            self._editor = SpineDBEditor(self._db_mngr, {"sqlite://": db_map.codename})
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", Map(["A", "B"], [1.1, 2.1])),
                ("class1", "object2", "parameter1", Map(["C", "D"], [1.2, 2.2])),
                ("class1", "object1", "parameter2", Map(["C", "D"], [-1.1, -2.1])),
                ("class1", "object2", "parameter2", Map(["A", "B"], [-1.2, -2.2])),
            ),
        }
        self._db_mngr.import_data({db_map: data})
        object_class_index = self._editor.entity_tree_model.index(0, 0)
        fetch_model(self._editor.entity_tree_model)
        index = self._editor.entity_tree_model.index(0, 0, object_class_index)
        for action in self._editor.pivot_action_group.actions():
            if action.text() == self._editor._INDEX_EXPANSION:
                action.trigger()
                break
        self._editor._update_class_attributes(index)
        with patch.object(self._editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
            mock_is_visible.return_value = True
            self._editor.do_reload_pivot_table()
        self._model = self._editor.pivot_table_model
        self._model.beginResetModel()
        self._model.endResetModel()
        qApp.processEvents()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

    def test_data(self):
        self.assertEqual(self._model.rowCount(), 11)
        self.assertEqual(self._model.columnCount(), 5)
        model_data = list()
        i = self._model.index
        for row in range(11):
            model_data.append(list(i(row, column).data() for column in range(5)))
        expected = [
            [None, "parameter", "parameter1", "parameter2", None],
            ["class1", "index", None, None, None],
            ["object1", "A", str(1.1), None, None],
            ["object1", "B", str(2.1), None, None],
            ["object1", "C", None, str(-1.1), None],
            ["object1", "D", None, str(-2.1), None],
            ["object2", "A", None, str(-1.2), None],
            ["object2", "B", None, str(-2.2), None],
            ["object2", "C", str(1.2), None, None],
            ["object2", "D", str(2.2), None, None],
            [None, None, None, None, None],
        ]
        self.assertEqual(model_data, expected)


if __name__ == '__main__':
    unittest.main()
