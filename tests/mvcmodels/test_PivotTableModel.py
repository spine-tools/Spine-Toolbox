######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
from unittest.mock import MagicMock
from PySide2.QtWidgets import QApplication
from spinetoolbox.mvcmodels.pivot_table_models import PivotTableModel
from spinetoolbox.widgets.tabular_view_widget import TabularViewForm


class TestPivotTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        db_mngr = MagicMock()
        tabular_view = TabularViewForm(db_mngr, ("sqlite://", "codename"))
        self._model = PivotTableModel(tabular_view)
        data = [['row1', 'col1', '1'], ['row2', 'col1', '3'], ['row1', 'col2', '5'], ['row2', 'col2', '7']]
        index_names = ['rows', 'cols']
        index_real_names = ['real_rows', 'real_cols']
        index_types = [str, str]
        self._model.set_data(data, index_names, index_types, index_real_names=index_real_names)
        self._model.set_pivot(['rows'], ['cols'], [], ())

    def test_x_flag(self):
        self.assertIsNone(self._model.plot_x_column)
        self._model.set_plot_x_column(1, True)
        self.assertEqual(self._model.plot_x_column, 1)
        self._model.set_plot_x_column(1, False)
        self.assertIsNone(self._model.plot_x_column)

    def test_get_col_key(self):
        self.assertEqual(self._model.get_col_key(1), ('col1',))
        self.assertEqual(self._model.get_col_key(2), ('col2',))

    def test_get_key(self):
        index = self._model.index(2, 2)
        self.assertEqual(self._model.get_key(index), ('row1', 'col2'))

    def test_first_data_row(self):
        self.assertEqual(self._model.first_data_row(), 2)


if __name__ == '__main__':
    unittest.main()
