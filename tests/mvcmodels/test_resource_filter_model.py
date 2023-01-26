######################################################################################################################
# Copyright (C) 2017-2023 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for the ``resource_filter_model`` module."""
import unittest
from unittest import mock
from contextlib import contextmanager

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QApplication

from spine_engine.project_item.project_item_resource import database_resource
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from spinetoolbox.mvcmodels.resource_filter_model import ResourceFilterModel


class TestResourceFilterModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._logger = mock.MagicMock()
        self._parent = QObject()
        self._undo_stack = QUndoStack(self._parent)

    def tearDown(self):
        self._parent.deleteLater()

    def test_setData_changes_checked_state(self):
        connection = mock.MagicMock()
        connection.database_resources = [database_resource("Data Store", "sqlite:///db.sqlite", filterable=True)]

        def online_filters(resource_label, resource_type):
            return {SCENARIO_FILTER_TYPE: {}, TOOL_FILTER_TYPE: {}}[resource_type]

        connection.online_filters.side_effect = online_filters
        connection.get_scenario_names.return_value = ["my_scenario"]
        connection.get_tool_names.return_value = ["my_tool"]
        connection.is_filter_online_by_default = True
        with resource_filter_model(connection, self._undo_stack, self._logger) as model:
            model.build_tree()
            root_index = model.index(0, 0)
            self.assertEqual(model.rowCount(root_index), 2)
            scenario_root_index = model.index(0, 0, root_index)
            self.assertEqual(model.rowCount(scenario_root_index), 2)
            my_scenario_index = model.index(1, 0, scenario_root_index)
            self.assertEqual(my_scenario_index.data(), "my_scenario")
            self.assertEqual(model.data(my_scenario_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked.value)
            self.assertTrue(
                model.setData(my_scenario_index, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole)
            )
            self.assertEqual(
                model.data(my_scenario_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Unchecked.value
            )
            self.assertTrue(
                model.setData(my_scenario_index, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)
            )
            self.assertEqual(model.data(my_scenario_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked.value)
            tool_root_index = model.index(1, 0, root_index)
            self.assertEqual(model.rowCount(tool_root_index), 2)
            my_tool_index = model.index(1, 0, tool_root_index)
            self.assertEqual(my_tool_index.data(), "my_tool")
            self.assertEqual(model.data(my_tool_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked.value)
            self.assertTrue(model.setData(my_tool_index, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole))
            self.assertEqual(model.data(my_tool_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Unchecked.value)
            self.assertTrue(model.setData(my_tool_index, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole))
            self.assertEqual(model.data(my_tool_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked.value)


@contextmanager
def resource_filter_model(connection, undo_stack, logger):
    model = ResourceFilterModel(connection, undo_stack, logger)
    try:
        yield model
    finally:
        model.deleteLater()


if __name__ == '__main__':
    unittest.main()
