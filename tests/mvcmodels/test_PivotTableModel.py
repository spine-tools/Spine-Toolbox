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
from unittest.mock import Mock, MagicMock
from PySide2.QtCore import QModelIndex
from PySide2.QtWidgets import QApplication, QAction
from spinetoolbox.mvcmodels.pivot_table_models import PivotTableModel
from spinetoolbox.widgets.data_store_widget import DataStoreForm


class TestPivotTableModel(unittest.TestCase):
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
        db_mngr.get_db_map_for_listener.side_effect = lambda *args, **kwargs: mock_db_map
        db_mngr.undo_action.__getitem__.side_effect = lambda key: QAction()
        db_mngr.redo_action.__getitem__.side_effect = lambda key: QAction()
        tabular_view = DataStoreForm(db_mngr, ("sqlite://", "codename"))
        self._model = PivotTableModel(tabular_view)
        data = {('row1', 'col1'): '1', ('row2', 'col1'): '3', ('row1', 'col2'): '5', ('row2', 'col2'): '7'}
        index_names = ['rows', 'cols']
        self._model.reset_model(data, index_names, ['rows'], ['cols'], [], ())
        self._model.fetchMore(QModelIndex())

    def test_x_flag(self):
        self.assertIsNone(self._model.plot_x_column)
        self._model.set_plot_x_column(1, True)
        self.assertEqual(self._model.plot_x_column, 1)
        self._model.set_plot_x_column(1, False)
        self.assertIsNone(self._model.plot_x_column)

    def test_header_name(self):
        self.assertEqual(self._model.header_name(self._model.index(0, 1)), 'col1')
        self.assertEqual(self._model.header_name(self._model.index(0, 2)), 'col2')

    def test_header_names(self):
        index = self._model.index(2, 2)
        self.assertEqual(self._model.header_names(index), (['row1'], 'col2'))

    def test_first_data_row(self):
        self.assertEqual(self._model.first_data_row(), 2)


if __name__ == '__main__':
    unittest.main()
