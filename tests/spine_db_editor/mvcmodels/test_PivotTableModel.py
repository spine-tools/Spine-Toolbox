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

import unittest
from unittest.mock import Mock, MagicMock, patch
from PySide2.QtWidgets import QApplication, QAction
from spinetoolbox.spine_db_editor.mvcmodels.pivot_table_models import (
    ParameterValuePivotTableModel,
    IndexExpansionPivotTableModel,
)
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor


class TestParameterValuePivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        db_mngr = MagicMock()
        db_mngr.get_value.side_effect = lambda db_map, item_type, id_, field, role: id_
        db_mngr.get_item.side_effect = lambda db_map, item_type, id_: {"name": id_, "parameter_name": id_}
        mock_db_map = Mock()
        mock_db_map.codename = "codename"
        db_mngr.undo_action.__getitem__.side_effect = lambda key: QAction()
        db_mngr.redo_action.__getitem__.side_effect = lambda key: QAction()
        with patch.object(SpineDBEditor, "restore_ui"):
            tabular_view = SpineDBEditor(db_mngr, mock_db_map)
        self._model = ParameterValuePivotTableModel(tabular_view)
        data = {
            ('object1', 'parameter1', 'alternative1'): '1',
            ('object2', 'parameter1', 'alternative1'): '3',
            ('object1', 'parameter2', 'alternative1'): '5',
            ('object2', 'parameter2', 'alternative1'): '7',
        }
        tabular_view.load_parameter_value_data = lambda: data
        object_class_ids = {'object_class': 1}
        self._model.call_reset_model(object_class_ids)
        self._model.start_fetching()

    def test_x_flag(self):
        self.assertIsNone(self._model.plot_x_column)
        self._model.set_plot_x_column(1, True)
        self.assertEqual(self._model.plot_x_column, 1)
        self._model.set_plot_x_column(1, False)
        self.assertIsNone(self._model.plot_x_column)

    def test_header_name(self):
        self.assertEqual(self._model.header_name(self._model.index(0, 2)), 'alternative1')
        self.assertEqual(self._model.header_name(self._model.index(2, 0)), 'object1')
        self.assertEqual(self._model.header_name(self._model.index(2, 1)), 'parameter1')
        self.assertEqual(self._model.header_name(self._model.index(3, 0)), 'object2')
        self.assertEqual(self._model.header_name(self._model.index(3, 1)), 'parameter1')
        self.assertEqual(self._model.header_name(self._model.index(4, 0)), 'object1')
        self.assertEqual(self._model.header_name(self._model.index(4, 1)), 'parameter2')
        self.assertEqual(self._model.header_name(self._model.index(5, 0)), 'object2')
        self.assertEqual(self._model.header_name(self._model.index(5, 1)), 'parameter2')

    def test_header_row_count(self):
        self.assertEqual(self._model.headerRowCount(), 2)


class TestIndexExpansionPivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        db_mngr = MagicMock()
        # db_mngr.get_value.side_effect = lambda db_map, item_type, id_, field, role: id_
        db_mngr.get_item.side_effect = lambda db_map, item_type, id_: {"name": id_, "parameter_name": id_}
        db_mngr.get_value_index.side_effect = (
            lambda db_map, item_type, id_, index, role: {
                "value1": {"index1": 5, "index2": -3},
                "value2": {"index1": 40, "index2": -24},
            }
            .get(id_, {})
            .get(index)
        )
        mock_db_map = Mock()
        mock_db_map.codename = "codename"
        db_mngr.undo_action.__getitem__.side_effect = lambda key: QAction()
        db_mngr.redo_action.__getitem__.side_effect = lambda key: QAction()
        with patch.object(SpineDBEditor, "restore_ui"):
            tabular_view = SpineDBEditor(db_mngr, mock_db_map)
        self._model = IndexExpansionPivotTableModel(tabular_view)
        data = {
            ('node1', 'unitA', 'index1', 'parameter1', 'alternative1'): 'value1',
            ('node1', 'unitB', 'index2', 'parameter1', 'alternative1'): 'value1',
            ('node2', 'unitA', 'index1', 'parameter1', 'alternative1'): 'value2',
            ('node2', 'unitB', 'index2', 'parameter1', 'alternative1'): 'value2',
        }
        tabular_view.load_expanded_parameter_value_data = lambda: data
        object_class_ids = {'node': 1, 'unit': 2}
        self._model.call_reset_model(object_class_ids)
        self._model.start_fetching()

    def test_data(self):
        self.assertEqual(self._model.index(2, 4).data(), 5)
        self.assertEqual(self._model.index(3, 4).data(), -3)
        self.assertEqual(self._model.index(4, 4).data(), 40)
        self.assertEqual(self._model.index(5, 4).data(), -24)


if __name__ == '__main__':
    unittest.main()
